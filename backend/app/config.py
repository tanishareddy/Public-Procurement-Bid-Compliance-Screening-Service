import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "Public Procurement Bid Compliance Screening Service"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/app.db"
    SYNC_DATABASE_URL: str = "sqlite:///./data/app.db"
    
    # Redis & Task Execution
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    ASYNC_MODE: str = "direct"  # "celery" or "direct" (for lightweight dev/test without Redis)
    
    # Vector DB & Embeddings
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma_db"
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    DEVICE: str = "cpu"
    
    # LLM Settings
    LLM_PROVIDER: str = "stub" # "stub", "google_genai", "openai"
    GOOGLE_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL_NAME: str = "gemini-1.5-flash"
    LLM_TEMPERATURE: float = 0.0
    LLM_REQUEST_TIMEOUT_SECONDS: float = 20.0
    
    # Rate Limiting & Circuit Breaker
    RATE_LIMIT_PER_MINUTE: int = 60
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 30
    
    # Observability
    ENABLE_METRICS: bool = True
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"
    OTEL_SERVICE_NAME: str = "bid-compliance-screening"
    
    # Prompt Versioning
    CURRENT_PROMPT_VERSION: str = "v2"

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
