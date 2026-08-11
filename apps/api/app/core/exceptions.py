from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uuid

class APIErrorDetail(BaseModel):
    message: str
    details: dict | None = None
    request_id: str | None = None

class APIError(BaseModel):
    error: APIErrorDetail

class BaseAPIException(Exception):
    def __init__(self, code: str, message: str, details: dict | None = None, status_code: int = 400):
        self.code = code
        self.message = message
        self.details = details
        self.status_code = status_code

async def api_exception_handler(request: Request, exc: BaseAPIException):
    request_id = request.state.request_id if hasattr(request.state, "request_id") else str(uuid.uuid4())
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details, "request_id": request_id}}
    )
