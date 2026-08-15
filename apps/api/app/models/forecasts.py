import uuid
import enum
from sqlalchemy import Column, String, Date, Numeric, ForeignKey, Enum, Uuid, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.models import TenantAwareMixin, TimestampMixin, AuditMixin

class ForecastStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    SUPERSEDED = "SUPERSEDED"

class ProjectForecast(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "project_forecasts"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    forecast_number = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(Enum(ForecastStatus, native_enum=False), default=ForecastStatus.DRAFT, nullable=False)
    notes = Column(Text, nullable=True)

    project = relationship("Project")
    lines = relationship("ProjectForecastLine", back_populates="forecast", cascade="all, delete-orphan")


class ProjectForecastLine(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "project_forecast_lines"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    forecast_id = Column(Uuid(as_uuid=True), ForeignKey("project_forecasts.id", ondelete="CASCADE"), nullable=False, index=True)
    cost_code_id = Column(Uuid(as_uuid=True), ForeignKey("cost_codes.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # Estimate To Complete (ETC)
    etc_amount = Column(Numeric(18, 4), nullable=False, default=0)
    notes = Column(Text, nullable=True)

    forecast = relationship("ProjectForecast", back_populates="lines")
    cost_code = relationship("CostCode")
