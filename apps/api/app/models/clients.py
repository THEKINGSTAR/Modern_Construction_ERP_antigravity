import uuid
from sqlalchemy import Column, String, Text, Boolean, Uuid, ForeignKey
from app.core.database import Base
from app.core.models import TenantAwareMixin

class Client(Base, TenantAwareMixin):
    __tablename__ = "clients"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    legal_name = Column(String(255), nullable=True)
    contact_information = Column(Text, nullable=True)
    billing_address = Column(Text, nullable=True)
    tax_identifier = Column(String(100), nullable=True)
    status = Column(String(50), nullable=False, default="ACTIVE", index=True)

class ClientContact(Base, TenantAwareMixin):
    __tablename__ = "client_contacts"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(Uuid(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(100), nullable=True)
    role = Column(String(100), nullable=True)
    is_primary = Column(Boolean, nullable=False, default=False)
