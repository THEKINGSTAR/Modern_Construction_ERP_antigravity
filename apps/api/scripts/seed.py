import uuid
from app.core.database import SessionLocal
from app.models.tenant import Tenant
from app.models.legal_entity import LegalEntity
from app.models.branch import Branch
from app.core.repository import BaseRepository
from app.core.context import set_current_tenant_id

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
    
    print(f"Seeding complete! Default Tenant ID: {tenant_id}")
    db.close()

if __name__ == "__main__":
    seed_data()
