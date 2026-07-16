import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    PG_DSN: str = os.getenv("PG_DSN", "postgresql://user:pass@localhost:5432/appsec_db")
    
    # Redis & Queue
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    SCAN_JOBS_QUEUE: str = "scan_jobs"
    AI_ANALYSIS_QUEUE_NAME: str = "ai_analysis_queue"
    
    # AI & VectorDB
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    COLLECTION_NAME: str = "code_chunks"
    
    # Storage
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "admin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "password123")
    MINIO_SECURE: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
