import uuid
from datetime import date
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.bank import BankAccount, BankTransaction, BankStatement, BankStatementLine, BankStatementStatus
from app.schemas.bank import BankAccountCreate, BankTransactionCreate, BankStatementCreate, ReconciliationMatchRequest

class BankService:
    def __init__(self, db: Session, tenant_id: UUID, current_user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.current_user_id = current_user_id

    def create_bank_account(self, schema: BankAccountCreate) -> BankAccount:
        account = BankAccount(
            tenant_id=self.tenant_id,
            name=schema.name,
            account_number=schema.account_number,
            bank_name=schema.bank_name,
            currency=schema.currency,
            gl_account_id=schema.gl_account_id,
            is_active=schema.is_active,
            created_by=self.current_user_id,
            updated_by=self.current_user_id
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def record_transaction(self, schema: BankTransactionCreate) -> BankTransaction:
        txn = BankTransaction(
            tenant_id=self.tenant_id,
            bank_account_id=schema.bank_account_id,
            date=schema.date,
            transaction_type=schema.transaction_type,
            amount=schema.amount,
            reference=schema.reference,
            description=schema.description,
            reconciled=False,
            created_by=self.current_user_id,
            updated_by=self.current_user_id
        )
        self.db.add(txn)
        self.db.commit()
        self.db.refresh(txn)
        return txn

    def import_statement(self, schema: BankStatementCreate) -> BankStatement:
        stmt = BankStatement(
            tenant_id=self.tenant_id,
            bank_account_id=schema.bank_account_id,
            statement_date=schema.statement_date,
            opening_balance=schema.opening_balance,
            closing_balance=schema.closing_balance,
            status=BankStatementStatus.DRAFT,
            created_by=self.current_user_id,
            updated_by=self.current_user_id
        )
        self.db.add(stmt)
        self.db.flush()

        for line_schema in schema.lines:
            line = BankStatementLine(
                tenant_id=self.tenant_id,
                statement_id=stmt.id,
                date=line_schema.date,
                description=line_schema.description,
                amount=line_schema.amount,
                matched=False,
                created_by=self.current_user_id,
                updated_by=self.current_user_id
            )
            self.db.add(line)

        self.db.commit()
        self.db.refresh(stmt)
        return stmt

    def match_transaction(self, schema: ReconciliationMatchRequest):
        line = self.db.query(BankStatementLine).filter(
            BankStatementLine.id == schema.statement_line_id,
            BankStatementLine.tenant_id == self.tenant_id
        ).first()
        if not line:
            raise HTTPException(status_code=404, detail="Statement line not found")

        txn = self.db.query(BankTransaction).filter(
            BankTransaction.id == schema.bank_transaction_id,
            BankTransaction.tenant_id == self.tenant_id
        ).first()
        if not txn:
            raise HTTPException(status_code=404, detail="Bank transaction not found")

        if line.amount != txn.amount:
            raise HTTPException(status_code=400, detail="Amounts do not match")

        line.matched = True
        line.bank_transaction_id = txn.id
        line.updated_by = self.current_user_id
        
        self.db.commit()
        return line

    def reconcile_statement(self, statement_id: UUID) -> BankStatement:
        stmt = self.db.query(BankStatement).filter(
            BankStatement.id == statement_id,
            BankStatement.tenant_id == self.tenant_id
        ).first()
        if not stmt:
            raise HTTPException(status_code=404, detail="Statement not found")

        unmatched = [line for line in stmt.lines if not line.matched]
        if unmatched:
            raise HTTPException(status_code=400, detail=f"{len(unmatched)} lines are not matched")

        # Mark all matched transactions as reconciled
        for line in stmt.lines:
            if line.bank_transaction_id:
                txn = self.db.query(BankTransaction).get(line.bank_transaction_id)
                txn.reconciled = True
                txn.updated_by = self.current_user_id

        stmt.status = BankStatementStatus.RECONCILED
        stmt.updated_by = self.current_user_id
        self.db.commit()
        self.db.refresh(stmt)
        return stmt
