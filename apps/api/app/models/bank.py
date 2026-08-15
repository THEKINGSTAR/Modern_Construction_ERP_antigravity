import uuid
import enum
from sqlalchemy import Column, String, Date, Numeric, ForeignKey, Enum, Uuid, Text, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.models import TenantAwareMixin, TimestampMixin, AuditMixin

class BankAccount(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "bank_accounts"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    account_number = Column(String(50), nullable=False)
    bank_name = Column(String(100), nullable=False)
    currency = Column(String(3), default="USD")
    gl_account_id = Column(Uuid(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    is_active = Column(Boolean, default=True)

    gl_account = relationship("Account")
    transactions = relationship("BankTransaction", back_populates="bank_account", cascade="all, delete-orphan")

class BankTransactionType(str, enum.Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"

class BankTransaction(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "bank_transactions"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bank_account_id = Column(Uuid(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False)
    date = Column(Date, nullable=False)
    transaction_type = Column(Enum(BankTransactionType, native_enum=False), nullable=False)
    amount = Column(Numeric(18, 4), nullable=False)
    reference = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    reconciled = Column(Boolean, default=False)
    payment_id = Column(Uuid(as_uuid=True), ForeignKey("payments.id"), nullable=True)

    bank_account = relationship("BankAccount", back_populates="transactions")
    # payment = relationship("Payment", back_populates="bank_transaction") # Added via backref in payment

class BankStatementStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    RECONCILING = "RECONCILING"
    RECONCILED = "RECONCILED"

class BankStatement(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "bank_statements"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bank_account_id = Column(Uuid(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False)
    statement_date = Column(Date, nullable=False)
    opening_balance = Column(Numeric(18, 4), nullable=False)
    closing_balance = Column(Numeric(18, 4), nullable=False)
    status = Column(Enum(BankStatementStatus, native_enum=False), default=BankStatementStatus.DRAFT, nullable=False)

    bank_account = relationship("BankAccount")
    lines = relationship("BankStatementLine", back_populates="statement", cascade="all, delete-orphan")

class BankStatementLine(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "bank_statement_lines"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    statement_id = Column(Uuid(as_uuid=True), ForeignKey("bank_statements.id"), nullable=False)
    date = Column(Date, nullable=False)
    description = Column(String(255), nullable=False)
    amount = Column(Numeric(18, 4), nullable=False)
    matched = Column(Boolean, default=False)
    bank_transaction_id = Column(Uuid(as_uuid=True), ForeignKey("bank_transactions.id"), nullable=True)

    statement = relationship("BankStatement", back_populates="lines")
    bank_transaction = relationship("BankTransaction")
