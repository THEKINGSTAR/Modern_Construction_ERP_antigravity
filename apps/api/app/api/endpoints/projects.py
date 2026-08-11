from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any
from uuid import UUID

from app.core.database import get_db
from app.core.auth import require_permissions, get_current_user
from app.core.repository import BaseRepository
from app.models.user import User
from app.models.projects import Project
from app.schemas.projects import ProjectCreate, ProjectUpdate, ProjectResponse

router = APIRouter()

@router.get("/", response_model=List[ProjectResponse])
def get_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["projects.read"]))
):
    repo = BaseRepository(Project, db)
    return repo.get_all()[skip : skip + limit]

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["projects.create"]))
):
    repo = BaseRepository(Project, db)
    project = repo.create(project_in.model_dump())
    return project

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["projects.read"]))
):
    repo = BaseRepository(Project, db)
    project = repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: UUID,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["projects.update"]))
):
    repo = BaseRepository(Project, db)
    project = repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    updated_project = repo.update(project, project_in.model_dump(exclude_unset=True))
    return updated_project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permissions(["projects.delete"]))
):
    repo = BaseRepository(Project, db)
    project = repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    repo.delete(project_id)
