from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import require_permissions
from app.core.repository import BaseRepository
from app.models.wbs import WBSNode
from app.schemas.wbs import WBSNodeCreate, WBSNodeUpdate, WBSNodeResponse, WBSNodeTreeResponse

router = APIRouter()

@router.get("", response_model=List[WBSNodeResponse])
def get_wbs_nodes(
    skip: int = 0,
    limit: int = 100,
    project_id: UUID = None,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["wbs.read"]))
):
    query = db.query(WBSNode)
    if project_id:
        query = query.filter(WBSNode.project_id == project_id)
    return query.all()[skip : skip + limit]

@router.get("/tree/{project_id}", response_model=List[WBSNodeTreeResponse])
def get_wbs_tree(
    project_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["wbs.read"]))
):
    root_nodes = db.query(WBSNode).filter(
        WBSNode.project_id == project_id,
        WBSNode.parent_id == None
    ).all()
    return root_nodes

@router.get("/{node_id}", response_model=WBSNodeResponse)
def get_wbs_node(
    node_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["wbs.read"]))
):
    repo = BaseRepository(WBSNode, db)
    node = repo.get(id=node_id)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="WBS Node not found")
    return node

@router.post("", response_model=WBSNodeResponse, status_code=status.HTTP_201_CREATED)
def create_wbs_node(
    node_in: WBSNodeCreate,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["wbs.create"]))
):
    repo = BaseRepository(WBSNode, db)
    return repo.create(node_in.model_dump())

@router.put("/{node_id}", response_model=WBSNodeResponse)
def update_wbs_node(
    node_id: UUID,
    node_in: WBSNodeUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["wbs.update"]))
):
    repo = BaseRepository(WBSNode, db)
    db_node = repo.get(id=node_id)
    if not db_node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="WBS Node not found")
    return repo.update(db_obj=db_node, obj_in=node_in.model_dump(exclude_unset=True))

@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wbs_node(
    node_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["wbs.delete"]))
):
    repo = BaseRepository(WBSNode, db)
    db_node = repo.get(id=node_id)
    if not db_node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="WBS Node not found")
    repo.delete(id=node_id)
