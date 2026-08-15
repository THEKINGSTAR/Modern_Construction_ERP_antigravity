import uuid
import enum
from sqlalchemy import Column, String, Date, Numeric, ForeignKey, Enum, Uuid, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.models import TenantAwareMixin, TimestampMixin, AuditMixin

class AccountType(str, enum.Enum):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"

class JournalStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    REVERSED = "REVERSED"

class ChartOfAccounts(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "chart_of_accounts"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    accounts = relationship("Account", back_populates="chart_of_accounts", cascade="all, delete-orphan")

class Account(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "accounts"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chart_of_accounts_id = Column(Uuid(as_uuid=True), ForeignKey("chart_of_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id = Column(Uuid(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    account_code = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    account_type = Column(Enum(AccountType, native_enum=False), nullable=False, index=True)
    is_control_account = Column(String(50), default="False", nullable=False)

    chart_of_accounts = relationship("ChartOfAccounts", back_populates="accounts")
    parent = relationship("Account", remote_side=[id], backref="children")

class Journal(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "journals"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(Date, nullable=False, index=True)
    reference = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)
    status = Column(Enum(JournalStatus, native_enum=False), default=JournalStatus.DRAFT, nullable=False, index=True)
    reversal_journal_id = Column(Uuid(as_uuid=True), ForeignKey("journals.id", ondelete="SET NULL"), nullable=True)

    lines = relationship("JournalLine", back_populates="journal", cascade="all, delete-orphan")

class JournalLine(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "journal_lines"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journal_id = Column(Uuid(as_uuid=True), ForeignKey("journals.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(Uuid(as_uuid=True), ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    debit = Column(Numeric(18, 4), nullable=False, default=0)
    credit = Column(Numeric(18, 4), nullable=False, default=0)

    # Dimensions
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    cost_code_id = Column(Uuid(as_uuid=True), ForeignKey("cost_codes.id", ondelete="SET NULL"), nullable=True, index=True)
    department_id = Column(Uuid(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    branch_id = Column(Uuid(as_uuid=True), ForeignKey("branches.id", ondelete="SET NULL"), nullable=True, index=True)
    business_unit_id = Column(Uuid(as_uuid=True), ForeignKey("business_units.id", ondelete="SET NULL"), nullable=True, index=True)

    journal = relationship("Journal", back_populates="lines")
    account = relationship("Account")
    project = relationship("Project")
    cost_code = relationship("CostCode")
    department = relationship("Department")
    branch = relationship("Branch")
    business_unit = relationship("BusinessUnit")
