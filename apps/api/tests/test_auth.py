import pytest
import uuid
from datetime import timedelta
from app.models.tenant import Tenant
from app.models.user import User
from app.models.auth import Role, Permission, UserRole, RolePermission
from app.core.security import get_password_hash, create_access_token
from app.core.context import set_current_tenant_id
from app.core.repository import BaseRepository
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import require_permissions, get_current_user
from app.main import app

# Add test endpoints to the app
test_router = APIRouter()
@test_router.get("/test/protected", dependencies=[Depends(require_permissions(["projects.read"]))])
def protected_endpoint(current_user: User = Depends(get_current_user)):
    return {"message": "Success", "tenant_id": str(current_user.tenant_id)}

@test_router.get("/test/roles")
def get_roles(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = BaseRepository(Role, db)
    return repo.get_all()

app.include_router(test_router)

def test_valid_login(client, db_session):
    tenant_id = uuid.uuid4()
    db_session.add(Tenant(id=tenant_id, name="Auth Tenant"))
    db_session.commit()
    
    set_current_tenant_id(tenant_id)
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password=get_password_hash("securepassword123"),
        tenant_id=tenant_id
    )
    db_session.add(user)
    db_session.commit()
    
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "securepassword123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_invalid_login(client, db_session):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "wrong@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

def test_unauthorized_access(client):
    response = client.get("/test/protected")
    assert response.status_code == 401

def test_role_permissions(client, db_session):
    tenant_id = uuid.uuid4()
    db_session.add(Tenant(id=tenant_id, name="RBAC Tenant"))
    db_session.commit()
    
    set_current_tenant_id(tenant_id)
    
    # Create Permission
    perm = Permission(id=uuid.uuid4(), name="projects.read")
    db_session.add(perm)
    
    # Create Role
    role = Role(id=uuid.uuid4(), name="Project Viewer", tenant_id=tenant_id)
    db_session.add(role)
    db_session.commit()
    
    # Map Role to Permission
    rp = RolePermission(id=uuid.uuid4(), role_id=role.id, permission_id=perm.id, tenant_id=tenant_id)
    db_session.add(rp)
    
    # Create User
    user = User(
        id=uuid.uuid4(),
        email="viewer@example.com",
        hashed_password=get_password_hash("password"),
        tenant_id=tenant_id
    )
    db_session.add(user)
    db_session.commit()
    
    # No roles assigned yet - should fail
    token = create_access_token({"sub": str(user.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id)
    }
    response = client.get("/test/protected", headers=headers)
    assert response.status_code == 403
    
    # Assign Role to User
    ur = UserRole(id=uuid.uuid4(), user_id=user.id, role_id=role.id, tenant_id=tenant_id)
    db_session.add(ur)
    db_session.commit()
    
    # Should succeed now
    response = client.get("/test/protected", headers=headers)
    assert response.status_code == 200
    assert response.json()["tenant_id"] == str(tenant_id)

def test_tenant_isolation_via_auth(client, db_session):
    tenant_a_id = uuid.uuid4()
    tenant_b_id = uuid.uuid4()
    db_session.add_all([
        Tenant(id=tenant_a_id, name="Tenant A"),
        Tenant(id=tenant_b_id, name="Tenant B")
    ])
    db_session.commit()
    
    set_current_tenant_id(tenant_a_id)
    user_a = User(id=uuid.uuid4(), email="a@example.com", hashed_password=get_password_hash("pw"), tenant_id=tenant_a_id, is_superuser=True)
    db_session.add(user_a)
    
    set_current_tenant_id(tenant_b_id)
    role_b = Role(id=uuid.uuid4(), name="Role B", tenant_id=tenant_b_id)
    db_session.add(role_b)
    db_session.commit()
    
    # Authenticate as User A
    token = create_access_token({"sub": str(user_a.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_a_id)
    }
    
    # User A accesses endpoint, tenant context should be Tenant A.
    # Therefore, listing roles using BaseRepository should return empty (Tenant B role is isolated).
    response = client.get("/test/roles", headers=headers)
    assert response.status_code == 200
    roles = response.json()
    assert len(roles) == 0

def test_expired_token(client, db_session):
    tenant_id = uuid.uuid4()
    db_session.add(Tenant(id=tenant_id, name="Expired Tenant"))
    db_session.commit()
    
    user = User(id=uuid.uuid4(), email="expire@example.com", hashed_password=get_password_hash("pw"), tenant_id=tenant_id)
    db_session.add(user)
    db_session.commit()
    
    token = create_access_token({"sub": str(user.id)}, expires_delta=timedelta(seconds=-1))
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/test/protected", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"
