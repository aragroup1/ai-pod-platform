from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import time

from app.config import settings
from app.database import engine, Base, get_db, db_pool
from app.api.v1 import (
    trends, products, artwork, platforms, 
    orders, analytics
)
from app.api.v1.dashboard import providers as dashboard_providers
from app.utils.cache import redis_client

logger.add(
    "logs/app.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting AI POD Platform...")
    
    # Initialize database
    await db_pool.initialize()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize Redis
    await redis_client.initialize()
    
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await db_pool.close()
    await redis_client.close()
    await engine.dispose()
    logger.info("Application shutdown complete")

app = FastAPI(
    title="AI POD Platform",
    description="AI-Powered Print-on-Demand Platform",
    version="1.0.0",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.railway.app", settings.DOMAIN]
    )

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Health check
@app.get("/health")
async def health_check():
    try:
        # Check database
        await db_pool.fetchval("SELECT 1")
        db_status = "healthy"
    except:
        db_status = "unhealthy"
    
    try:
        # Check Redis
        await redis_client.ping()
        redis_status = "healthy"
    except:
        redis_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded",
        "database": db_status,
        "redis": redis_status,
        "version": "1.0.0"
    }

# Root
@app.get("/")
async def root():
    return {
        "message": "AI POD Platform API",
        "version": "1.0.0",
        "docs": "/api/docs" if settings.DEBUG else None
    }

# Include routers
app.include_router(trends.router, prefix=f"{settings.API_V1_PREFIX}/trends", tags=["Trends"])
app.include_router(products.router, prefix=f"{settings.API_V1_PREFIX}/products", tags=["Products"])
app.include_router(artwork.router, prefix=f"{settings.API_V1_PREFIX}/artwork", tags=["Artwork"])
app.include_router(platforms.router, prefix=f"{settings.API_V1_PREFIX}/platforms", tags=["Platforms"])
app.include_router(orders.router, prefix=f"{settings.API_V1_PREFIX}/orders", tags=["Orders"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_PREFIX}/analytics", tags=["Analytics"])
app.include_router(dashboard_providers.router, prefix=f"{settings.API_V1_PREFIX}/dashboard", tags=["Dashboard"])

# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
