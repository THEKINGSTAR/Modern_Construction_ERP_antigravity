from sqlalchemy import Column, String, DateTime, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import enum
from datetime import datetime

from app.core.database import Base

class SystemEventType(str, enum.Enum):
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVAL_COMPLETED = "APPROVAL_COMPLETED"
    INVOICE_DUE = "INVOICE_DUE"
    PAYMENT_OVERDUE = "PAYMENT_OVERDUE"
    LOW_STOCK = "LOW_STOCK"
    BUDGET_VARIANCE = "BUDGET_VARIANCE"
    CONTRACT_EXPIRY = "CONTRACT_EXPIRY"

class EventStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"

class SystemEvent(Base):
    __tablename__ = "system_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    
    event_type = Column(String, nullable=False) # SystemEventType
    entity_type = Column(String, nullable=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    
    payload = Column(JSON().with_variant(JSONB, 'postgresql'), nullable=False, default={})
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default=EventStatus.PENDING.value, nullable=False)
