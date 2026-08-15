from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import os

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.documents import Document, DocumentPermission
from app.schemas.documents import DocumentResponse, DocumentPermissionCreate, DocumentPermissionResponse
from app.services.document_service import DocumentService, STORAGE_DIR

router = APIRouter()

@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    entity_type: str = Form(...),
    entity_id: UUID = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = DocumentService(db, current_user.tenant_id, current_user.id)
    doc = await service.upload_document(entity_type, entity_id, title, file)
    return doc

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document_metadata(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(
        Document.tenant_id == current_user.tenant_id,
        Document.id == document_id
    ).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc

@router.get("/{document_id}/download")
def download_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(
        Document.tenant_id == current_user.tenant_id,
        Document.id == document_id
    ).first()
    if not doc:
        raise HTTPException(404, "Document not found")
        
    local_path = os.path.join(STORAGE_DIR, doc.object_key.replace("/", "_"))
    if not os.path.exists(local_path):
        raise HTTPException(404, "File not found on disk")
        
    return FileResponse(local_path, media_type=doc.mime_type, filename=doc.title)

@router.post("/{document_id}/permissions", response_model=DocumentPermissionResponse, status_code=201)
def create_permission(
    document_id: UUID,
    data: DocumentPermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    perm = DocumentPermission(
        tenant_id=current_user.tenant_id,
        **data.model_dump()
    )
    db.add(perm)
    db.commit()
    db.refresh(perm)
    return perm
