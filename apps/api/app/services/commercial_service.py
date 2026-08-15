from sqlalchemy.orm import Session
from uuid import UUID
from datetime import date
from typing import List, Optional
from app.core.exceptions import BaseAPIException
from app.models.commercial import (
    Subcontract, ClientChangeOrder, SubcontractChangeOrder,
    ClientPaymentApplication, SubcontractPaymentApplication,
    ChangeOrderStatus, PaymentAppStatus
)
from app.models.contracts import Contract
from app.schemas.commercial import (
    SubcontractCreate, ClientChangeOrderCreate, SubcontractChangeOrderCreate,
    ClientPaymentApplicationCreate, SubcontractPaymentApplicationCreate
)
from app.schemas.accounting import JournalCreate
from app.services.commercial_calculation_engine import PaymentCalculationEngine
from app.services.accounting import AccountingEngine
from app.models.accounting import Journal, JournalLine

class CommercialService:
    def __init__(self, db: Session):
        self.db = db

    # --- Subcontracts ---
    def create_subcontract(self, tenant_id: UUID, user_id: UUID, create_data: SubcontractCreate) -> Subcontract:
        subcontract = Subcontract(
            tenant_id=tenant_id,
            created_by=user_id,
            updated_by=user_id,
            project_id=create_data.project_id,
            supplier_id=create_data.supplier_id,
            subcontract_number=create_data.subcontract_number,
            original_value=create_data.original_value,
            current_value=create_data.original_value,
            currency_code=create_data.currency_code,
            retention_rate=create_data.retention_rate,
            start_date=create_data.start_date,
            end_date=create_data.end_date
        )
        self.db.add(subcontract)
        self.db.commit()
        return subcontract

    # --- Client Change Orders ---
    def create_client_change_order(self, tenant_id: UUID, user_id: UUID, create_data: ClientChangeOrderCreate) -> ClientChangeOrder:
        contract = self.db.get(Contract, create_data.contract_id)
        if not contract or contract.tenant_id != tenant_id:
            raise BaseAPIException(code="NOT_FOUND", message="Contract not found", status_code=404)
            
        cco = ClientChangeOrder(
            tenant_id=tenant_id,
            created_by=user_id,
            updated_by=user_id,
            contract_id=create_data.contract_id,
            number=create_data.number,
            title=create_data.title,
            description=create_data.description,
            amount=create_data.amount,
            status=ChangeOrderStatus.DRAFT
        )
        self.db.add(cco)
        self.db.commit()
        return cco

    def approve_client_change_order(self, tenant_id: UUID, user_id: UUID, cco_id: UUID) -> ClientChangeOrder:
        cco = self.db.get(ClientChangeOrder, cco_id)
        if not cco or cco.tenant_id != tenant_id:
            raise BaseAPIException(code="NOT_FOUND", message="Change order not found", status_code=404)
            
        if cco.status == ChangeOrderStatus.APPROVED:
            return cco
            
        cco.status = ChangeOrderStatus.APPROVED
        cco.approved_date = date.today()
        cco.updated_by = user_id
        
        # Update contract current value
        contract = self.db.get(Contract, cco.contract_id)
        contract.current_value += cco.amount
        
        self.db.commit()
        return cco

    # --- Subcontract Payment Applications ---
    def create_subcontract_payment_application(self, tenant_id: UUID, user_id: UUID, create_data: SubcontractPaymentApplicationCreate) -> SubcontractPaymentApplication:
        subcontract = self.db.get(Subcontract, create_data.subcontract_id)
        if not subcontract or subcontract.tenant_id != tenant_id:
            raise BaseAPIException(code="NOT_FOUND", message="Subcontract not found", status_code=404)
            
        net_amount_due = PaymentCalculationEngine.calculate_net_amount_due(
            gross_work=create_data.gross_work,
            previous_certified_work=create_data.previous_certified_work,
            retention_amount=create_data.retention_amount,
            advance_recovery_amount=create_data.advance_recovery_amount,
            deductions_amount=create_data.deductions_amount,
            adjustments_amount=create_data.adjustments_amount
        )
        
        app = SubcontractPaymentApplication(
            tenant_id=tenant_id,
            created_by=user_id,
            updated_by=user_id,
            subcontract_id=create_data.subcontract_id,
            accounting_period_id=create_data.accounting_period_id,
            number=create_data.number,
            date=create_data.date,
            gross_work=create_data.gross_work,
            previous_certified_work=create_data.previous_certified_work,
            retention_amount=create_data.retention_amount,
            advance_recovery_amount=create_data.advance_recovery_amount,
            deductions_amount=create_data.deductions_amount,
            adjustments_amount=create_data.adjustments_amount,
            net_amount_due=net_amount_due,
            status=PaymentAppStatus.DRAFT
        )
        self.db.add(app)
        self.db.commit()
        return app

    def approve_subcontract_payment_application(self, tenant_id: UUID, user_id: UUID, app_id: UUID) -> SubcontractPaymentApplication:
        app = self.db.get(SubcontractPaymentApplication, app_id)
        if not app or app.tenant_id != tenant_id:
            raise BaseAPIException(code="NOT_FOUND", message="Subcontract Payment Application not found", status_code=404)
            
        if app.status != PaymentAppStatus.DRAFT:
            raise BaseAPIException(code="VALIDATION_ERROR", message="Only DRAFT payment applications can be approved", status_code=400)
            
        app.status = PaymentAppStatus.APPROVED
        app.updated_by = user_id
        self.db.commit()
        return app
        
    def post_subcontract_payment_application(self, tenant_id: UUID, user_id: UUID, app_id: UUID, wip_account_id: UUID, ap_account_id: UUID, retention_account_id: UUID) -> SubcontractPaymentApplication:
        """
        Integrates with General Ledger. 
        Debit WIP/Expense for the current certified work.
        Credit Accounts Payable for the net amount due.
        Credit Retention Payable for the retention deducted.
        """
        app = self.db.get(SubcontractPaymentApplication, app_id)
        if not app or app.tenant_id != tenant_id:
            raise BaseAPIException(code="NOT_FOUND", message="Subcontract Payment Application not found", status_code=404)
            
        if app.status != PaymentAppStatus.APPROVED:
            raise BaseAPIException(code="VALIDATION_ERROR", message="Only APPROVED payment applications can be posted", status_code=400)
            
        subcontract = self.db.get(Subcontract, app.subcontract_id)
            
        current_certified_work = app.gross_work - app.previous_certified_work
            
        # Create Journal
        accounting_engine = AccountingEngine(self.db, tenant_id, user_id)
        
        lines = []
        # Debit WIP (Current Certified Work)
        if current_certified_work > 0:
            lines.append({
                "account_id": wip_account_id,
                "debit": current_certified_work,
                "credit": 0,
                "description": f"Subcontract {subcontract.subcontract_number} App {app.number} Certified Work"
            })
            
        # Credit AP (Net Amount Due)
        if app.net_amount_due > 0:
            lines.append({
                "account_id": ap_account_id,
                "debit": 0,
                "credit": app.net_amount_due,
                "description": f"Subcontract {subcontract.subcontract_number} App {app.number} Net Payable"
            })
            
        # Credit Retention
        if app.retention_amount > 0:
            lines.append({
                "account_id": retention_account_id,
                "debit": 0,
                "credit": app.retention_amount,
                "description": f"Subcontract {subcontract.subcontract_number} App {app.number} Retention"
            })
            
        journal_schema = JournalCreate(
            date=app.date,
            reference=f"SC-APP-{app.number}",
            description=f"Posting Subcontract Payment Application {app.number}",
            lines=lines
        )
        journal = accounting_engine.create_journal(schema=journal_schema)
        
        accounting_engine.post_journal(journal.id)
        
        app.journal_id = journal.id
        app.status = PaymentAppStatus.POSTED
        app.updated_by = user_id
        
        self.db.commit()
        return app

    # --- Client Payment Applications ---
    def create_client_payment_application(self, tenant_id: UUID, user_id: UUID, create_data: ClientPaymentApplicationCreate) -> ClientPaymentApplication:
        contract = self.db.get(Contract, create_data.contract_id)
        if not contract or contract.tenant_id != tenant_id:
            raise BaseAPIException(code="NOT_FOUND", message="Contract not found", status_code=404)
            
        net_amount_due = PaymentCalculationEngine.calculate_net_amount_due(
            gross_work=create_data.gross_work,
            previous_certified_work=create_data.previous_certified_work,
            retention_amount=create_data.retention_amount,
            advance_recovery_amount=create_data.advance_recovery_amount,
            deductions_amount=create_data.deductions_amount,
            adjustments_amount=create_data.adjustments_amount
        )
        
        app = ClientPaymentApplication(
            tenant_id=tenant_id,
            created_by=user_id,
            updated_by=user_id,
            contract_id=create_data.contract_id,
            accounting_period_id=create_data.accounting_period_id,
            number=create_data.number,
            date=create_data.date,
            gross_work=create_data.gross_work,
            previous_certified_work=create_data.previous_certified_work,
            retention_amount=create_data.retention_amount,
            advance_recovery_amount=create_data.advance_recovery_amount,
            deductions_amount=create_data.deductions_amount,
            adjustments_amount=create_data.adjustments_amount,
            net_amount_due=net_amount_due,
            status=PaymentAppStatus.DRAFT
        )
        self.db.add(app)
        self.db.commit()
        return app

    def approve_client_payment_application(self, tenant_id: UUID, user_id: UUID, app_id: UUID) -> ClientPaymentApplication:
        app = self.db.get(ClientPaymentApplication, app_id)
        if not app or app.tenant_id != tenant_id:
            raise BaseAPIException(code="NOT_FOUND", message="Client Payment Application not found", status_code=404)
            
        if app.status != PaymentAppStatus.DRAFT:
            raise BaseAPIException(code="VALIDATION_ERROR", message="Only DRAFT payment applications can be approved", status_code=400)
            
        app.status = PaymentAppStatus.APPROVED
        app.updated_by = user_id
        self.db.commit()
        return app
        
    def post_client_payment_application(self, tenant_id: UUID, user_id: UUID, app_id: UUID, ar_account_id: UUID, revenue_account_id: UUID, retention_account_id: UUID) -> ClientPaymentApplication:
        """
        Integrates with General Ledger.
        Debit Accounts Receivable (Net Amount Due)
        Debit Retention Receivable (Retention Amount)
        Credit Revenue (Current Certified Work)
        """
        app = self.db.get(ClientPaymentApplication, app_id)
        if not app or app.tenant_id != tenant_id:
            raise BaseAPIException(code="NOT_FOUND", message="Client Payment Application not found", status_code=404)
            
        if app.status != PaymentAppStatus.APPROVED:
            raise BaseAPIException(code="VALIDATION_ERROR", message="Only APPROVED payment applications can be posted", status_code=400)
            
        contract = self.db.get(Contract, app.contract_id)
            
        current_certified_work = app.gross_work - app.previous_certified_work
            
        # Create Journal
        accounting_engine = AccountingEngine(self.db)
        
        lines = []
        
        # Debit AR (Net Amount Due)
        if app.net_amount_due > 0:
            lines.append({
                "account_id": ar_account_id,
                "debit": app.net_amount_due,
                "credit": 0,
                "description": f"Contract {contract.contract_number} App {app.number} Net Receivable"
            })
            
        # Debit Retention Receivable
        if app.retention_amount > 0:
            lines.append({
                "account_id": retention_account_id,
                "debit": app.retention_amount,
                "credit": 0,
                "description": f"Contract {contract.contract_number} App {app.number} Retention"
            })
            
        # Credit Revenue (Current Certified Work)
        if current_certified_work > 0:
            lines.append({
                "account_id": revenue_account_id,
                "debit": 0,
                "credit": current_certified_work,
                "description": f"Contract {contract.contract_number} App {app.number} Certified Work"
            })
            
        journal_schema = JournalCreate(
            date=app.date,
            reference=f"CL-APP-{app.number}",
            description=f"Posting Client Payment Application {app.number}",
            lines=lines
        )
        journal = accounting_engine.create_journal(schema=journal_schema)
        
        accounting_engine.post_journal(journal.id)
        
        app.journal_id = journal.id
        app.status = PaymentAppStatus.POSTED
        app.updated_by = user_id
        
        self.db.commit()
        return app
