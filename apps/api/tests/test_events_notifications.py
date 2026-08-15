import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.events import SystemEvent, SystemEventType, EventStatus
from app.services.event_service import EventService

def test_events_and_notifications(client: TestClient, db_session: Session, auth_headers, test_tenant):
    entity_id = uuid4()
    
    # 1. Create a System Event
    event = SystemEvent(
        tenant_id=test_tenant.id,
        event_type=SystemEventType.LOW_STOCK.value,
        entity_type="MATERIAL",
        entity_id=entity_id,
        payload={"material": "Cement", "current_stock": 5}
    )
    db_session.add(event)
    db_session.commit()
    
    # 2. Process events
    service = EventService(db_session)
    processed_count = service.process_pending_events()
    assert processed_count >= 1
    
    # Verify event status
    db_session.refresh(event)
    assert event.status == EventStatus.PROCESSED.value
    
    # 3. Check notifications via API
    notif_res = client.get("/api/v1/notifications", headers=auth_headers)
    assert notif_res.status_code == 200
    notifications = notif_res.json()
    
    # Since EventService notifies all users in tenant for LOW_STOCK, we should have notifications
    assert len(notifications) > 0
    in_app_notifs = [n for n in notifications if n["type"] == "IN_APP"]
    assert len(in_app_notifs) >= 1
    
    target_notif = in_app_notifs[0]
    assert "System Event: LOW_STOCK" in target_notif["subject"]
    assert target_notif["is_read"] == False
    notif_id = target_notif["id"]
    
    # 4. Mark as read
    read_res = client.post(f"/api/v1/notifications/{notif_id}/read", headers=auth_headers)
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] == True
