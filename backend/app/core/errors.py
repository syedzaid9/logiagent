import logging
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.config import settings

logger = logging.getLogger("logiagent")

def get_error_code(status_code: int) -> str:
    codes = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "RESOURCE_NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT"
    }
    return codes.get(status_code, "API_ERROR")

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    req_id = getattr(request.state, "request_id", "req-unknown")
    err_code = get_error_code(exc.status_code)
    
    # Detail can be a string or structured dict/list
    msg = str(exc.detail) if not isinstance(exc.detail, (dict, list)) else "Request error occurred"
    details = exc.detail if isinstance(exc.detail, (dict, list)) else []
    
    body = {
        "error": {
            "code": err_code,
            "message": msg,
            "request_id": req_id,
            "details": details
        },
        "detail": msg  # Backwards compatibility for existing clients
    }
    
    headers = getattr(exc, "headers", None) or {}
    headers["X-Request-ID"] = req_id
    
    return JSONResponse(
        status_code=exc.status_code,
        content=body,
        headers=headers
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    req_id = getattr(request.state, "request_id", "req-unknown")
    
    # Clean up validation errors for readability
    formatted_errors = []
    for err in exc.errors():
        loc = " -> ".join([str(l) for l in err.get("loc", [])])
        formatted_errors.append({
            "field": loc,
            "message": err.get("msg", "Invalid value"),
            "type": err.get("type", "value_error")
        })
        
    summary_msg = f"Validation failed for {len(formatted_errors)} field(s)."
    
    body = {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": summary_msg,
            "request_id": req_id,
            "details": formatted_errors
        },
        "detail": formatted_errors  # FastAPI convention
    }
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=body,
        headers={"X-Request-ID": req_id}
    )

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    req_id = getattr(request.state, "request_id", "req-unknown")
    logger.error(f"[{req_id}] Unhandled Server Error on {request.method} {request.url.path}: {exc}", exc_info=True)
    
    safe_message = "An internal server error occurred. Please contact system support."
    if settings.ENVIRONMENT.lower() == "development":
        safe_message = f"Internal Server Error: {str(exc)}"
        
    body = {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": safe_message,
            "request_id": req_id,
            "details": []
        },
        "detail": safe_message
    }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=body,
        headers={"X-Request-ID": req_id}
    )

def register_error_handlers(app):
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

