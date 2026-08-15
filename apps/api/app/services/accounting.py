import uuid
from datetime import date
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, select
from fastapi import HTTPException, status
from app.models.accounting import Journal, JournalLine, JournalStatus, Account, AccountType
from app.models.org_settings import AccountingPeriod, FiscalYear
from app.schemas.accounting import JournalCreate, JournalLineCreate, GLBalanceResponse

class AccountingEngine:
    def __init__(self, db: Session, tenant_id: UUID, current_user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.current_user_id = current_user_id

    def _check_period_open(self, target_date: date):
        # Find accounting period for this date
        period = self.db.query(AccountingPeriod).join(FiscalYear).filter(
            AccountingPeriod.tenant_id == self.tenant_id,
            AccountingPeriod.start_date <= target_date,
            AccountingPeriod.end_date >= target_date
        ).first()

        if not period:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No accounting period found for date {target_date}"
            )
        
        if period.is_closed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Accounting period for {target_date} is closed"
            )

    def create_journal(self, schema: JournalCreate, auto_post: bool = False) -> Journal:
        # Schema validates balancing inherently

        journal = Journal(
            tenant_id=self.tenant_id,
            date=schema.date,
            reference=schema.reference,
            description=schema.description,
            status=JournalStatus.DRAFT,
            created_by=self.current_user_id,
            updated_by=self.current_user_id
        )
        self.db.add(journal)
        self.db.flush()

        for line_schema in schema.lines:
            line = JournalLine(
                tenant_id=self.tenant_id,
                journal_id=journal.id,
                account_id=line_schema.account_id,
                debit=line_schema.debit,
                credit=line_schema.credit,
                project_id=line_schema.project_id,
                cost_code_id=line_schema.cost_code_id,
                department_id=line_schema.department_id,
                branch_id=line_schema.branch_id,
                business_unit_id=line_schema.business_unit_id,
                created_by=self.current_user_id,
                updated_by=self.current_user_id
            )
            self.db.add(line)

        self.db.flush()

        if auto_post:
            return self.post_journal(journal.id)
            
        return journal

    def post_journal(self, journal_id: UUID) -> Journal:
        journal = self.db.query(Journal).filter(
            Journal.id == journal_id,
            Journal.tenant_id == self.tenant_id
        ).with_for_update().first()

        if not journal:
            raise HTTPException(status_code=404, detail="Journal not found")
        
        if journal.status == JournalStatus.POSTED:
            raise HTTPException(status_code=400, detail="Journal is already posted")
        
        if journal.status == JournalStatus.REVERSED:
            raise HTTPException(status_code=400, detail="Cannot post a reversed journal")

        self._check_period_open(journal.date)

        # Re-verify balancing just in case
        total_debit = sum(line.debit for line in journal.lines)
        total_credit = sum(line.credit for line in journal.lines)

        if total_debit != total_credit:
            raise HTTPException(status_code=400, detail=f"Journal does not balance. Debits: {total_debit}, Credits: {total_credit}")

        journal.status = JournalStatus.POSTED
        journal.updated_by = self.current_user_id
        
        self.db.flush()
        return journal

    def reverse_journal(self, journal_id: UUID, reversal_date: date, description: str) -> Journal:
        original = self.db.query(Journal).filter(
            Journal.id == journal_id,
            Journal.tenant_id == self.tenant_id
        ).with_for_update().first()

        if not original:
            raise HTTPException(status_code=404, detail="Journal not found")
        
        if original.status != JournalStatus.POSTED:
            raise HTTPException(status_code=400, detail="Can only reverse a posted journal")

        self._check_period_open(reversal_date)

        reversal = Journal(
            tenant_id=self.tenant_id,
            date=reversal_date,
            reference=f"REV-{original.reference or original.id}",
            description=description,
            status=JournalStatus.POSTED,  # Reversals are posted immediately
            created_by=self.current_user_id,
            updated_by=self.current_user_id
        )
        self.db.add(reversal)
        self.db.flush()

        for line in original.lines:
            rev_line = JournalLine(
                tenant_id=self.tenant_id,
                journal_id=reversal.id,
                account_id=line.account_id,
                debit=line.credit, # Swap debit and credit
                credit=line.debit,
                project_id=line.project_id,
                cost_code_id=line.cost_code_id,
                department_id=line.department_id,
                branch_id=line.branch_id,
                business_unit_id=line.business_unit_id,
                created_by=self.current_user_id,
                updated_by=self.current_user_id
            )
            self.db.add(rev_line)

        original.status = JournalStatus.REVERSED
        original.reversal_journal_id = reversal.id
        original.updated_by = self.current_user_id

        self.db.flush()
        return reversal

    def get_gl_balances(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        account_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        department_id: Optional[UUID] = None,
        branch_id: Optional[UUID] = None,
        business_unit_id: Optional[UUID] = None
    ) -> List[GLBalanceResponse]:
        
        query = self.db.query(
            Account.id,
            Account.account_code,
            Account.name,
            Account.account_type,
            func.sum(JournalLine.debit).label("total_debit"),
            func.sum(JournalLine.credit).label("total_credit")
        ).join(
            JournalLine, JournalLine.account_id == Account.id
        ).join(
            Journal, Journal.id == JournalLine.journal_id
        ).filter(
            Account.tenant_id == self.tenant_id,
            Journal.status == JournalStatus.POSTED
        )

        if start_date:
            query = query.filter(Journal.date >= start_date)
        if end_date:
            query = query.filter(Journal.date <= end_date)
        if account_id:
            query = query.filter(Account.id == account_id)
        if project_id:
            query = query.filter(JournalLine.project_id == project_id)
        if department_id:
            query = query.filter(JournalLine.department_id == department_id)
        if branch_id:
            query = query.filter(JournalLine.branch_id == branch_id)
        if business_unit_id:
            query = query.filter(JournalLine.business_unit_id == business_unit_id)

        query = query.group_by(Account.id, Account.account_code, Account.name, Account.account_type)

        results = query.all()
        
        balances = []
        for row in results:
            total_debit = row.total_debit or Decimal(0)
            total_credit = row.total_credit or Decimal(0)

            # Normal balances:
            # Asset / Expense -> Debit is positive
            # Liability / Equity / Revenue -> Credit is positive
            if row.account_type in (AccountType.ASSET, AccountType.EXPENSE):
                balance = total_debit - total_credit
            else:
                balance = total_credit - total_debit
            
            balances.append(GLBalanceResponse(
                account_id=row.id,
                account_code=row.account_code,
                account_name=row.name,
                total_debit=total_debit,
                total_credit=total_credit,
                balance=balance
            ))
            
        return balances
