import time
import uuid
import logging
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.config import settings

logger = logging.getLogger("logiagent")

class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """
    Assigns a unique correlation Request ID to every incoming HTTP request.
    Appends the 'X-Request-ID' header to the response.
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        req_id = request.headers.get("X-Request-ID")
        if not req_id:
            req_id = f"req-{uuid.uuid4().hex[:12]}"
        request.state.request_id = req_id
        
        start_time = time.time()
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Response-Time-Ms"] = str(duration_ms)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Enforces enterprise HTTP security headers across all API responses.
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Standard security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Permissions-Policy"] = "geolocation=(self), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' ws: wss: http: https:;"
        
        # HSTS in production
        if settings.ENVIRONMENT.lower() == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            
        return response


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs API requests with response code, processing duration, and correlation ID.
    Sanitizes against logging sensitive query params and tokens.
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Don't log health probes repeatedly to avoid noise
        path = request.url.path
        is_health = path in ["/health", "/health/live", "/health/ready", "/"]
        
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        req_id = getattr(request.state, "request_id", "req-unknown")
        
        try:
            response = await call_next(request)
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            if not is_health:
                logger.info(
                    f"[{req_id}] {request.method} {path} -> {response.status_code} ({duration_ms}ms) [IP: {client_ip}]"
                )
            return response
        except Exception as exc:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                f"[{req_id}] {request.method} {path} -> 500 Unhandled Exception ({duration_ms}ms) [IP: {client_ip}]: {exc}",
                exc_info=True
            )
            raise
