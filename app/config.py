from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache

class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str
    ENCRYPTION_KEY: str
    API_V1_PREFIX: str = "/api/v1"
    DOMAIN: str = "localhost"
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    DATABASE_POOL_TIMEOUT: int = 30
    
    # Redis
    REDIS_URL: str
    REDIS_CACHE_TTL: int = 300
    
    # AI APIs
    REPLICATE_API_TOKEN: Optional[str] = None
    LEONARDO_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    IDEOGRAM_API_KEY: Optional[str] = None
    STABILITY_API_KEY: Optional[str] = None
    
    # Costs
    FLUX_COST_PER_IMAGE: float = 0.003
    LEONARDO_COST_PER_IMAGE: float = 0.039
    OPENAI_COST_PER_IMAGE: float = 0.040
    
    # Trend Analysis
    SERPAPI_KEY: Optional[str] = None
    GOOGLE_TRENDS_API_KEY: Optional[str] = None
    
    # POD Providers
    PRINTFUL_API_TOKEN: Optional[str] = None
    PRINTIFY_API_TOKEN: Optional[str] = None
    
    # Platforms
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
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Business Logic
    MIN_TREND_SCORE: float = 0.7
    MAX_PRODUCTS_PER_TREND: int = 50
    DEFAULT_PROFIT_MARGIN: float = 0.35
    MIN_PROFIT_MARGIN: float = 0.25
    MAX_PROFIT_MARGIN: float = 0.50
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
