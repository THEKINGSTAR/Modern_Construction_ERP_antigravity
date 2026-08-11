from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import date
from uuid import UUID
from app.models.projects import ProjectStatus

class ProjectBase(BaseModel):
    project_number: str = Field(..., max_length=100)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    project_type: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = None
    start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    status: ProjectStatus = ProjectStatus.PLANNING
    base_currency: Optional[str] = Field(None, max_length=3)

class ProjectCreate(ProjectBase):
    legal_entity_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    project_manager_id: Optional[UUID] = None

class ProjectUpdate(BaseModel):
    project_number: Optional[str] = Field(None, max_length=100)
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    project_type: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = None
    start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    status: Optional[ProjectStatus] = None
    base_currency: Optional[str] = Field(None, max_length=3)
    legal_entity_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    project_manager_id: Optional[UUID] = None

class ProjectResponse(ProjectBase):
    id: UUID
    legal_entity_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    project_manager_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)
