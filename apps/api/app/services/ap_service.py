import uuid
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from fastapi import HTTPException

from app.models.ap_ar import (
    APInvoice, APInvoiceLine, Payment, PaymentAllocation,
    InvoiceStatus, PaymentType, PaymentStatus, MatchingStatus
)
from app.models.accounting import Account, AccountType
from app.models.purchase_orders import PurchaseOrder, PurchaseOrderLine
from app.models.goods_receipts import GoodsReceipt, GoodsReceiptLine
from app.models.suppliers import Supplier
from app.models.bank import BankAccount
from app.schemas.ap_ar import (
    APInvoiceCreate, PaymentCreate,
    ThreeWayMatchResponse, ThreeWayMatchLineReport,
    APSummaryResponse
)
from app.schemas.accounting import JournalCreate, JournalLineCreate
from app.services.accounting import AccountingEngine

class APService:
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
            # Fallback to any account if specific not found
            account = self.db.query(Account).filter(Account.tenant_id == self.tenant_id).first()
            if not account:
                raise HTTPException(status_code=400, detail=f"No account of type {type_} found.")
        return account.id

    def create_invoice(self, schema: APInvoiceCreate) -> APInvoice:
        subtotal = sum((line.quantity * line.unit_price) for line in schema.lines)
        tax_total = Decimal("0.0000")
        for line in schema.lines:
            if line.tax_amount and line.tax_amount > 0:
                tax_total += Decimal(str(line.tax_amount))
            elif line.tax_rate and line.tax_rate > 0:
                tax_total += (line.quantity * line.unit_price * (line.tax_rate / Decimal("100.0")))
        
        if schema.tax_amount and schema.tax_amount > 0:
            tax_total = Decimal(str(schema.tax_amount))
            
        total = subtotal + tax_total

        invoice = APInvoice(
            tenant_id=self.tenant_id,
            number=schema.number,
            supplier_id=schema.supplier_id,
            purchase_order_id=schema.purchase_order_id,
            goods_receipt_id=schema.goods_receipt_id,
            date=schema.date,
            due_date=schema.due_date,
            invoice_type=schema.invoice_type,
            matching_status="UNMATCHED",
            subtotal=subtotal,
            tax_amount=tax_total,
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
            line_subtotal = line_schema.quantity * line_schema.unit_price
            line_tax = Decimal("0.0000")
            if line_schema.tax_amount and line_schema.tax_amount > 0:
                line_tax = Decimal(str(line_schema.tax_amount))
            elif line_schema.tax_rate and line_schema.tax_rate > 0:
                line_tax = line_subtotal * (line_schema.tax_rate / Decimal("100.0"))
            
            line_total = line_subtotal + line_tax
            
            line = APInvoiceLine(
                tenant_id=self.tenant_id,
                invoice_id=invoice.id,
                project_id=line_schema.project_id,
                cost_code_id=line_schema.cost_code_id,
                purchase_order_line_id=line_schema.purchase_order_line_id,
                goods_receipt_line_id=line_schema.goods_receipt_line_id,
                material_id=line_schema.material_id,
                description=line_schema.description,
                quantity=line_schema.quantity,
                unit_price=line_schema.unit_price,
                tax_rate=line_schema.tax_rate,
                tax_amount=line_tax,
                line_total=line_total,
                created_by=self.current_user_id,
                updated_by=self.current_user_id
            )
            self.db.add(line)
        
        self.db.flush()
        
        # If PO or GRN is linked, automatically perform initial 3-way match check
        if invoice.purchase_order_id or invoice.goods_receipt_id:
            try:
                self._compute_and_update_match(invoice)
            except Exception:
                pass

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def _compute_and_update_match(self, invoice: APInvoice) -> Tuple[str, Decimal, List[ThreeWayMatchLineReport]]:
        po = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.id == invoice.purchase_order_id,
            PurchaseOrder.tenant_id == self.tenant_id
        ).first() if invoice.purchase_order_id else None

        grn = self.db.query(GoodsReceipt).filter(
            GoodsReceipt.id == invoice.goods_receipt_id,
            GoodsReceipt.tenant_id == self.tenant_id
        ).first() if invoice.goods_receipt_id else None

        # If invoice has PO but no GRN, look up the latest posted GRN for this PO
        if po and not grn:
            grn = self.db.query(GoodsReceipt).filter(
                GoodsReceipt.purchase_order_id == po.id,
                GoodsReceipt.tenant_id == self.tenant_id
            ).first()
            if grn:
                invoice.goods_receipt_id = grn.id

        # If invoice has GRN but no PO, resolve PO from GRN
        if grn and not po:
            po = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.id == grn.purchase_order_id,
                PurchaseOrder.tenant_id == self.tenant_id
            ).first()
            if po:
                invoice.purchase_order_id = po.id

        po_lines = self.db.query(PurchaseOrderLine).filter(
            PurchaseOrderLine.purchase_order_id == po.id
        ).all() if po else []

        grn_lines = self.db.query(GoodsReceiptLine).filter(
            GoodsReceiptLine.goods_receipt_id == grn.id
        ).all() if grn else []

        line_reports: List[ThreeWayMatchLineReport] = []
        all_matched = True
        total_variance = Decimal("0.0000")

        for inv_line in invoice.lines:
            matched_po_line: Optional[PurchaseOrderLine] = None
            matched_grn_line: Optional[GoodsReceiptLine] = None

            # Try matching PO line by explicit ID or description
            if inv_line.purchase_order_line_id:
                matched_po_line = next((p for p in po_lines if p.id == inv_line.purchase_order_line_id), None)
            if not matched_po_line and po_lines:
                matched_po_line = next(
                    (p for p in po_lines if p.item_description.lower() in inv_line.description.lower() or inv_line.description.lower() in p.item_description.lower()),
                    po_lines[0] if len(po_lines) == 1 else None
                )

            # Try matching GRN line by explicit ID or material
            if inv_line.goods_receipt_line_id:
                matched_grn_line = next((g for g in grn_lines if g.id == inv_line.goods_receipt_line_id), None)
            if not matched_grn_line and matched_po_line:
                matched_grn_line = next((g for g in grn_lines if g.purchase_order_line_id == matched_po_line.id), None)
            if not matched_grn_line and grn_lines:
                matched_grn_line = grn_lines[0] if len(grn_lines) == 1 else None

            po_qty = Decimal(str(matched_po_line.quantity)) if matched_po_line else None
            po_price = Decimal(str(matched_po_line.unit_price)) if matched_po_line else None
            grn_qty = Decimal(str(matched_grn_line.accepted_quantity)) if matched_grn_line else None

            inv_qty = Decimal(str(inv_line.quantity))
            inv_price = Decimal(str(inv_line.unit_price))
            inv_total = Decimal(str(inv_line.line_total))

            qty_var = Decimal("0.0000")
            price_var = Decimal("0.0000")
            line_status = "MATCHED"
            notes = "Quantities and unit pricing fully verified across PO and GRN."

            if grn_qty is not None:
                qty_var = inv_qty - grn_qty
            elif po_qty is not None:
                qty_var = inv_qty - po_qty

            if po_price is not None:
                price_var = inv_price - po_price

            line_var_total = (qty_var * inv_price) + (inv_qty * price_var) if (qty_var or price_var) else Decimal("0.0000")
            total_variance += abs(line_var_total)

            if not matched_po_line and not matched_grn_line:
                line_status = "UNMATCHED"
                all_matched = False
                notes = "No matching PO line or GRN line linked."
            elif abs(qty_var) > Decimal("0.001") and abs(price_var) > Decimal("0.001"):
                line_status = "QTY_AND_PRICE_VARIANCE"
                all_matched = False
                notes = f"Quantity variance of {qty_var:+.2f} and price variance of {price_var:+.2f} USD."
            elif abs(qty_var) > Decimal("0.001"):
                line_status = "QTY_VARIANCE"
                all_matched = False
                notes = f"Quantity variance of {qty_var:+.2f} against accepted GRN quantity."
            elif abs(price_var) > Decimal("0.001"):
                line_status = "PRICE_VARIANCE"
                all_matched = False
                notes = f"Price variance of {price_var:+.2f} USD against approved PO unit price."

            line_reports.append(ThreeWayMatchLineReport(
                invoice_line_id=inv_line.id,
                description=inv_line.description,
                invoice_qty=inv_qty,
                invoice_unit_price=inv_price,
                invoice_line_total=inv_total,
                po_qty=po_qty,
                po_unit_price=po_price,
                grn_accepted_qty=grn_qty,
                qty_variance=qty_var,
                price_variance=price_var,
                total_variance=line_var_total,
                line_status=line_status,
                notes=notes
            ))

        if not po and not grn:
            final_status = "UNMATCHED"
        elif all_matched and total_variance == Decimal("0.0000"):
            final_status = "MATCHED"
        else:
            final_status = "VARIANCE"

        invoice.matching_status = final_status
        return final_status, total_variance, line_reports

    def perform_three_way_match(self, invoice_id: UUID) -> ThreeWayMatchResponse:
        invoice = self.db.query(APInvoice).filter(
            APInvoice.id == invoice_id,
            APInvoice.tenant_id == self.tenant_id
        ).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        matching_status, variance_amount, lines = self._compute_and_update_match(invoice)
        self.db.commit()
        self.db.refresh(invoice)

        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == invoice.purchase_order_id).first() if invoice.purchase_order_id else None
        grn = self.db.query(GoodsReceipt).filter(GoodsReceipt.id == invoice.goods_receipt_id).first() if invoice.goods_receipt_id else None
        supplier = self.db.query(Supplier).filter(Supplier.id == invoice.supplier_id).first() if invoice.supplier_id else None

        total_po = Decimal(str(po.total_amount)) if po else None
        total_grn = Decimal(str(grn.total_received_amount)) if (grn and hasattr(grn, 'total_received_amount')) else (total_po if grn else None)

        is_matched = (matching_status == "MATCHED")
        can_approve = is_matched or (matching_status == "VARIANCE") # Authorized approvers can approve with variance

        return ThreeWayMatchResponse(
            invoice_id=invoice.id,
            invoice_number=invoice.number,
            supplier_name=supplier.name if supplier else None,
            purchase_order_id=invoice.purchase_order_id,
            po_number=po.po_number if po else None,
            goods_receipt_id=invoice.goods_receipt_id,
            grn_number=grn.receipt_number if grn else None,
            matching_status=matching_status,
            total_invoice_amount=Decimal(str(invoice.total_amount)),
            total_po_amount=total_po,
            total_grn_accepted_amount=total_grn,
            variance_amount=variance_amount,
            is_matched=is_matched,
            can_approve=can_approve,
            lines=lines
        )

    def approve_invoice(self, invoice_id: UUID, notes: Optional[str] = None) -> APInvoice:
        invoice = self.db.query(APInvoice).filter(
            APInvoice.id == invoice_id,
            APInvoice.tenant_id == self.tenant_id
        ).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        if invoice.status in [InvoiceStatus.POSTED, InvoiceStatus.PAID, InvoiceStatus.VOID]:
            raise HTTPException(status_code=400, detail=f"Invoice in {invoice.status} status cannot be approved")

        invoice.status = InvoiceStatus.APPROVED
        invoice.updated_by = self.current_user_id
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def post_invoice(self, invoice_id: UUID) -> APInvoice:
        invoice = self.db.query(APInvoice).filter(
            APInvoice.id == invoice_id,
            APInvoice.tenant_id == self.tenant_id
        ).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        if invoice.status not in [InvoiceStatus.DRAFT, InvoiceStatus.APPROVED]:
            raise HTTPException(status_code=400, detail="Only DRAFT or APPROVED invoices can be posted")

        ap_account_id = self._get_account(AccountType.LIABILITY)
        expense_account_id = self._get_account(AccountType.EXPENSE)
        inventory_account_id = self._get_account(AccountType.ASSET)

        journal_lines = []
        # Credit AP Liability (Total Invoice Amount)
        journal_lines.append(JournalLineCreate(
            account_id=ap_account_id,
            credit=invoice.total_amount,
            description=f"AP Invoice {invoice.number}"
        ))

        # Debit Expense or Inventory for each line
        lines_sum = Decimal("0.0000")
        for line in invoice.lines:
            lines_sum += Decimal(str(line.line_total))
            
            # If the AP invoice line is for a stocked material or matched to a GRN, it hits Inventory Asset, not Project Expense
            is_inventory = bool(line.material_id or line.goods_receipt_line_id)
            target_account_id = inventory_account_id if is_inventory else expense_account_id
            
            journal_lines.append(JournalLineCreate(
                account_id=target_account_id,
                debit=line.line_total,
                project_id=line.project_id if not is_inventory else None,
                cost_code_id=line.cost_code_id if not is_inventory else None,
                description=line.description
            ))

        # Reconcile any rounding or tax discrepancy so Debits strictly equal Credits
        total_debit = sum((line.debit for line in journal_lines if line.debit), Decimal("0.0000"))
        diff = Decimal(str(invoice.total_amount)) - total_debit
        if abs(diff) > Decimal("0.0000"):
            journal_lines.append(JournalLineCreate(
                account_id=expense_account_id,
                debit=diff,
                description=f"Tax & freight adjustments for AP Invoice {invoice.number}"
            ))

        journal_schema = JournalCreate(
            date=invoice.date,
            reference=invoice.number,
            description=invoice.description or f"AP Invoice {invoice.number}",
            lines=journal_lines
        )
        
        journal = self.accounting.create_journal(journal_schema)
        # Immediately post the journal since the invoice is being posted
        journal = self.accounting.post_journal(journal.id)

        invoice.status = InvoiceStatus.POSTED
        invoice.journal_id = journal.id
        invoice.updated_by = self.current_user_id
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def get_outstanding_balance(self, invoice_id: UUID) -> Decimal:
        invoice = self.db.query(APInvoice).filter(APInvoice.id == invoice_id).first()
        if not invoice or invoice.status not in [InvoiceStatus.POSTED, InvoiceStatus.PARTIAL]:
            return Decimal("0.0000")

        allocated = self.db.query(func.sum(PaymentAllocation.amount)).filter(
            PaymentAllocation.ap_invoice_id == invoice_id
        ).scalar() or Decimal("0.0000")
        return max(Decimal("0.0000"), Decimal(str(invoice.total_amount)) - Decimal(str(allocated)))

    def create_payment(self, schema: PaymentCreate) -> Payment:
        bank = self.db.query(BankAccount).filter(
            BankAccount.id == schema.bank_account_id,
            BankAccount.tenant_id == self.tenant_id
        ).first()
        if not bank:
            raise HTTPException(status_code=400, detail="Valid bank account required for payment disbursement")

        payment = Payment(
            tenant_id=self.tenant_id,
            reference=schema.reference,
            payment_type=schema.payment_type,
            date=schema.date,
            amount=schema.amount,
            currency=schema.currency,
            supplier_id=schema.supplier_id,
            client_id=schema.client_id,
            bank_account_id=schema.bank_account_id,
            status=PaymentStatus.POSTED,
            created_by=self.current_user_id,
            updated_by=self.current_user_id
        )
        self.db.add(payment)
        self.db.flush()

        ap_account_id = self._get_account(AccountType.LIABILITY)
        cash_account_id = bank.gl_account_id or self._get_account(AccountType.ASSET)

        # Create GL Entry for payment: Debit AP Liability, Credit Cash
        journal_lines = [
            JournalLineCreate(account_id=ap_account_id, debit=schema.amount, description=f"Vendor Payment {schema.reference}"),
            JournalLineCreate(account_id=cash_account_id, credit=schema.amount, description=f"Disbursement {schema.reference}")
        ]
        
        journal_schema = JournalCreate(
            date=schema.date,
            reference=schema.reference,
            description=f"Payment {schema.reference}",
            lines=journal_lines
        )
        journal = self.accounting.create_journal(journal_schema)
        journal = self.accounting.post_journal(journal.id)
        payment.journal_id = journal.id

        # Allocate payment to invoices
        unapplied = Decimal(str(schema.amount))
        for alloc_schema in schema.allocations:
            alloc_amt = Decimal(str(alloc_schema.amount))
            if unapplied < alloc_amt:
                raise HTTPException(status_code=400, detail="Allocation exceeds payment amount")
            
            allocation = PaymentAllocation(
                tenant_id=self.tenant_id,
                payment_id=payment.id,
                ap_invoice_id=alloc_schema.ap_invoice_id,
                amount=alloc_amt,
                created_by=self.current_user_id,
                updated_by=self.current_user_id
            )
            self.db.add(allocation)
            unapplied -= alloc_amt
            
            # Update invoice status based on outstanding balance
            if alloc_schema.ap_invoice_id:
                self.db.flush()
                bal = self.get_outstanding_balance(alloc_schema.ap_invoice_id)
                inv = self.db.query(APInvoice).filter(APInvoice.id == alloc_schema.ap_invoice_id).first()
                if inv:
                    if bal <= Decimal("0.0001"):
                        inv.status = InvoiceStatus.PAID
                    else:
                        inv.status = InvoiceStatus.PARTIAL
        
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def get_ap_summary(self) -> APSummaryResponse:
        invoices = self.db.query(APInvoice).filter(APInvoice.tenant_id == self.tenant_id).all()
        payments = self.db.query(Payment).filter(
            Payment.tenant_id == self.tenant_id,
            Payment.payment_type == PaymentType.AP_PAYMENT
        ).all()

        total_invoiced = sum((Decimal(str(inv.total_amount)) for inv in invoices), Decimal("0.0000"))
        total_paid = sum((Decimal(str(p.amount)) for p in payments), Decimal("0.0000"))
        total_payables = sum((inv.outstanding_amount for inv in invoices if inv.status in [InvoiceStatus.POSTED, InvoiceStatus.PARTIAL]), Decimal("0.0000"))

        draft_count = sum(1 for inv in invoices if inv.status == InvoiceStatus.DRAFT)
        approved_count = sum(1 for inv in invoices if inv.status == InvoiceStatus.APPROVED)
        posted_count = sum(1 for inv in invoices if inv.status in [InvoiceStatus.POSTED, InvoiceStatus.PARTIAL])
        paid_count = sum(1 for inv in invoices if inv.status == InvoiceStatus.PAID)
        matched_count = sum(1 for inv in invoices if inv.matching_status == "MATCHED")
        variance_count = sum(1 for inv in invoices if inv.matching_status == "VARIANCE")

        today = date.today()
        aging_current = Decimal("0.0000")
        aging_31_60 = Decimal("0.0000")
        aging_61_90 = Decimal("0.0000")
        aging_over_90 = Decimal("0.0000")

        for inv in invoices:
            if inv.status in [InvoiceStatus.POSTED, InvoiceStatus.PARTIAL]:
                bal = inv.outstanding_amount
                days_overdue = (today - inv.due_date).days if inv.due_date else 0
                if days_overdue <= 30:
                    aging_current += bal
                elif days_overdue <= 60:
                    aging_31_60 += bal
                elif days_overdue <= 90:
                    aging_61_90 += bal
                else:
                    aging_over_90 += bal

        recent_inv_data = [
            {
                "id": str(inv.id),
                "number": inv.number,
                "supplier_name": inv.supplier_name or "Unknown Supplier",
                "date": str(inv.date),
                "due_date": str(inv.due_date),
                "total_amount": float(inv.total_amount),
                "outstanding_amount": float(inv.outstanding_amount),
                "status": inv.status.value,
                "matching_status": inv.matching_status,
                "po_number": inv.po_number,
                "grn_number": inv.grn_number
            }
            for inv in sorted(invoices, key=lambda x: x.created_at or datetime.min, reverse=True)[:5]
        ]

        recent_pay_data = [
            {
                "id": str(p.id),
                "reference": p.reference,
                "supplier_name": p.supplier_name or "Unknown Supplier",
                "bank_name": p.bank_name or "Main Treasury",
                "date": str(p.date),
                "amount": float(p.amount),
                "status": p.status.value
            }
            for p in sorted(payments, key=lambda x: x.created_at or datetime.min, reverse=True)[:5]
        ]

        return APSummaryResponse(
            total_payables=total_payables,
            total_invoiced=total_invoiced,
            total_paid=total_paid,
            invoices_count=len(invoices),
            draft_count=draft_count,
            approved_count=approved_count,
            posted_count=posted_count,
            paid_count=paid_count,
            matched_count=matched_count,
            variance_count=variance_count,
            aging_current=aging_current,
            aging_31_60=aging_31_60,
            aging_61_90=aging_61_90,
            aging_over_90=aging_over_90,
            recent_invoices=recent_inv_data,
            recent_payments=recent_pay_data
        )
