import uuid
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from fastapi import HTTPException

from app.models.ap_ar import (
    ARInvoice,
    ARInvoiceLine,
    Payment,
    PaymentAllocation,
    InvoiceStatus,
    PaymentType,
    PaymentStatus,
    InvoiceType
)
from app.models.accounting import Account, AccountType
from app.models.bank import BankAccount
from app.models.commercial import ClientPaymentApplication
from app.models.contracts import Contract
from app.schemas.ap_ar import (
    ARInvoiceCreate,
    PaymentCreate,
    ARSummaryResponse
)
from app.schemas.accounting import JournalCreate, JournalLineCreate
from app.services.accounting import AccountingEngine


class ARService:
    def __init__(self, db: Session, tenant_id: UUID, current_user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.current_user_id = current_user_id
        self.accounting = AccountingEngine(db, tenant_id, current_user_id)

    def _get_account_by_code_or_type(self, code: str, type_: AccountType) -> UUID:
        """Find account by code first; fallback to any account of given type."""
        account = self.db.query(Account).filter(
            Account.tenant_id == self.tenant_id,
            Account.account_code == code
        ).first()
        if account:
            return account.id
        fallback = self.db.query(Account).filter(
            Account.tenant_id == self.tenant_id,
            Account.account_type == type_
        ).first()
        if not fallback:
            raise HTTPException(status_code=400, detail=f"No account with code {code} or type {type_} found.")
        return fallback.id

    def list_invoices(
        self,
        client_id: Optional[UUID] = None,
        contract_id: Optional[UUID] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[ARInvoice]:
        query = self.db.query(ARInvoice).filter(ARInvoice.tenant_id == self.tenant_id)
        if client_id:
            query = query.filter(ARInvoice.client_id == client_id)
        if contract_id:
            query = query.filter(ARInvoice.contract_id == contract_id)
        if status and status != "ALL":
            query = query.filter(ARInvoice.status == status)
        if search:
            query = query.filter(
                or_(
                    ARInvoice.number.ilike(f"%{search}%"),
                    ARInvoice.description.ilike(f"%{search}%"),
                )
            )
        if start_date:
            query = query.filter(ARInvoice.date >= start_date)
        if end_date:
            query = query.filter(ARInvoice.date <= end_date)
        return query.order_by(ARInvoice.date.desc(), ARInvoice.created_at.desc()).all()

    def get_invoice(self, invoice_id: UUID) -> ARInvoice:
        invoice = self.db.query(ARInvoice).filter(
            ARInvoice.id == invoice_id,
            ARInvoice.tenant_id == self.tenant_id
        ).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="AR Invoice not found")
        return invoice

    def create_invoice(self, schema: ARInvoiceCreate) -> ARInvoice:
        subtotal = Decimal("0.00")
        total_tax = Decimal("0.00")

        for line_schema in schema.lines:
            lt = Decimal(str(line_schema.quantity)) * Decimal(str(line_schema.unit_price))
            subtotal += lt
            rate = Decimal(str(line_schema.tax_rate or 0))
            tax_for_line = (lt * (rate / Decimal("100.00"))).quantize(Decimal("0.01")) if rate > 0 else Decimal(str(line_schema.tax_amount or 0))
            total_tax += tax_for_line

        retention = Decimal(str(schema.retention_amount or 0))
        # Total due = subtotal + tax - retention
        calculated_total = (subtotal + total_tax - retention).quantize(Decimal("0.01"))
        total_amount = Decimal(str(schema.total_amount)) if schema.total_amount is not None and schema.total_amount > 0 else calculated_total

        invoice = ARInvoice(
            tenant_id=self.tenant_id,
            number=schema.number,
            client_id=schema.client_id,
            contract_id=schema.contract_id,
            payment_application_id=schema.payment_application_id,
            date=schema.date,
            due_date=schema.due_date,
            invoice_type=schema.invoice_type,
            subtotal=subtotal,
            tax_amount=total_tax,
            retention_amount=retention,
            total_amount=total_amount,
            currency=schema.currency,
            description=schema.description,
            status=InvoiceStatus.DRAFT,
            created_by=self.current_user_id,
            updated_by=self.current_user_id
        )
        self.db.add(invoice)
        self.db.flush()

        for line_schema in schema.lines:
            lt = (Decimal(str(line_schema.quantity)) * Decimal(str(line_schema.unit_price))).quantize(Decimal("0.01"))
            rate = Decimal(str(line_schema.tax_rate or 0))
            tax_for_line = (lt * (rate / Decimal("100.00"))).quantize(Decimal("0.01")) if rate > 0 else Decimal(str(line_schema.tax_amount or 0))

            line = ARInvoiceLine(
                tenant_id=self.tenant_id,
                invoice_id=invoice.id,
                project_id=line_schema.project_id,
                cost_code_id=line_schema.cost_code_id,
                description=line_schema.description,
                quantity=line_schema.quantity,
                unit_price=line_schema.unit_price,
                line_total=lt,
                tax_rate=rate,
                tax_amount=tax_for_line,
                created_by=self.current_user_id,
                updated_by=self.current_user_id
            )
            self.db.add(line)

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def create_invoice_from_payment_application(self, payment_app_id: UUID) -> ARInvoice:
        """Create a client invoice directly from an approved Client Payment Application (IPC)."""
        pay_app = self.db.query(ClientPaymentApplication).filter(
            ClientPaymentApplication.id == payment_app_id,
            ClientPaymentApplication.tenant_id == self.tenant_id
        ).first()
        if not pay_app:
            raise HTTPException(status_code=404, detail="Client Payment Application not found")

        contract = self.db.query(Contract).filter(
            Contract.id == pay_app.contract_id,
            Contract.tenant_id == self.tenant_id
        ).first()

        client_id = contract.client_id if contract and contract.client_id else None
        if not client_id:
            raise HTTPException(status_code=400, detail="Contract has no associated client")

        invoice_number = f"INV-AR-{pay_app.number}"
        current_work = Decimal(str(pay_app.gross_work)) - Decimal(str(pay_app.previous_certified_work))
        retention = Decimal(str(pay_app.retention_amount))
        net_due = Decimal(str(pay_app.net_amount_due))

        invoice = ARInvoice(
            tenant_id=self.tenant_id,
            number=invoice_number,
            client_id=client_id,
            contract_id=pay_app.contract_id,
            payment_application_id=pay_app.id,
            date=pay_app.date,
            due_date=pay_app.date,
            invoice_type=InvoiceType.STANDARD,
            subtotal=current_work,
            tax_amount=Decimal("0.00"),
            retention_amount=retention,
            total_amount=net_due,
            currency="USD",
            description=f"Progress Billing Invoice for IPC {pay_app.number} - {contract.contract_number if contract else ''}",
            status=InvoiceStatus.DRAFT,
            created_by=self.current_user_id,
            updated_by=self.current_user_id
        )
        self.db.add(invoice)
        self.db.flush()

        line = ARInvoiceLine(
            tenant_id=self.tenant_id,
            invoice_id=invoice.id,
            project_id=contract.project_id if contract else None,
            description=f"Work Certified Period {pay_app.period_name or ''}",
            quantity=Decimal("1.0"),
            unit_price=current_work,
            line_total=current_work,
            tax_rate=Decimal("0.0"),
            tax_amount=Decimal("0.0"),
            created_by=self.current_user_id,
            updated_by=self.current_user_id
        )
        self.db.add(line)

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def approve_invoice(self, invoice_id: UUID) -> ARInvoice:
        invoice = self.get_invoice(invoice_id)
        if invoice.status != InvoiceStatus.DRAFT:
            raise HTTPException(status_code=400, detail="Only DRAFT invoices can be approved")
        invoice.status = InvoiceStatus.APPROVED
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def post_invoice(self, invoice_id: UUID) -> ARInvoice:
        invoice = self.get_invoice(invoice_id)
        if invoice.status not in [InvoiceStatus.DRAFT, InvoiceStatus.APPROVED]:
            raise HTTPException(status_code=400, detail="Only DRAFT or APPROVED invoices can be posted")

        ar_account_id = self._get_account_by_code_or_type("1200", AccountType.ASSET)
        retention_account_id = self._get_account_by_code_or_type("1210", AccountType.ASSET)
        revenue_account_id = self._get_account_by_code_or_type("4010", AccountType.REVENUE)
        tax_account_id = self._get_account_by_code_or_type("2040", AccountType.LIABILITY)

        journal_lines: List[JournalLineCreate] = []

        # 1. Debit Accounts Receivable (Net Amount Due)
        net_due = Decimal(str(invoice.total_amount))
        journal_lines.append(JournalLineCreate(
            account_id=ar_account_id,
            debit=net_due,
            credit=Decimal("0.00"),
            description=f"AR Invoice {invoice.number} - Net Due"
        ))

        # 2. Debit Retainage Receivable (if retention > 0)
        retention = Decimal(str(invoice.retention_amount or 0))
        if retention > Decimal("0.00"):
            journal_lines.append(JournalLineCreate(
                account_id=retention_account_id,
                debit=retention,
                credit=Decimal("0.00"),
                description=f"AR Invoice {invoice.number} - Retainage Withheld"
            ))

        # 3. Credit Revenue for invoice lines
        subtotal = Decimal(str(invoice.subtotal or 0))
        if invoice.lines:
            for line in invoice.lines:
                journal_lines.append(JournalLineCreate(
                    account_id=revenue_account_id,
                    debit=Decimal("0.00"),
                    credit=Decimal(str(line.line_total)),
                    project_id=line.project_id,
                    cost_code_id=line.cost_code_id,
                    description=line.description
                ))
        else:
            journal_lines.append(JournalLineCreate(
                account_id=revenue_account_id,
                debit=Decimal("0.00"),
                credit=subtotal,
                description=f"AR Invoice {invoice.number} - Contract Revenue"
            ))

        # 4. Credit Tax Payable (if tax > 0)
        tax_amount = Decimal(str(invoice.tax_amount or 0))
        if tax_amount > Decimal("0.00"):
            journal_lines.append(JournalLineCreate(
                account_id=tax_account_id,
                debit=Decimal("0.00"),
                credit=tax_amount,
                description=f"AR Invoice {invoice.number} - VAT/Tax Payable"
            ))

        # Verify balancing
        total_debits = sum(line.debit for line in journal_lines)
        total_credits = sum(line.credit for line in journal_lines)

        # Micro-adjustment if there's rounding difference between lines and total
        diff = total_debits - total_credits
        if diff != Decimal("0.00") and abs(diff) <= Decimal("0.05"):
            # Adjust the first revenue line
            for jl in journal_lines:
                if jl.account_id == revenue_account_id:
                    jl.credit = jl.credit + diff
                    break

        journal_schema = JournalCreate(
            date=invoice.date,
            reference=invoice.number,
            description=invoice.description or f"Client Progress Billing {invoice.number}",
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
        invoice = self.get_invoice(invoice_id)
        if invoice.status not in [InvoiceStatus.POSTED, InvoiceStatus.PARTIAL]:
            return Decimal("0.00")

        allocated = self.db.query(func.sum(PaymentAllocation.amount)).filter(
            PaymentAllocation.ar_invoice_id == invoice_id,
            PaymentAllocation.tenant_id == self.tenant_id
        ).scalar() or Decimal("0.00")
        return max(Decimal("0.00"), Decimal(str(invoice.total_amount)) - Decimal(str(allocated)))

    def list_receipts(
        self,
        client_id: Optional[UUID] = None,
        search: Optional[str] = None
    ) -> List[Payment]:
        query = self.db.query(Payment).filter(
            Payment.tenant_id == self.tenant_id,
            Payment.payment_type == PaymentType.AR_RECEIPT
        )
        if client_id:
            query = query.filter(Payment.client_id == client_id)
        if search:
            query = query.filter(Payment.reference.ilike(f"%{search}%"))
        return query.order_by(Payment.date.desc(), Payment.created_at.desc()).all()

    def get_receipt(self, receipt_id: UUID) -> Payment:
        receipt = self.db.query(Payment).filter(
            Payment.id == receipt_id,
            Payment.payment_type == PaymentType.AR_RECEIPT,
            Payment.tenant_id == self.tenant_id
        ).first()
        if not receipt:
            raise HTTPException(status_code=404, detail="Customer Receipt not found")
        return receipt

    def create_receipt(self, schema: PaymentCreate) -> Payment:
        bank_account = None
        if schema.bank_account_id:
            bank_account = self.db.query(BankAccount).filter(
                BankAccount.id == schema.bank_account_id,
                BankAccount.tenant_id == self.tenant_id
            ).first()

        cash_account_id = None
        if bank_account and bank_account.gl_account_id:
            cash_account_id = bank_account.gl_account_id
        else:
            cash_account_id = self._get_account_by_code_or_type("1010", AccountType.ASSET)

        ar_account_id = self._get_account_by_code_or_type("1200", AccountType.ASSET)

        receipt = Payment(
            tenant_id=self.tenant_id,
            reference=schema.reference,
            payment_type=PaymentType.AR_RECEIPT,
            date=schema.date,
            amount=schema.amount,
            currency=schema.currency,
            client_id=schema.client_id,
            bank_account_id=schema.bank_account_id,
            status=PaymentStatus.POSTED,
            created_by=self.current_user_id,
            updated_by=self.current_user_id
        )
        self.db.add(receipt)
        self.db.flush()

        # Create balanced double-entry GL journal: Debit Cash, Credit Accounts Receivable
        journal_lines = [
            JournalLineCreate(
                account_id=cash_account_id,
                debit=schema.amount,
                credit=Decimal("0.00"),
                description=f"Customer Collection {schema.reference}"
            ),
            JournalLineCreate(
                account_id=ar_account_id,
                debit=Decimal("0.00"),
                credit=schema.amount,
                description=f"Customer Collection {schema.reference} - AR Settlement"
            )
        ]

        journal_schema = JournalCreate(
            date=schema.date,
            reference=schema.reference,
            description=f"Customer Collection Receipt {schema.reference}",
            lines=journal_lines
        )
        journal = self.accounting.create_journal(journal_schema)
        journal = self.accounting.post_journal(journal.id)
        receipt.journal_id = journal.id

        # Allocate receipt to invoices
        unapplied = Decimal(str(schema.amount))
        for alloc_schema in schema.allocations:
            alloc_amt = Decimal(str(alloc_schema.amount))
            if unapplied < alloc_amt:
                raise HTTPException(status_code=400, detail="Allocation exceeds receipt amount")

            allocation = PaymentAllocation(
                tenant_id=self.tenant_id,
                payment_id=receipt.id,
                ar_invoice_id=alloc_schema.ar_invoice_id,
                amount=alloc_amt,
                created_by=self.current_user_id,
                updated_by=self.current_user_id
            )
            self.db.add(allocation)
            unapplied -= alloc_amt

            if alloc_schema.ar_invoice_id:
                self.db.flush()
                bal = self.get_outstanding_balance(alloc_schema.ar_invoice_id)
                inv = self.db.query(ARInvoice).filter(
                    ARInvoice.id == alloc_schema.ar_invoice_id,
                    ARInvoice.tenant_id == self.tenant_id
                ).first()
                if inv:
                    if bal <= Decimal("0.00"):
                        inv.status = InvoiceStatus.PAID
                    else:
                        inv.status = InvoiceStatus.PARTIAL

        self.db.commit()
        self.db.refresh(receipt)
        return receipt

    def get_ar_summary(self) -> ARSummaryResponse:
        invoices = self.db.query(ARInvoice).filter(ARInvoice.tenant_id == self.tenant_id).all()
        receipts = self.db.query(Payment).filter(
            Payment.tenant_id == self.tenant_id,
            Payment.payment_type == PaymentType.AR_RECEIPT,
            Payment.status == PaymentStatus.POSTED
        ).all()

        total_invoiced = sum(Decimal(str(inv.total_amount or 0)) for inv in invoices)
        total_retention = sum(Decimal(str(inv.retention_amount or 0)) for inv in invoices)
        total_received = sum(Decimal(str(rec.amount or 0)) for rec in receipts)

        total_receivables = Decimal("0.00")
        draft_count = 0
        approved_count = 0
        posted_count = 0
        paid_count = 0

        current_receivables = Decimal("0.00")
        overdue_30 = Decimal("0.00")
        overdue_60 = Decimal("0.00")
        overdue_90_plus = Decimal("0.00")
        today = date.today()

        for inv in invoices:
            if inv.status == InvoiceStatus.DRAFT:
                draft_count += 1
            elif inv.status == InvoiceStatus.APPROVED:
                approved_count += 1
            elif inv.status in [InvoiceStatus.POSTED, InvoiceStatus.PARTIAL]:
                posted_count += 1
                out = inv.outstanding_amount
                total_receivables += out
                # Aging
                days = (today - inv.due_date).days if inv.due_date else 0
                if days <= 0:
                    current_receivables += out
                elif days <= 30:
                    overdue_30 += out
                elif days <= 60:
                    overdue_60 += out
                else:
                    overdue_90_plus += out
            elif inv.status == InvoiceStatus.PAID:
                paid_count += 1

        recent_invoices = [
            {
                "id": str(inv.id),
                "number": inv.number,
                "client_name": inv.client_name or "Client",
                "contract_number": inv.contract_number,
                "date": str(inv.date),
                "total_amount": float(inv.total_amount),
                "outstanding_amount": float(inv.outstanding_amount),
                "status": inv.status.value if hasattr(inv.status, "value") else str(inv.status),
            }
            for inv in sorted(invoices, key=lambda x: x.date, reverse=True)[:5]
        ]

        recent_receipts = [
            {
                "id": str(rec.id),
                "reference": rec.reference,
                "client_name": rec.client_name or "Client",
                "date": str(rec.date),
                "amount": float(rec.amount),
                "status": rec.status.value if hasattr(rec.status, "value") else str(rec.status),
            }
            for rec in sorted(receipts, key=lambda x: x.date, reverse=True)[:5]
        ]

        return ARSummaryResponse(
            total_invoiced=total_invoiced,
            total_receivables=total_receivables,
            total_received=total_received,
            total_retention_held=total_retention,
            invoices_count=len(invoices),
            draft_count=draft_count,
            approved_count=approved_count,
            posted_count=posted_count,
            paid_count=paid_count,
            collections_count=len(receipts),
            current_receivables=current_receivables,
            overdue_30=overdue_30,
            overdue_60=overdue_60,
            overdue_90_plus=overdue_90_plus,
            recent_invoices=recent_invoices,
            recent_receipts=recent_receipts,
        )
