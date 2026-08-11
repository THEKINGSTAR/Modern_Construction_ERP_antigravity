from contextvars import ContextVar
import uuid

# Context variables to store request-scoped data
tenant_context: ContextVar[uuid.UUID | None] = ContextVar("tenant_context", default=None)
user_context: ContextVar[uuid.UUID | None] = ContextVar("user_context", default=None)

def get_current_tenant_id() -> uuid.UUID | None:
    return tenant_context.get()

def set_current_tenant_id(tenant_id: uuid.UUID | str | None) -> None:
    if isinstance(tenant_id, str):
        tenant_id = uuid.UUID(tenant_id)
    tenant_context.set(tenant_id)
