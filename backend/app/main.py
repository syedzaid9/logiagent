import sys
from pathlib import Path

# Ensure backend root is in sys.path when executed directly
_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import setup_logging, logger
from app.core.database import Base, engine, SessionLocal
from app.core.middleware import (
    RequestCorrelationMiddleware,
    SecurityHeadersMiddleware,
    StructuredLoggingMiddleware
)
from app.core.errors import register_error_handlers
from app.api.deps import get_db
from app.models.user import User
from app.data.seed_data import seed_database
from app.rag import initialize_rag
from app.api.v1 import api_v1_router

setup_logging()

def ensure_schema_compatibility():
    """Ensures database schema backwards compatibility across SQLite and PostgreSQL."""
    try:
        from sqlalchemy import inspect
        Base.metadata.create_all(bind=engine)
        inspector = inspect(engine)
        if "users" in inspector.get_table_names():
            cols = [c["name"] for c in inspector.get_columns("users")]
            with engine.begin() as conn:
                if "reset_password_token" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN reset_password_token VARCHAR(255);"))
                if "reset_password_expires_at" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN reset_password_expires_at TIMESTAMP;"))
    except Exception as e:
        logger.warning(f"Schema check notice: {e}")

ensure_schema_compatibility()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up LogiAgent Backend Server (Production Hardened)...")
    ensure_schema_compatibility()
    
    # Check if DB has data, otherwise seed
    db = SessionLocal()
    try:
        if not db.query(User).first():
            logger.info("Fresh database detected. Seeding realistic dataset...")
            seed_database(force_recreate=False)
        else:
            # Still make sure RAG is loaded
            initialize_rag()
    finally:
        db.close()
        
    logger.info(f"LogiAgent API v{settings.VERSION} ready [{settings.ENVIRONMENT}].")
    yield
    logger.info("Shutting down LogiAgent Backend Server...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise AI Logistics Operations Platform powered by LangGraph, Tool Calling, and RAG.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 1. Custom Security & Observability Middlewares (Applied in reverse execution order)
app.add_middleware(StructuredLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestCorrelationMiddleware)

# 2. CORS Middleware with environment-scoped origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)

# 3. Register Standardized Error Handlers
register_error_handlers(app)

# 4. Mount API Routers
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

# 5. Root & Health Check Endpoints
@app.get("/", tags=["Health"])
def root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "online",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR
    }

@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "llm_provider": settings.LLM_PROVIDER
    }

@app.get("/health/live", tags=["Health"])
def health_liveness():
    """Liveness probe to confirm the server process is responsive."""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/health/ready", tags=["Health"])
def health_readiness(db: Session = Depends(get_db)):
    """Readiness probe to verify database and service dependencies are ready."""
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected",
            "environment": settings.ENVIRONMENT,
            "version": settings.VERSION,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as exc:
        logger.error(f"Readiness check failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service dependencies unavailable"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
