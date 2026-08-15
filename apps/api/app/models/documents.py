from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base

class AccessLevel(str, enum.Enum):
    READ = "READ"
    WRITE = "WRITE"
    ADMIN = "ADMIN"

class ScanResult(str, enum.Enum):
    PENDING = "PENDING"
    CLEAN = "CLEAN"
    INFECTED = "INFECTED"
    ERROR = "ERROR"

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Polymorphic linkage
    entity_type = Column(String, nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    
    title = Column(String, nullable=False)
    object_key = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    current_version = Column(Integer, default=1, nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), nullable=False)
    
    # Security Integration
    is_malware_scanned = Column(Boolean, default=False, nullable=False)
    malware_scan_result = Column(String, default=ScanResult.PENDING.value, nullable=False)

    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    permissions = relationship("DocumentPermission", back_populates="document", cascade="all, delete-orphan")

class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    version_number = Column(Integer, nullable=False)
    object_key = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), nullable=False)
    
    document = relationship("Document", back_populates="versions")

class DocumentPermission(Base):
    __tablename__ = "document_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    user_id = Column(UUID(as_uuid=True), nullable=True)
    role = Column(String, nullable=True)
    access_level = Column(String, nullable=False) # AccessLevel

    document = relationship("Document", back_populates="permissions")
