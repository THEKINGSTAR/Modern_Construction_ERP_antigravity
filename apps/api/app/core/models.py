import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import declarative_mixin, declared_attr
from app.core.context import get_current_tenant_id

@declarative_mixin
class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

@declarative_mixin
class AuditMixin:
    created_by = Column(Uuid(as_uuid=True), nullable=True)
    updated_by = Column(Uuid(as_uuid=True), nullable=True)

@declarative_mixin
class TenantAwareMixin(TimestampMixin, AuditMixin):
    @declared_attr
    def tenant_id(cls):
        return Column(Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True, default=get_current_tenant_id)
