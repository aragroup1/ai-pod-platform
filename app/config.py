from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache
import os

class Settings(BaseSettings):
    # CRITICAL: These must be set in production
    SECRET_KEY: str = "change-this-in-production-a-very-long-secret-key"
    ENCRYPTION_KEY: str = "change-this-in-production-a-32-byte-long-key"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    DOMAIN: str = "localhost"
    
    # Database (Railway will set this)
    DATABASE_URL: str = ""
    
    # Redis (Railway will set this)
    REDIS_URL: str = ""
    
    # Celery
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""
    
    # Optional API Keys
    REPLICATE_API_TOKEN: Optional[str] = None
    LEONARDO_API_KEY: Optional[str] = None
    # ... add other optional keys here ...
    
    # Storage
    CLOUDFLARE_R2_ACCESS_KEY: Optional[str] = None
    CLOUDFLARE_R2_SECRET_KEY: Optional[str] = None
    CLOUDFLARE_R2_BUCKET: str = "pod-assets"
    CLOUDFLARE_R2_ENDPOINT: Optional[str] = None
    CLOUDFLARE_R2_PUBLIC_URL: Optional[str] = None

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
