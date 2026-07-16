import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database Configuration
    PG_DSN: str = os.getenv("PG_DSN", "postgresql://user:pass@postgres:5432/appsec_db")
    
    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    INGEST_QUEUE_NAME: str = "vulnerability_ingest"
    AI_ANALYSIS_QUEUE_NAME: str = "ai_analysis_queue"
    
    # Storage Configuration
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    
    # Service Configuration
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://ollama:11434")
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://qdrant:6333")

settings = Settings()
