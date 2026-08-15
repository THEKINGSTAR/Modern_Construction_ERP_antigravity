from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.models.notifications import NotificationType

class NotificationBase(BaseModel):
    user_id: UUID
    type: NotificationType
    subject: str
    body: str

class NotificationCreate(NotificationBase):
    pass

class NotificationResponse(NotificationBase):
    id: UUID
    is_read: bool
    sent_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True
