import pytest
from httpx import AsyncClient

def test_get_currencies(client, auth_headers, db_session):
    from app.models.org_settings import Currency
    if not db_session.query(Currency).filter_by(code="USD").first():
        db_session.add_all([
            Currency(code="USD", name="US Dollar", symbol="$"),
            Currency(code="EGP", name="Egyptian Pound", symbol="E£")
        ])
        db_session.commit()

    response = client.get("/api/v1/settings/currencies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    codes = [c["code"] for c in data]
    assert "USD" in codes
    assert "EGP" in codes

def test_get_tenant_settings(client, auth_headers, admin_user, db_session, test_tenant):
    from app.models.org_settings import TenantSettings, Currency
    # Create currency and tenant settings
    if not db_session.query(Currency).filter_by(code="USD").first():
        db_session.add(Currency(code="USD", name="US Dollar", symbol="$"))
    db_session.add(TenantSettings(
        tenant_id=test_tenant.id,
        base_currency_code="USD",
        default_locale="en-US",
        default_timezone="UTC"
    ))
    db_session.commit()

    # The default tenant seeded has some settings
    response = client.get("/api/v1/settings/tenant", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["base_currency_code"] == "USD"
    assert data["default_locale"] == "en-US"

def test_update_tenant_settings(client, auth_headers, db_session, test_tenant):
    from app.models.org_settings import TenantSettings, Currency
    if not db_session.query(Currency).filter_by(code="USD").first():
        db_session.add(Currency(code="USD", name="US Dollar", symbol="$"))
    if not db_session.query(TenantSettings).filter_by(tenant_id=test_tenant.id).first():
        db_session.add(TenantSettings(tenant_id=test_tenant.id, base_currency_code="USD"))
    db_session.commit()

    update_data = {
        "default_locale": "ar-EG",
        "default_timezone": "Africa/Cairo"
    }
    response = client.put("/api/v1/settings/tenant", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["default_locale"] == "ar-EG"
    assert data["default_timezone"] == "Africa/Cairo"
    
    # Re-fetch to ensure persistence
    res2 = client.get("/api/v1/settings/tenant", headers=auth_headers)
    assert res2.json()["default_locale"] == "ar-EG"

def test_get_fiscal_years(client, auth_headers, db_session, test_tenant):
    from app.models.org_settings import FiscalYear
    import datetime
    db_session.add(FiscalYear(
        tenant_id=test_tenant.id,
        name="FY-2026",
        start_date=datetime.date(2026, 1, 1),
        end_date=datetime.date(2026, 12, 31)
    ))
    db_session.commit()

    response = client.get("/api/v1/settings/fiscal-years", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["name"] == "FY-2026"
