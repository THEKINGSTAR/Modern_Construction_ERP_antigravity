from sqlalchemy import Column, String, ForeignKey, Boolean, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from datetime import datetime

from app.core.database import Base

class NotificationType(str, enum.Enum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    
    user_id = Column(UUID(as_uuid=True), nullable=False)
    type = Column(String, nullable=False) # NotificationType
    
    subject = Column(String, nullable=False)
    body = Column(String, nullable=False)
    
    is_read = Column(Boolean, default=False, nullable=False)
    sent_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
