from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import require_permissions
from app.core.repository import BaseRepository
from app.models.contracts import Contract, ContractType
from app.schemas.contracts import (
    ContractCreate, ContractUpdate, ContractResponse,
    ContractTypeCreate, ContractTypeUpdate, ContractTypeResponse
)

router = APIRouter()

# --- Contract Types ---

@router.get("/types", response_model=List[ContractTypeResponse])
def get_contract_types(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["contracts.read"]))
):
    repo = BaseRepository(ContractType, db)
    return repo.get_all()[skip : skip + limit]

@router.post("/types", response_model=ContractTypeResponse, status_code=status.HTTP_201_CREATED)
def create_contract_type(
    contract_type_in: ContractTypeCreate,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["contracts.create"]))
):
    repo = BaseRepository(ContractType, db)
    return repo.create(contract_type_in.model_dump())

@router.put("/types/{type_id}", response_model=ContractTypeResponse)
def update_contract_type(
    type_id: UUID,
    contract_type_in: ContractTypeUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["contracts.update"]))
):
    repo = BaseRepository(ContractType, db)
    db_type = repo.get(id=type_id)
    if not db_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract type not found")
    return repo.update(db_obj=db_type, obj_in=contract_type_in.model_dump(exclude_unset=True))

@router.delete("/types/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract_type(
    type_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["contracts.delete"]))
):
    repo = BaseRepository(ContractType, db)
    db_type = repo.get(id=type_id)
    if not db_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract type not found")
    repo.delete(id=type_id)

# --- Contracts ---

@router.get("", response_model=List[ContractResponse])
def get_contracts(
    skip: int = 0,
    limit: int = 100,
    project_id: UUID = None,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["contracts.read"]))
):
    repo = BaseRepository(Contract, db)
    filters = {}
    if project_id:
        filters["project_id"] = project_id
    return repo.get_all(skip=skip, limit=limit, **filters)

@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract(
    contract_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["contracts.read"]))
):
    repo = BaseRepository(Contract, db)
    contract = repo.get(id=contract_id)
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    return contract

@router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(
    contract_in: ContractCreate,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["contracts.create"]))
):
    repo = BaseRepository(Contract, db)
    data = contract_in.model_dump()
    data["current_value"] = data.get("original_value", 0.0)
    return repo.create(data)

@router.put("/{contract_id}", response_model=ContractResponse)
def update_contract(
    contract_id: UUID,
    contract_in: ContractUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["contracts.update"]))
):
    repo = BaseRepository(Contract, db)
    db_contract = repo.get(id=contract_id)
    if not db_contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    return repo.update(db_obj=db_contract, obj_in=contract_in.model_dump(exclude_unset=True))

@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract(
    contract_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["contracts.delete"]))
):
    repo = BaseRepository(Contract, db)
    db_contract = repo.get(id=contract_id)
    if not db_contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    repo.delete(id=contract_id)
