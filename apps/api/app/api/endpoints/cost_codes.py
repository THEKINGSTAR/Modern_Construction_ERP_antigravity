from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import require_permissions
from app.core.repository import BaseRepository
from app.models.cost_codes import CostCode
from app.schemas.cost_codes import CostCodeCreate, CostCodeUpdate, CostCodeResponse, CostCodeTreeResponse

router = APIRouter()

@router.get("", response_model=List[CostCodeResponse])
def get_cost_codes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["cost_codes.read"]))
):
    repo = BaseRepository(CostCode, db)
    return repo.get_all()[skip : skip + limit]

@router.get("/tree", response_model=List[CostCodeTreeResponse])
def get_cost_codes_tree(
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["cost_codes.read"]))
):
    from app.core.context import get_current_tenant_id
    tenant_id = get_current_tenant_id()
    root_nodes = db.query(CostCode).filter(CostCode.parent_id == None, CostCode.tenant_id == tenant_id).all()
    return root_nodes

@router.get("/{code_id}", response_model=CostCodeResponse)
def get_cost_code(
    code_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["cost_codes.read"]))
):
    repo = BaseRepository(CostCode, db)
    node = repo.get(id=code_id)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cost Code not found")
    return node

@router.post("", response_model=CostCodeResponse, status_code=status.HTTP_201_CREATED)
def create_cost_code(
    code_in: CostCodeCreate,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["cost_codes.create"]))
):
    repo = BaseRepository(CostCode, db)
    return repo.create(code_in.model_dump())

@router.put("/{code_id}", response_model=CostCodeResponse)
def update_cost_code(
    code_id: UUID,
    code_in: CostCodeUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["cost_codes.update"]))
):
    repo = BaseRepository(CostCode, db)
    db_node = repo.get(id=code_id)
    if not db_node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cost Code not found")
    return repo.update(db_obj=db_node, obj_in=code_in.model_dump(exclude_unset=True))

@router.delete("/{code_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cost_code(
    code_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["cost_codes.delete"]))
):
    repo = BaseRepository(CostCode, db)
    db_node = repo.get(id=code_id)
    if not db_node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cost Code not found")
    repo.delete(id=code_id)
