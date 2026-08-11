from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any
from uuid import UUID

from app.core.database import get_db
from app.core.auth import require_permissions, get_current_user
from app.core.repository import BaseRepository
from app.models.user import User
from app.models.clients import Client, ClientContact
from app.schemas.clients import ClientCreate, ClientUpdate, ClientResponse, ClientDetailResponse

router = APIRouter()

@router.get("/", response_model=List[ClientResponse])
def get_clients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["clients.read"]))
):
    repo = BaseRepository(Client, db)
    return repo.get_all()[skip : skip + limit]

@router.post("/", response_model=ClientDetailResponse, status_code=status.HTTP_201_CREATED)
def create_client(
    client_in: ClientCreate,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["clients.create"]))
):
    repo = BaseRepository(Client, db)
    client_data = client_in.model_dump(exclude={"contacts"})
    client = repo.create(client_data)
    
    if client_in.contacts:
        contact_repo = BaseRepository(ClientContact, db)
        for contact_in in client_in.contacts:
            contact_data = contact_in.model_dump()
            contact_data["client_id"] = client.id
            contact_repo.create(contact_data)
            
    db.refresh(client)
    # The client response needs contacts, but BaseRepository might not lazy load it implicitly unless we define relationship.
    # We should fetch them explicitly or assume the relationship handles it. Let's fetch explicitly.
    contacts = db.query(ClientContact).filter(ClientContact.client_id == client.id).all()
    client_dict = {
        "id": client.id,
        "name": client.name,
        "legal_name": client.legal_name,
        "contact_information": client.contact_information,
        "billing_address": client.billing_address,
        "tax_identifier": client.tax_identifier,
        "status": client.status,
        "contacts": contacts
    }
    return client_dict

@router.get("/{client_id}", response_model=ClientDetailResponse)
def get_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["clients.read"]))
):
    repo = BaseRepository(Client, db)
    client = repo.get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    contacts = db.query(ClientContact).filter(ClientContact.client_id == client.id).all()
    client_dict = {
        "id": client.id,
        "name": client.name,
        "legal_name": client.legal_name,
        "contact_information": client.contact_information,
        "billing_address": client.billing_address,
        "tax_identifier": client.tax_identifier,
        "status": client.status,
        "contacts": contacts
    }
    return client_dict

@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: UUID,
    client_in: ClientUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["clients.update"]))
):
    repo = BaseRepository(Client, db)
    client = repo.get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    updated_client = repo.update(client, client_in.model_dump(exclude_unset=True))
    return updated_client

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["clients.delete"]))
):
    repo = BaseRepository(Client, db)
    client = repo.get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    repo.delete(client_id)
