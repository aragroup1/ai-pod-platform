from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
from app.routers import admin_routes
import sys

from app.config import settings
from app.database import db_pool
from app.utils.cache import redis_client
from app.api.v1 import debug  # Add this to your imports
from app.api.v1 import shopify


# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("🚀 Starting AI POD Platform...")
    
    # Initialize database pool
    try:
        await db_pool.initialize()
        logger.info("✅ Database pool initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise
    
    # Initialize Redis (optional)
    try:
        await redis_client.initialize()
        if redis_client.is_connected:
            logger.info("✅ Redis connected")
        else:
            logger.warning("⚠️ Redis not available (caching disabled)")
    except Exception as e:
        logger.warning(f"⚠️ Redis initialization failed: {e}")
    
    logger.info("✅ Application started successfully!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    await db_pool.close()
    await redis_client.close()
    logger.info("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="AI POD Platform API",
    description="AI-Powered Print-on-Demand Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_origin_regex=r"https://.*\.up\.railway\.app",  # ✅ This works!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": db_pool.pool is not None,
        "redis": redis_client.is_connected
    }

@app.get("/")
async def root():
    return {
        "message": "AI POD Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Import routers
from app.api.v1 import (
    test, products, orders, trends, platforms, artwork,
    analytics, analytics_detailed, generation, approval,
    product_feedback, keyword_research, admin
)

# Include routers
logger.info("📋 Registering API routes...")
app.include_router(shopify.router, prefix=f"{settings.API_V1_PREFIX}/shopify", tags=["Shopify"])
app.include_router(test.router, prefix=f"{settings.API_V1_PREFIX}/test", tags=["Test"])
app.include_router(products.router, prefix=f"{settings.API_V1_PREFIX}/products", tags=["Products"])
app.include_router(orders.router, prefix=f"{settings.API_V1_PREFIX}/orders", tags=["Orders"])
app.include_router(trends.router, prefix=f"{settings.API_V1_PREFIX}/trends", tags=["Trends"])
app.include_router(platforms.router, prefix=f"{settings.API_V1_PREFIX}/platforms", tags=["Platforms"])
app.include_router(artwork.router, prefix=f"{settings.API_V1_PREFIX}/artwork", tags=["Artwork"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_PREFIX}/analytics", tags=["Analytics"])
app.include_router(analytics_detailed.router, prefix=f"{settings.API_V1_PREFIX}/analytics-detailed", tags=["Analytics Detailed"])
app.include_router(generation.router, prefix=f"{settings.API_V1_PREFIX}/generation", tags=["Generation"])
app.include_router(approval.router, prefix=f"{settings.API_V1_PREFIX}/approval", tags=["Approval"])
app.include_router(product_feedback.router, prefix=f"{settings.API_V1_PREFIX}/product-feedback", tags=["Feedback"])
app.include_router(keyword_research.router, prefix=f"{settings.API_V1_PREFIX}/keyword-research", tags=["Keywords"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(debug.router, prefix=f"{settings.API_V1_PREFIX}/debug", tags=["Debug"])
app.include_router(admin_routes.router, prefix="/api/v1/admin", tags=["Admin"])
logger.info("✅ All routes registered")
