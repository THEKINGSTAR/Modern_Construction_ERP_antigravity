import uuid
from sqlalchemy import Column, String, Text, Boolean, Uuid
from app.core.database import Base
from app.core.models import TenantAwareMixin

class Material(Base, TenantAwareMixin):
    __tablename__ = "materials"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    material_code = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    base_unit = Column(String(50), nullable=False)
    alternate_units = Column(Text, nullable=True)
    conversion = Column(Text, nullable=True)
    active = Column(Boolean, default=True, nullable=False, index=True)
