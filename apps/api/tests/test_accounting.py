import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import date, timedelta
from app.models.accounting import Account, AccountType, Journal, JournalLine, JournalStatus
from app.models.org_settings import FiscalYear, AccountingPeriod
from app.services.accounting import AccountingEngine
from app.schemas.accounting import JournalCreate, JournalLineCreate
from fastapi import HTTPException

def test_accounting_engine_unbalanced_journal(db_session, test_tenant, test_user):
    engine = AccountingEngine(db_session, test_tenant.id, test_user.id)
    
    # Try to create an unbalanced journal schema
    with pytest.raises(ValueError, match="Journal must balance"):
        JournalCreate(
            date=date.today(),
            description="Test Unbalanced",
            lines=[
                JournalLineCreate(account_id=uuid4(), debit=Decimal("100.0000")),
                JournalLineCreate(account_id=uuid4(), credit=Decimal("90.0000"))
            ]
        )

def test_accounting_engine_closed_period(db_session, test_tenant, test_user):
    # Setup closed period
    fy = FiscalYear(
        tenant_id=test_tenant.id,
        name="2026",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31)
    )
    db_session.add(fy)
    db_session.flush()

    period = AccountingPeriod(
        tenant_id=test_tenant.id,
        fiscal_year_id=fy.id,
        name="Jan 2026",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        is_closed=True
    )
    db_session.add(period)
    db_session.flush()

    engine = AccountingEngine(db_session, test_tenant.id, test_user.id)
    
    # Create journal (draft)
    schema = JournalCreate(
        date=date(2026, 1, 15),
        description="Test Closed Period",
        lines=[
            JournalLineCreate(account_id=uuid4(), debit=Decimal("100.0000")),
            JournalLineCreate(account_id=uuid4(), credit=Decimal("100.0000"))
        ]
    )

    journal = engine.create_journal(schema)

    # Attempt to post
    with pytest.raises(HTTPException) as exc:
        engine.post_journal(journal.id)
    
    assert "is closed" in str(exc.value.detail)

def test_accounting_engine_post_and_reverse(db_session, test_tenant, test_user):
    # Setup open period
    fy = FiscalYear(
        tenant_id=test_tenant.id,
        name="2026",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31)
    )
    db_session.add(fy)
    db_session.flush()

    period = AccountingPeriod(
        tenant_id=test_tenant.id,
        fiscal_year_id=fy.id,
        name="Feb 2026",
        start_date=date(2026, 2, 1),
        end_date=date(2026, 2, 28),
        is_closed=False
    )
    db_session.add(period)
    db_session.flush()

    engine = AccountingEngine(db_session, test_tenant.id, test_user.id)

    schema = JournalCreate(
        date=date(2026, 2, 15),
        description="Test Post and Reverse",
        reference="JE-001",
        lines=[
            JournalLineCreate(account_id=uuid4(), debit=Decimal("500.0000")),
            JournalLineCreate(account_id=uuid4(), credit=Decimal("500.0000"))
        ]
    )

    journal = engine.create_journal(schema, auto_post=True)
    
    assert journal.status == JournalStatus.POSTED
    assert len(journal.lines) == 2

    # Reverse it
    reversal = engine.reverse_journal(journal.id, date(2026, 2, 16), "Reversal of JE-001")
    
    assert journal.status == JournalStatus.REVERSED
    assert journal.reversal_journal_id == reversal.id
    
    assert reversal.status == JournalStatus.POSTED
    assert reversal.reference == f"REV-JE-001"
    
    # Check lines are swapped
    assert len(reversal.lines) == 2
    # The first line originally had debit 500. The reversal should have credit 500.
    orig_line_1 = journal.lines[0]
    rev_line_1 = next(l for l in reversal.lines if l.account_id == orig_line_1.account_id)
    assert rev_line_1.credit == Decimal("500.0000")
    assert rev_line_1.debit == Decimal("0.0000")
