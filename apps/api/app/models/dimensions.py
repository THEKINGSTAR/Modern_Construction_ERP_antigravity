import uuid
from sqlalchemy import Column, String, Uuid
from app.core.database import Base
from app.core.models import TenantAwareMixin

class Department(Base, TenantAwareMixin):
    __tablename__ = "departments"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False, index=True)

class BusinessUnit(Base, TenantAwareMixin):
    __tablename__ = "business_units"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False, index=True)
