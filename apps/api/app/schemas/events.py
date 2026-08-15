from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from app.models.events import SystemEventType, EventStatus

class SystemEventBase(BaseModel):
    event_type: SystemEventType
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    payload: Dict[str, Any] = {}

class SystemEventCreate(SystemEventBase):
    pass

class SystemEventResponse(SystemEventBase):
    id: UUID
    created_at: datetime
    processed_at: Optional[datetime] = None
    status: EventStatus

    class Config:
        from_attributes = True
