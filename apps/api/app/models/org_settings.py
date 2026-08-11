import uuid
from sqlalchemy import Column, String, Boolean, Date, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.core.models import TenantAwareMixin, TimestampMixin

class Currency(Base, TimestampMixin):
    __tablename__ = "currencies"
    
    code = Column(String(3), primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    symbol = Column(String(10), nullable=False)

class ExchangeRate(Base, TenantAwareMixin, TimestampMixin):
    __tablename__ = "exchange_rates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_currency_code = Column(String(3), ForeignKey("currencies.code"), nullable=False)
    to_currency_code = Column(String(3), ForeignKey("currencies.code"), nullable=False)
    rate = Column(Numeric(18, 6), nullable=False)
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime, nullable=True)

class FiscalYear(Base, TenantAwareMixin, TimestampMixin):
    __tablename__ = "fiscal_years"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_closed = Column(Boolean, default=False, nullable=False)
    
    periods = relationship("AccountingPeriod", back_populates="fiscal_year", cascade="all, delete-orphan")

class AccountingPeriod(Base, TenantAwareMixin, TimestampMixin):
    __tablename__ = "accounting_periods"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fiscal_year_id = Column(UUID(as_uuid=True), ForeignKey("fiscal_years.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_closed = Column(Boolean, default=False, nullable=False)
    
    fiscal_year = relationship("FiscalYear", back_populates="periods")

class TenantSettings(Base, TenantAwareMixin, TimestampMixin):
    __tablename__ = "tenant_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    base_currency_code = Column(String(3), ForeignKey("currencies.code"), nullable=False)
    default_locale = Column(String(20), default="en-US", nullable=False)
    default_timezone = Column(String(50), default="UTC", nullable=False)
    default_date_format = Column(String(20), default="YYYY-MM-DD", nullable=False)
    default_number_format = Column(String(20), default="#,##0.00", nullable=False)
