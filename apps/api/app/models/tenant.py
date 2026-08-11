import uuid
from sqlalchemy import Column, String, Uuid
from app.core.database import Base
from app.core.models import TimestampMixin, AuditMixin

class Tenant(Base, TimestampMixin, AuditMixin):
    __tablename__ = "tenants"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
