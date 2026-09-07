import uuid
import enum
from sqlalchemy import Column, String, Text, ForeignKey, Enum, Uuid
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.models import TenantAwareMixin

class WarehouseType(str, enum.Enum):
    CENTRAL = "CENTRAL"
    PROJECT = "PROJECT"
    TRANSIT = "TRANSIT"
    VIRTUAL = "VIRTUAL"

class Warehouse(Base, TenantAwareMixin):
    __tablename__ = "warehouses"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    location = Column(Text, nullable=True)
    type = Column(Enum(WarehouseType), nullable=False, default=WarehouseType.CENTRAL, index=True)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    manager_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    project = relationship("Project", foreign_keys=[project_id], lazy="selectin")

    @property
    def project_name(self) -> str:
        return self.project.name if self.project else "Central / All Projects"
