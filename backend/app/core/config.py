import os
from typing import List, Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Load .env from root directory or backend directory
_root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))
_backend_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
if os.path.exists(_root_env):
    load_dotenv(_root_env)
if os.path.exists(_backend_env):
    load_dotenv(_backend_env)

class Settings(BaseSettings):
    PROJECT_NAME: str = "LogiAgent — AI Logistics Operations Agent"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment & Security
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = Field(default="logiagent-super-secret-production-jwt-key-2026-secure", validation_alias="JWT_SECRET")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database (Supabase PostgreSQL / SQLite configurable via .env)
    DATABASE_URL: str = Field(
        default="sqlite:///./logiagent.db",
        validation_alias="DATABASE_URL"
    )
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    
    # AI / LLM APIs
    GEMINI_API_KEY: str = Field(default="", validation_alias="GEMINI_API_KEY")
    OPENAI_API_KEY: str = Field(default="", validation_alias="OPENAI_API_KEY")
    LLM_PROVIDER: str = Field(default="auto", validation_alias="LLM_PROVIDER") # auto, gemini, openai, fallback
    
    # RAG & Vector Embeddings
    EMBEDDING_MODEL_TYPE: str = Field(default="local", validation_alias="EMBEDDING_MODEL_TYPE") # local or gemini
    EMBEDDING_MODEL_NAME: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", validation_alias="EMBEDDING_MODEL_NAME")
    EMBEDDING_DIMENSION: int = Field(default=384, validation_alias="EMBEDDING_DIMENSION")

    # External Logistics APIs (Mockable)
    MAPS_API_KEY: str = Field(default="", validation_alias="MAPS_API_KEY")
    TRAFFIC_API_KEY: str = Field(default="", validation_alias="TRAFFIC_API_KEY")
    WEATHER_API_KEY: str = Field(default="", validation_alias="WEATHER_API_KEY")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8000"
    ]
    CORS_ALLOWED_ORIGINS: Optional[str] = Field(default=None, validation_alias="CORS_ALLOWED_ORIGINS")

    # Rate Limiting (Requests per minute per IP / User)
    RATE_LIMIT_ENABLED: bool = Field(default=True, validation_alias="RATE_LIMIT_ENABLED")
    RATE_LIMIT_LOGIN: int = Field(default=60, validation_alias="RATE_LIMIT_LOGIN")
    RATE_LIMIT_REGISTER: int = Field(default=60, validation_alias="RATE_LIMIT_REGISTER")
    RATE_LIMIT_AI: int = Field(default=60, validation_alias="RATE_LIMIT_AI")
    RATE_LIMIT_ROUTE_OPTIMIZE: int = Field(default=60, validation_alias="RATE_LIMIT_ROUTE_OPTIMIZE")
    RATE_LIMIT_DEFAULT: int = Field(default=180, validation_alias="RATE_LIMIT_DEFAULT")

    @property
    def cors_origins(self) -> List[str]:
        if self.CORS_ALLOWED_ORIGINS:
            return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]
        if self.ENVIRONMENT.lower() == "production":
            return [o for o in self.BACKEND_CORS_ORIGINS if o != "*"]
        return self.BACKEND_CORS_ORIGINS + ["*"]

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        case_sensitive=False,
        extra="allow"
    )

settings = Settings()
