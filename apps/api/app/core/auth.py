from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session
from uuid import UUID

from app.config import settings
from app.core.database import get_db
from app.core.security import ALGORITHM
from app.core.context import set_current_tenant_id
from app.models.user import User
from app.models.auth import Role, Permission, UserRole, RolePermission

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except (jwt.PyJWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Note: We must NOT use BaseRepository here because the context might not be set yet.
    # We query the DB directly, and then set the context.
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # Critical: Set tenant context based on the user's tenant
    set_current_tenant_id(user.tenant_id)
    
    return user

def get_current_tenant(current_user: User = Depends(get_current_user)) -> UUID:
    return current_user.tenant_id

def require_permissions(required_permissions: list[str]):
    def permission_checker(
        current_user: User = Depends(get_current_user), 
        db: Session = Depends(get_db)
    ):
        if current_user.is_superuser:
            return True

        # Fetch all permissions for this user
        user_roles = db.query(UserRole).filter(UserRole.user_id == current_user.id).all()
        role_ids = [ur.role_id for ur in user_roles]
        
        if not role_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Not enough permissions"
            )

        role_permissions = (
            db.query(RolePermission)
            .filter(RolePermission.role_id.in_(role_ids))
            .all()
        )
        permission_ids = [rp.permission_id for rp in role_permissions]
        
        permissions = (
            db.query(Permission)
            .filter(Permission.id.in_(permission_ids))
            .all()
        )
        user_perms = {p.name for p in permissions}

        for req in required_permissions:
            if req not in user_perms:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail="Not enough permissions"
                )
        return True
    
    return permission_checker
