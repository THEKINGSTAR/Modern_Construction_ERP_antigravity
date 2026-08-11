import pytest
import uuid
from app.models.tenant import Tenant
from app.models.legal_entity import LegalEntity
from app.core.repository import BaseRepository
from app.core.context import set_current_tenant_id

def test_tenant_isolation_at_repository_layer(db_session):
    # 1. Create two tenants
    tenant_a_id = uuid.uuid4()
    tenant_b_id = uuid.uuid4()
    
    t_a = Tenant(id=tenant_a_id, name="Tenant A")
    t_b = Tenant(id=tenant_b_id, name="Tenant B")
    db_session.add_all([t_a, t_b])
    db_session.commit()

    # 2. Set context to Tenant A and create a Legal Entity
    set_current_tenant_id(tenant_a_id)
    repo_le = BaseRepository(LegalEntity, db_session)
    le_a = repo_le.create({"name": "Legal Entity A", "tax_id": "123"})
    
    # Verify Tenant A can read it
    assert repo_le.get(le_a.id) is not None
    assert len(repo_le.get_all()) == 1

    # 3. Switch context to Tenant B
    set_current_tenant_id(tenant_b_id)
    repo_le_b = BaseRepository(LegalEntity, db_session)
    
    # Verify Tenant B CANNOT read Tenant A's Legal Entity
    assert repo_le_b.get(le_a.id) is None
    assert len(repo_le_b.get_all()) == 0

    # Verify Tenant B CANNOT update Tenant A's Legal Entity
    with pytest.raises(ValueError, match="Cannot update record belonging to another tenant"):
        repo_le_b.update(le_a, {"name": "Hacked Entity"})

def test_missing_tenant_context_blocks_creation(db_session):
    # Clear tenant context
    set_current_tenant_id(None)
    repo_le = BaseRepository(LegalEntity, db_session)
    
    with pytest.raises(ValueError, match="Tenant context is required for creation"):
        repo_le.create({"name": "Orphan Entity"})

def test_missing_tenant_context_blocks_reads(db_session):
    # Clear tenant context
    set_current_tenant_id(None)
    repo_le = BaseRepository(LegalEntity, db_session)
    
    with pytest.raises(ValueError, match="Tenant context is required for this operation"):
        repo_le.get_all()
