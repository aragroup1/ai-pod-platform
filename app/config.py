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
    
    # AI Generation APIs
    REPLICATE_API_TOKEN: Optional[str] = None
    LEONARDO_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    IDEOGRAM_API_KEY: Optional[str] = None
    STABILITY_API_KEY: Optional[str] = None
    
    # Google Ads / Keyword Planner
    GOOGLE_ADS_DEVELOPER_TOKEN: Optional[str] = None
    GOOGLE_ADS_CLIENT_ID: Optional[str] = None
    GOOGLE_ADS_CLIENT_SECRET: Optional[str] = None
    GOOGLE_ADS_REFRESH_TOKEN: Optional[str] = None
    GOOGLE_ADS_CUSTOMER_ID: Optional[str] = None
    GOOGLE_ADS_LOGIN_CUSTOMER_ID: Optional[str] = None
    
    # Trend Analysis
    SERPAPI_KEY: Optional[str] = None
    GOOGLE_TRENDS_API_KEY: Optional[str] = None
    
    # POD Providers
    PRINTFUL_API_TOKEN: Optional[str] = None
    PRINTIFY_API_TOKEN: Optional[str] = None
    
    # E-commerce Platforms
    SHOPIFY_API_KEY: Optional[str] = None
    SHOPIFY_API_SECRET: Optional[str] = None
    SHOPIFY_ACCESS_TOKEN: Optional[str] = None
    SHOPIFY_SHOP_DOMAIN: Optional[str] = None
    
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
