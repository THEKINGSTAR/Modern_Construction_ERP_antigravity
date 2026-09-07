from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from datetime import date
from decimal import Decimal
from typing import List, Optional, Dict, Any
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
        self.db.refresh(subcontract)
        return subcontract

    def get_subcontracts(self, tenant_id: UUID, project_id: Optional[UUID] = None) -> List[Subcontract]:
        query = self.db.query(Subcontract).filter(Subcontract.tenant_id == tenant_id)
        if project_id:
            query = query.filter(Subcontract.project_id == project_id)
        return query.order_by(Subcontract.created_at.desc()).all()

    def get_subcontract(self, tenant_id: UUID, subcontract_id: UUID) -> Optional[Subcontract]:
        return self.db.query(Subcontract).filter(
            Subcontract.tenant_id == tenant_id,
            Subcontract.id == subcontract_id
        ).first()

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
        self.db.refresh(cco)
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
        if contract:
            contract.current_value += cco.amount
        
        self.db.commit()
        self.db.refresh(cco)
        return cco

    def get_client_change_orders(self, tenant_id: UUID, contract_id: Optional[UUID] = None) -> List[ClientChangeOrder]:
        query = self.db.query(ClientChangeOrder).filter(ClientChangeOrder.tenant_id == tenant_id)
        if contract_id:
            query = query.filter(ClientChangeOrder.contract_id == contract_id)
        return query.order_by(ClientChangeOrder.created_at.desc()).all()

    # --- Subcontract Change Orders ---
    def create_subcontract_change_order(self, tenant_id: UUID, user_id: UUID, create_data: SubcontractChangeOrderCreate) -> SubcontractChangeOrder:
        subcontract = self.db.get(Subcontract, create_data.subcontract_id)
        if not subcontract or subcontract.tenant_id != tenant_id:
            raise BaseAPIException(code="NOT_FOUND", message="Subcontract not found", status_code=404)
            
        sco = SubcontractChangeOrder(
            tenant_id=tenant_id,
            created_by=user_id,
            updated_by=user_id,
            subcontract_id=create_data.subcontract_id,
            number=create_data.number,
            title=create_data.title,
            description=create_data.description,
            amount=create_data.amount,
            status=ChangeOrderStatus.DRAFT
        )
        self.db.add(sco)
        self.db.commit()
        self.db.refresh(sco)
        return sco

    def approve_subcontract_change_order(self, tenant_id: UUID, user_id: UUID, sco_id: UUID) -> SubcontractChangeOrder:
        sco = self.db.get(SubcontractChangeOrder, sco_id)
        if not sco or sco.tenant_id != tenant_id:
            raise BaseAPIException(code="NOT_FOUND", message="Subcontract change order not found", status_code=404)
            
        if sco.status == ChangeOrderStatus.APPROVED:
            return sco
            
        sco.status = ChangeOrderStatus.APPROVED
        sco.approved_date = date.today()
        sco.updated_by = user_id
        
        # Update subcontract current value
        subcontract = self.db.get(Subcontract, sco.subcontract_id)
        if subcontract:
            subcontract.current_value += sco.amount
        
        self.db.commit()
        self.db.refresh(sco)
        return sco

    def get_subcontract_change_orders(self, tenant_id: UUID, subcontract_id: Optional[UUID] = None) -> List[SubcontractChangeOrder]:
        query = self.db.query(SubcontractChangeOrder).filter(SubcontractChangeOrder.tenant_id == tenant_id)
        if subcontract_id:
            query = query.filter(SubcontractChangeOrder.subcontract_id == subcontract_id)
        return query.order_by(SubcontractChangeOrder.created_at.desc()).all()

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
        self.db.refresh(app)
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
        self.db.refresh(app)
        return app
        
    def post_subcontract_payment_application(self, tenant_id: UUID, user_id: UUID, app_id: UUID, wip_account_id: UUID, ap_account_id: UUID, retention_account_id: UUID) -> SubcontractPaymentApplication:
        app = self.db.get(SubcontractPaymentApplication, app_id)
        if not app or app.tenant_id != tenant_id:
            raise BaseAPIException(code="NOT_FOUND", message="Subcontract Payment Application not found", status_code=404)
            
        if app.status != PaymentAppStatus.APPROVED:
            raise BaseAPIException(code="VALIDATION_ERROR", message="Only APPROVED payment applications can be posted", status_code=400)
            
        subcontract = self.db.get(Subcontract, app.subcontract_id)
        current_certified_work = app.gross_work - app.previous_certified_work
            
        accounting_engine = AccountingEngine(self.db, tenant_id, user_id)
        
        lines = []
        if current_certified_work > 0:
            lines.append({
                "account_id": wip_account_id,
                "debit": current_certified_work,
                "credit": 0,
                "description": f"Subcontract {subcontract.subcontract_number} App {app.number} Certified Work"
            })
            
        if app.net_amount_due > 0:
            lines.append({
                "account_id": ap_account_id,
                "debit": 0,
                "credit": app.net_amount_due,
                "description": f"Subcontract {subcontract.subcontract_number} App {app.number} Net Payable"
            })
            
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
        self.db.refresh(app)
        return app

    def get_subcontract_payment_applications(self, tenant_id: UUID, subcontract_id: Optional[UUID] = None) -> List[SubcontractPaymentApplication]:
        query = self.db.query(SubcontractPaymentApplication).filter(SubcontractPaymentApplication.tenant_id == tenant_id)
        if subcontract_id:
            query = query.filter(SubcontractPaymentApplication.subcontract_id == subcontract_id)
        return query.order_by(SubcontractPaymentApplication.created_at.desc()).all()

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
        self.db.refresh(app)
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
        self.db.refresh(app)
        return app
        
    def post_client_payment_application(self, tenant_id: UUID, user_id: UUID, app_id: UUID, ar_account_id: UUID, revenue_account_id: UUID, retention_account_id: UUID) -> ClientPaymentApplication:
        app = self.db.get(ClientPaymentApplication, app_id)
        if not app or app.tenant_id != tenant_id:
            raise BaseAPIException(code="NOT_FOUND", message="Client Payment Application not found", status_code=404)
            
        if app.status != PaymentAppStatus.APPROVED:
            raise BaseAPIException(code="VALIDATION_ERROR", message="Only APPROVED payment applications can be posted", status_code=400)
            
        contract = self.db.get(Contract, app.contract_id)
        current_certified_work = app.gross_work - app.previous_certified_work
            
        accounting_engine = AccountingEngine(self.db, tenant_id, user_id)
        
        lines = []
        if app.net_amount_due > 0:
            lines.append({
                "account_id": ar_account_id,
                "debit": app.net_amount_due,
                "credit": 0,
                "description": f"Contract {contract.contract_number} App {app.number} Net Receivable"
            })
            
        if app.retention_amount > 0:
            lines.append({
                "account_id": retention_account_id,
                "debit": app.retention_amount,
                "credit": 0,
                "description": f"Contract {contract.contract_number} App {app.number} Retention"
            })
            
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
        self.db.refresh(app)
        return app

    def get_client_payment_applications(self, tenant_id: UUID, contract_id: Optional[UUID] = None) -> List[ClientPaymentApplication]:
        query = self.db.query(ClientPaymentApplication).filter(ClientPaymentApplication.tenant_id == tenant_id)
        if contract_id:
            query = query.filter(ClientPaymentApplication.contract_id == contract_id)
        return query.order_by(ClientPaymentApplication.created_at.desc()).all()

    # --- Summary ---
    def get_commercial_summary(self, tenant_id: UUID) -> Dict[str, Any]:
        total_contracts = self.db.query(func.coalesce(func.sum(Contract.current_value), 0)).filter(Contract.tenant_id == tenant_id).scalar() or Decimal("0.0")
        total_subcontracts = self.db.query(func.coalesce(func.sum(Subcontract.current_value), 0)).filter(Subcontract.tenant_id == tenant_id).scalar() or Decimal("0.0")
        
        total_cco_app = self.db.query(func.coalesce(func.sum(ClientChangeOrder.amount), 0)).filter(
            ClientChangeOrder.tenant_id == tenant_id,
            ClientChangeOrder.status == ChangeOrderStatus.APPROVED
        ).scalar() or Decimal("0.0")
        
        total_cco_pen = self.db.query(func.coalesce(func.sum(ClientChangeOrder.amount), 0)).filter(
            ClientChangeOrder.tenant_id == tenant_id,
            ClientChangeOrder.status.in_([ChangeOrderStatus.DRAFT, ChangeOrderStatus.SUBMITTED, ChangeOrderStatus.UNDER_REVIEW])
        ).scalar() or Decimal("0.0")
        
        total_sco_app = self.db.query(func.coalesce(func.sum(SubcontractChangeOrder.amount), 0)).filter(
            SubcontractChangeOrder.tenant_id == tenant_id,
            SubcontractChangeOrder.status == ChangeOrderStatus.APPROVED
        ).scalar() or Decimal("0.0")
        
        total_cl_billed = self.db.query(func.coalesce(func.sum(ClientPaymentApplication.gross_work), 0)).filter(ClientPaymentApplication.tenant_id == tenant_id).scalar() or Decimal("0.0")
        total_cl_ret = self.db.query(func.coalesce(func.sum(ClientPaymentApplication.retention_amount), 0)).filter(ClientPaymentApplication.tenant_id == tenant_id).scalar() or Decimal("0.0")
        
        total_sc_billed = self.db.query(func.coalesce(func.sum(SubcontractPaymentApplication.gross_work), 0)).filter(SubcontractPaymentApplication.tenant_id == tenant_id).scalar() or Decimal("0.0")
        total_sc_ret = self.db.query(func.coalesce(func.sum(SubcontractPaymentApplication.retention_amount), 0)).filter(SubcontractPaymentApplication.tenant_id == tenant_id).scalar() or Decimal("0.0")
        
        subcontracts_count = self.db.query(func.count(Subcontract.id)).filter(Subcontract.tenant_id == tenant_id).scalar() or 0
        cco_count = self.db.query(func.count(ClientChangeOrder.id)).filter(ClientChangeOrder.tenant_id == tenant_id).scalar() or 0
        sco_count = self.db.query(func.count(SubcontractChangeOrder.id)).filter(SubcontractChangeOrder.tenant_id == tenant_id).scalar() or 0
        cl_app_count = self.db.query(func.count(ClientPaymentApplication.id)).filter(ClientPaymentApplication.tenant_id == tenant_id).scalar() or 0
        sc_app_count = self.db.query(func.count(SubcontractPaymentApplication.id)).filter(SubcontractPaymentApplication.tenant_id == tenant_id).scalar() or 0
        
        return {
            "total_prime_contract_value": Decimal(str(total_contracts)),
            "total_subcontracts_value": Decimal(str(total_subcontracts)),
            "total_client_change_orders_approved": Decimal(str(total_cco_app)),
            "total_client_change_orders_pending": Decimal(str(total_cco_pen)),
            "total_subcontract_change_orders_approved": Decimal(str(total_sco_app)),
            "total_client_billed": Decimal(str(total_cl_billed)),
            "total_client_retention": Decimal(str(total_cl_ret)),
            "total_subcontractor_billed": Decimal(str(total_sc_billed)),
            "total_subcontractor_retention": Decimal(str(total_sc_ret)),
            "subcontracts_count": subcontracts_count,
            "change_orders_count": cco_count + sco_count,
            "payment_applications_count": cl_app_count + sc_app_count
        }
