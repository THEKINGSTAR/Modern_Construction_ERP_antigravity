import uuid
from app.core.database import SessionLocal
from app.models.tenant import Tenant
from app.models.legal_entity import LegalEntity
from app.models.branch import Branch
from app.core.repository import BaseRepository
from app.core.context import set_current_tenant_id
from app.models.user import User
from app.models.auth import Role, Permission, UserRole, RolePermission
from app.core.security import get_password_hash

def seed_data():
    db = SessionLocal()
    
    # Check if a tenant already exists to prevent duplicate seeding
    if db.query(Tenant).first():
        print("Data already seeded.")
        return

    print("Seeding initial data...")
    
    # Create Default Tenant
    tenant_id = uuid.uuid4()
    tenant = Tenant(id=tenant_id, name="Default Construction Corp")
    db.add(tenant)
    db.commit()

    # Set context to the new tenant so Repository can create records
    set_current_tenant_id(tenant_id)
    
    # Create Legal Entity
    repo_le = BaseRepository(LegalEntity, db)
    le = repo_le.create({
        "name": "Construction LLC",
        "tax_id": "TAX-12345",
        "registration_number": "REG-98765"
    })
    
    # Create Branch
    repo_branch = BaseRepository(Branch, db)
    repo_branch.create({
        "legal_entity_id": le.id,
        "name": "HQ - New York",
        "code": "NY-01",
        "address": "123 Build Street, New York, NY"
    })
    
    # Create Permissions
    permissions_list = [
        "projects.read", "projects.create", "projects.update", "projects.approve",
        "finance.journal.post", "inventory.issue.create", "procurement.po.approve"
    ]
    perm_repo = BaseRepository(Permission, db)
    created_perms = []
    for p_name in permissions_list:
        created_perms.append(perm_repo.create({"name": p_name, "description": f"Can {p_name}"}))
        
    # Create Admin Role
    role_repo = BaseRepository(Role, db)
    admin_role = role_repo.create({"name": "System Administrator", "description": "Full access"})
    
    # Associate Permissions to Role
    rp_repo = BaseRepository(RolePermission, db)
    for perm in created_perms:
        rp_repo.create({"role_id": admin_role.id, "permission_id": perm.id})
        
    # Create Admin User
    user_repo = BaseRepository(User, db)
    admin_user = user_repo.create({
        "email": "admin@example.com",
        "hashed_password": get_password_hash("admin"),
        "is_active": True,
        "is_superuser": True,
    })
    
    # Assign Role to User
    ur_repo = BaseRepository(UserRole, db)
    ur_repo.create({"user_id": admin_user.id, "role_id": admin_role.id})
    
    print(f"Seeding complete! Default Tenant ID: {tenant_id}")
    print(f"Admin User created: admin@example.com / admin")
    db.close()

if __name__ == "__main__":
    seed_data()
