import uuid
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
import redis

from app.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import BaseAPIException, api_exception_handler
from app.core.database import SessionLocal
from app.core.context import set_current_tenant_id

setup_logging(settings.ENVIRONMENT)

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

app.add_exception_handler(BaseAPIException, api_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def tenant_context_middleware(request: Request, call_next):
    tenant_id = request.headers.get("X-Tenant-ID")
    if tenant_id:
        set_current_tenant_id(tenant_id)
    else:
        set_current_tenant_id(None)
    response = await call_next(request)
    return response

@app.middleware("http")
async def add_request_id_and_timing(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

@app.get("/health/live", tags=["Health"])
def health_live():
    return {"status": "ok"}

@app.get("/health/ready", tags=["Health"])
def health_ready():
    db_status = "ok"
    redis_status = "ok"
    
    # Check DB
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception:
        db_status = "error"
        
    # Check Redis
    try:
        r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        r.ping()
    except Exception:
        redis_status = "error"
        
    status = "ok" if db_status == "ok" and redis_status == "ok" else "error"
    status_code = 200 if status == "ok" else 503
    
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status_code, 
        content={"status": status, "components": {"database": db_status, "redis": redis_status}}
    )

@app.get("/api/v1/health", tags=["Health"])
def api_health():
    return {"status": "ok", "version": settings.VERSION}
