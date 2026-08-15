from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import List

from app.models.events import SystemEvent, EventStatus, SystemEventType
from app.models.notifications import Notification, NotificationType
from app.models.user import User

class EventService:
    def __init__(self, db: Session):
        self.db = db

    def process_pending_events(self) -> int:
        events = self.db.query(SystemEvent).filter(
            SystemEvent.status == EventStatus.PENDING.value
        ).all()

        processed_count = 0
        for event in events:
            try:
                self._process_event(event)
                event.status = EventStatus.PROCESSED.value
                event.processed_at = datetime.utcnow()
                processed_count += 1
            except Exception as e:
                event.status = EventStatus.FAILED.value
                event.processed_at = datetime.utcnow()
                # In production, we'd log the error properly
                print(f"Failed to process event {event.id}: {e}")
                
        self.db.commit()
        return processed_count

    def _process_event(self, event: SystemEvent):
        # We need to determine who should receive the notification.
        # For this MVP, if it's an APPROVAL_REQUIRED, we notify all admins in the tenant.
        # This is a simplification.
        
        users_to_notify: List[User] = []
        if event.event_type in [SystemEventType.APPROVAL_REQUIRED.value, SystemEventType.APPROVAL_COMPLETED.value]:
            users_to_notify = self.db.query(User).filter(User.tenant_id == event.tenant_id).all()
        else:
            # Default to all users for other events in this mock
            users_to_notify = self.db.query(User).filter(User.tenant_id == event.tenant_id).all()
            
        subject = f"System Event: {event.event_type}"
        body = f"Entity: {event.entity_type} {event.entity_id}. Details: {event.payload}"
        
        for user in users_to_notify:
            # Generate IN_APP notification
            notif = Notification(
                tenant_id=event.tenant_id,
                user_id=user.id,
                type=NotificationType.IN_APP.value,
                subject=subject,
                body=body
            )
            self.db.add(notif)
            
            # We could also generate EMAIL notification stubs here
            email_notif = Notification(
                tenant_id=event.tenant_id,
                user_id=user.id,
                type=NotificationType.EMAIL.value,
                subject=subject,
                body=body
            )
            self.db.add(email_notif)
