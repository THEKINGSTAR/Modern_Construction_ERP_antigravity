from typing import TypeVar, Generic, Type, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.context import get_current_tenant_id
from app.core.models import TenantAwareMixin

ModelType = TypeVar("ModelType", bound=TenantAwareMixin)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def _apply_tenant_filter(self, query):
        tenant_id = get_current_tenant_id()
        if not tenant_id:
            raise ValueError("Tenant context is required for this operation")
        return query.where(self.model.tenant_id == tenant_id)

    def get(self, id: UUID) -> ModelType | None:
        query = select(self.model).where(self.model.id == id)
        query = self._apply_tenant_filter(query)
        return self.db.scalars(query).first()

    def get_all(self) -> list[ModelType]:
        query = select(self.model)
        query = self._apply_tenant_filter(query)
        return list(self.db.scalars(query).all())

    def create(self, obj_in: dict[str, Any]) -> ModelType:
        tenant_id = get_current_tenant_id()
        if not tenant_id:
            raise ValueError("Tenant context is required for creation")
        
        db_obj = self.model(**obj_in)
        db_obj.tenant_id = tenant_id  # explicitly enforce
        
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: ModelType, obj_in: dict[str, Any]) -> ModelType:
        tenant_id = get_current_tenant_id()
        if db_obj.tenant_id != tenant_id:
            raise ValueError("Cannot update record belonging to another tenant")

        for field, value in obj_in.items():
            setattr(db_obj, field, value)
            
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: UUID) -> bool:
        obj = self.get(id)
        if not obj:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True
