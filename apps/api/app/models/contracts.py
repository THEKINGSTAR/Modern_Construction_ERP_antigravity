import uuid
import enum
from sqlalchemy import Column, String, Uuid, Numeric, Date, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.models import TenantAwareMixin, TimestampMixin, AuditMixin

class ContractStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class ContractType(Base, TenantAwareMixin, TimestampMixin):
    __tablename__ = "contract_types"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

class Contract(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "contracts"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    client_id = Column(Uuid(as_uuid=True), ForeignKey("clients.id", ondelete="RESTRICT"), nullable=True)
    contract_number = Column(String(100), nullable=False)
    contract_type_id = Column(Uuid(as_uuid=True), ForeignKey("contract_types.id", ondelete="RESTRICT"), nullable=False)
    
    original_value = Column(Numeric(18, 6), default=0.0, nullable=False)
    current_value = Column(Numeric(18, 6), default=0.0, nullable=False)
    currency_code = Column(String(3), ForeignKey("currencies.code", ondelete="RESTRICT"), nullable=False)
    
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    retention_rate = Column(Numeric(5, 2), default=0.0, nullable=False)
    payment_terms = Column(String(255), nullable=True)
    status = Column(Enum(ContractStatus, name="contract_status_enum", create_type=False), default=ContractStatus.DRAFT, nullable=False)
    
    project = relationship("Project")
    client = relationship("Client")
    contract_type = relationship("ContractType")
