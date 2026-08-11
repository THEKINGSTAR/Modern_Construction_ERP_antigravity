import uuid
from sqlalchemy import Column, String, ForeignKey, Uuid
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.models import TenantAwareMixin

class Branch(Base, TenantAwareMixin):
    __tablename__ = "branches"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    legal_entity_id = Column(Uuid(as_uuid=True), ForeignKey("legal_entities.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)

    legal_entity = relationship("LegalEntity", back_populates="branches")
