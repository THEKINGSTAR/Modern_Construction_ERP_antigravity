import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
from app.main import app as fastapi_app
from fastapi.testclient import TestClient

# Import models to ensure they are registered with Base.metadata before create_all
import app.models.tenant
import app.models.legal_entity
import app.models.branch
import app.models.user
import app.models.auth
import app.models.materials
import app.models.warehouses
import app.models.inventory
import app.models.goods_receipts
import app.models.material_issues
import app.models.inventory_transfers
import app.models.inventory_adjustments
import app.models.dimensions
import app.models.accounting
import app.models.bank
import app.models.ap_ar

# Use SQLite in-memory for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
            
    fastapi_app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(fastapi_app) as test_client:
        yield test_client

@pytest.fixture
def test_tenant(db_session):
    import uuid
    from app.models.tenant import Tenant
    tenant_id = uuid.uuid4()
    tenant = Tenant(id=tenant_id, name=f"Test Tenant {tenant_id}")
    db_session.add(tenant)
    db_session.commit()
    return tenant

@pytest.fixture
def auth_headers(client, db_session, test_tenant):
    import uuid
    from app.models.user import User
    from app.core.security import get_password_hash, create_access_token
    # Use a unique email per test to avoid reusing the same user across different test tenants
    email = f"admin_{uuid.uuid4()}@example.com"
    user = db_session.query(User).filter_by(email=email).first()
    if not user:
        user = User(
            id=uuid.uuid4(),
            email=email,
            hashed_password=get_password_hash("pw"),
            tenant_id=test_tenant.id,
            is_superuser=True
        )
        db_session.add(user)
        db_session.commit()
    token = create_access_token({"sub": str(user.id)})
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(test_tenant.id)
    }

@pytest.fixture
def test_user(db_session, test_tenant):
    import uuid
    from app.models.user import User
    from app.core.security import get_password_hash
    email = f"test_{uuid.uuid4()}@example.com"
    user = User(
        id=uuid.uuid4(),
        email=email,
        hashed_password=get_password_hash("pw"),
        tenant_id=test_tenant.id,
        is_superuser=True
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def admin_user(db_session, auth_headers):
    pass

