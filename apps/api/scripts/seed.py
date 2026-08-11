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
        "projects.read", "projects.create", "projects.update", "projects.approve", "projects.delete",
        "clients.read", "clients.create", "clients.update", "clients.delete",
        "finance.journal.post", "inventory.issue.create", "procurement.po.approve"
    ]
    perm_repo = BaseRepository(Permission, db)
    created_perms = {}
    for p_name in permissions_list:
        created_perms[p_name] = perm_repo.create({"name": p_name, "description": f"Can {p_name}"})
        
    # Create Admin Role
    role_repo = BaseRepository(Role, db)
    admin_role = role_repo.create({"name": "System Administrator", "description": "Full access"})
    
    # Create Project Manager Role
    pm_role = role_repo.create({"name": "Project Manager", "description": "Project Management access"})
    
    # Associate Permissions to Roles
    rp_repo = BaseRepository(RolePermission, db)
    for p_name, perm in created_perms.items():
        rp_repo.create({"role_id": admin_role.id, "permission_id": perm.id})
        if p_name.startswith("projects.") or p_name.startswith("clients."):
            rp_repo.create({"role_id": pm_role.id, "permission_id": perm.id})
        
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
    
    # Create Currencies (Global)
    from app.models.org_settings import Currency, TenantSettings, FiscalYear
    import datetime
    
    currencies = [
        Currency(code="USD", name="US Dollar", symbol="$"),
        Currency(code="EGP", name="Egyptian Pound", symbol="E£"),
        Currency(code="EUR", name="Euro", symbol="€"),
        Currency(code="AED", name="UAE Dirham", symbol="د.إ")
    ]
    db.add_all(currencies)
    db.commit()
    
    # Create Tenant Settings
    ts_repo = BaseRepository(TenantSettings, db)
    ts_repo.create({
        "base_currency_code": "USD",
        "default_locale": "en-US",
        "default_timezone": "UTC",
        "default_date_format": "YYYY-MM-DD",
        "default_number_format": "#,##0.00"
    })
    
    # Create Fiscal Year
    fy_repo = BaseRepository(FiscalYear, db)
    fy_repo.create({
        "name": "FY-2026",
        "start_date": datetime.date(2026, 1, 1),
        "end_date": datetime.date(2026, 12, 31),
        "is_closed": False
    })
    
    print(f"Seeding complete! Default Tenant ID: {tenant_id}")
    print(f"Admin User created: admin@example.com / admin")
    db.close()

if __name__ == "__main__":
    seed_data()
