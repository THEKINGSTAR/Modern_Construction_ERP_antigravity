import uuid
from sqlalchemy import Column, String, Uuid
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.models import TenantAwareMixin

class LegalEntity(Base, TenantAwareMixin):
    __tablename__ = "legal_entities"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    tax_id = Column(String(100), nullable=True)
    registration_number = Column(String(100), nullable=True)

    branches = relationship("Branch", back_populates="legal_entity", cascade="all, delete-orphan")
