import uuid
from datetime import date
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from app.models.ap_ar import ARInvoice, ARInvoiceLine, Payment, PaymentAllocation, InvoiceStatus, PaymentType, PaymentStatus
from app.models.accounting import Account, AccountType
from app.schemas.ap_ar import ARInvoiceCreate, PaymentCreate
from app.schemas.accounting import JournalCreate, JournalLineCreate
from app.services.accounting import AccountingEngine

class ARService:
    def __init__(self, db: Session, tenant_id: UUID, current_user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.current_user_id = current_user_id
        self.accounting = AccountingEngine(db, tenant_id, current_user_id)

    def _get_account(self, type_: AccountType) -> UUID:
        account = self.db.query(Account).filter(
            Account.tenant_id == self.tenant_id,
            Account.account_type == type_
        ).first()
        if not account:
            raise HTTPException(status_code=400, detail=f"No account of type {type_} found.")
        return account.id

    def create_invoice(self, schema: ARInvoiceCreate) -> ARInvoice:
        total = sum((line.quantity * line.unit_price) for line in schema.lines)
        
        invoice = ARInvoice(
            tenant_id=self.tenant_id,
            number=schema.number,
            client_id=schema.client_id,
            date=schema.date,
            due_date=schema.due_date,
            invoice_type=schema.invoice_type,
            total_amount=total,
            currency=schema.currency,
            description=schema.description,
            status=InvoiceStatus.DRAFT,
            created_by=self.current_user_id,
            updated_by=self.current_user_id
        )
        self.db.add(invoice)
        self.db.flush()

        for line_schema in schema.lines:
            line_total = line_schema.quantity * line_schema.unit_price
            line = ARInvoiceLine(
                tenant_id=self.tenant_id,
                invoice_id=invoice.id,
                project_id=line_schema.project_id,
                description=line_schema.description,
                quantity=line_schema.quantity,
                unit_price=line_schema.unit_price,
                line_total=line_total,
                created_by=self.current_user_id,
                updated_by=self.current_user_id
            )
            self.db.add(line)
        
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def post_invoice(self, invoice_id: UUID) -> ARInvoice:
        invoice = self.db.query(ARInvoice).filter(ARInvoice.id == invoice_id, ARInvoice.tenant_id == self.tenant_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        if invoice.status != InvoiceStatus.DRAFT:
            raise HTTPException(status_code=400, detail="Only DRAFT invoices can be posted")

        ar_account_id = self._get_account(AccountType.ASSET) # AR is an asset
        revenue_account_id = self._get_account(AccountType.REVENUE)

        journal_lines = []
        # Debit AR Asset
        journal_lines.append(JournalLineCreate(
            account_id=ar_account_id,
            debit=invoice.total_amount,
            description=f"AR Invoice {invoice.number}"
        ))

        # Credit Revenue for each line
        for line in invoice.lines:
            journal_lines.append(JournalLineCreate(
                account_id=revenue_account_id,
                credit=line.line_total,
                project_id=line.project_id,
                description=line.description
            ))

        journal_schema = JournalCreate(
            date=invoice.date,
            reference=invoice.number,
            description=invoice.description or f"AR Invoice {invoice.number}",
            lines=journal_lines
        )
        
        journal = self.accounting.create_journal(journal_schema)
        journal = self.accounting.post_journal(journal.id)

        invoice.status = InvoiceStatus.POSTED
        invoice.journal_id = journal.id
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def get_outstanding_balance(self, invoice_id: UUID) -> Decimal:
        invoice = self.db.query(ARInvoice).filter(ARInvoice.id == invoice_id).first()
        if not invoice or invoice.status not in [InvoiceStatus.POSTED, InvoiceStatus.PARTIAL]:
            return Decimal('0.00')

        allocated = self.db.query(func.sum(PaymentAllocation.amount)).filter(
            PaymentAllocation.ar_invoice_id == invoice_id
        ).scalar() or Decimal('0.00')
        return invoice.total_amount - allocated

    def create_receipt(self, schema: PaymentCreate) -> Payment:
        payment = Payment(
            tenant_id=self.tenant_id,
            reference=schema.reference,
            payment_type=schema.payment_type,
            date=schema.date,
            amount=schema.amount,
            currency=schema.currency,
            client_id=schema.client_id,
            bank_account_id=schema.bank_account_id,
            status=PaymentStatus.POSTED,
            created_by=self.current_user_id,
            updated_by=self.current_user_id
        )
        self.db.add(payment)
        self.db.flush()

        ar_account_id = self._get_account(AccountType.ASSET)
        cash_account_id = self._get_account(AccountType.ASSET)

        # Create GL Entry for receipt
        # Debit Cash, Credit AR Asset
        journal_lines = [
            JournalLineCreate(account_id=cash_account_id, debit=schema.amount, description=f"Receipt {schema.reference}"),
            JournalLineCreate(account_id=ar_account_id, credit=schema.amount, description=f"Receipt {schema.reference}")
        ]
        
        journal_schema = JournalCreate(
            date=schema.date,
            reference=schema.reference,
            description=f"Receipt {schema.reference}",
            lines=journal_lines
        )
        journal = self.accounting.create_journal(journal_schema)
        journal = self.accounting.post_journal(journal.id)
        payment.journal_id = journal.id

        # Allocate receipt to invoices
        unapplied = schema.amount
        for alloc_schema in schema.allocations:
            if unapplied < alloc_schema.amount:
                raise HTTPException(status_code=400, detail="Allocation exceeds receipt amount")
            
            allocation = PaymentAllocation(
                tenant_id=self.tenant_id,
                payment_id=payment.id,
                ar_invoice_id=alloc_schema.ar_invoice_id,
                amount=alloc_schema.amount,
                created_by=self.current_user_id,
                updated_by=self.current_user_id
            )
            self.db.add(allocation)
            unapplied -= alloc_schema.amount
            
            # Update invoice status based on outstanding balance
            if alloc_schema.ar_invoice_id:
                self.db.flush()
                bal = self.get_outstanding_balance(alloc_schema.ar_invoice_id)
                inv = self.db.query(ARInvoice).get(alloc_schema.ar_invoice_id)
                if bal <= 0:
                    inv.status = InvoiceStatus.PAID
                else:
                    inv.status = InvoiceStatus.PARTIAL
        
        self.db.commit()
        self.db.refresh(payment)
        return payment
