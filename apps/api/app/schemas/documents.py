from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.models.documents import AccessLevel, ScanResult

class DocumentBase(BaseModel):
    entity_type: str
    entity_id: UUID
    title: str

class DocumentCreate(DocumentBase):
    pass
    # The actual file is handled via multipart form data in the endpoint, 
    # so we might not need a strict Pydantic model for the upload itself,
    # but we can use this for metadata.

class DocumentVersionResponse(BaseModel):
    id: UUID
    version_number: int
    object_key: str
    file_size: int
    uploaded_by: UUID

    class Config:
        from_attributes = True

class DocumentPermissionResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    role: Optional[str] = None
    access_level: AccessLevel

    class Config:
        from_attributes = True

class DocumentResponse(DocumentBase):
    id: UUID
    object_key: str
    mime_type: str
    file_size: int
    current_version: int
    uploaded_by: UUID
    is_malware_scanned: bool
    malware_scan_result: ScanResult
    
    versions: List[DocumentVersionResponse] = []
    permissions: List[DocumentPermissionResponse] = []

    class Config:
        from_attributes = True

class DocumentPermissionCreate(BaseModel):
    document_id: UUID
    user_id: Optional[UUID] = None
    role: Optional[str] = None
    access_level: AccessLevel
