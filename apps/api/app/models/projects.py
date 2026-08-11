import uuid
import enum
from sqlalchemy import Column, String, Text, Date, Enum, Uuid, ForeignKey
from app.core.database import Base
from app.core.models import TenantAwareMixin

class ProjectStatus(str, enum.Enum):
    PLANNING = "PLANNING"
    BIDDING = "BIDDING"
    AWARDED = "AWARDED"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"

class Project(Base, TenantAwareMixin):
    __tablename__ = "projects"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    legal_entity_id = Column(Uuid(as_uuid=True), ForeignKey("legal_entities.id", ondelete="RESTRICT"), nullable=True, index=True)
    project_number = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    client_id = Column(Uuid(as_uuid=True), ForeignKey("clients.id", ondelete="RESTRICT"), nullable=True, index=True)
    project_type = Column(String(100), nullable=True)
    location = Column(Text, nullable=True)
    start_date = Column(Date, nullable=True)
    planned_end_date = Column(Date, nullable=True)
    actual_end_date = Column(Date, nullable=True)
    status = Column(Enum(ProjectStatus), nullable=False, default=ProjectStatus.PLANNING, index=True)
    base_currency = Column(String(3), nullable=True)
    project_manager_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
