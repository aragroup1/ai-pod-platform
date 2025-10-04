from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import os
import sys

# Configure logging immediately
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/app.log", rotation="500 MB", retention="10 days", level="INFO")

# Import settings
try:
    from app.config import settings
    logger.info(f"Settings loaded. Environment: {settings.ENVIRONMENT}")
except Exception as e:
    logger.error(f"Failed to load settings: {e}")
    # Create minimal settings for startup
    class Settings:
        ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        DEBUG = os.getenv("DEBUG", "false").lower() == "true"
        API_V1_PREFIX = "/api/v1"
        DATABASE_URL = os.getenv("DATABASE_URL", "")
        REDIS_URL = os.getenv("REDIS_URL", "")
        CORS_ORIGINS = ["*"]
        DOMAIN = "localhost"
    settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with graceful degradation"""
    logger.info("Starting AI POD Platform...")
    
    # Try to initialize database
    try:
        from app.database import db_pool
        await db_pool.initialize()
        app.state.db_available = True
        logger.info("Database connected successfully")
    except Exception as e:
        logger.warning(f"Database connection failed: {e}")
        app.state.db_available = False
    
    # Try to initialize Redis
    try:
        from app.utils.cache import redis_client
        await redis_client.initialize()
        await redis_client.ping()
        app.state.redis_available = True
        logger.info("Redis connected successfully")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
        app.state.redis_available = False
    
    logger.info("Application started (some services may be degraded)")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    if app.state.db_available:
        try:
            from app.database import db_pool
            await db_pool.close()
        except:
            pass
    
    if app.state.redis_available:
        try:
            from app.utils.cache import redis_client
            await redis_client.close()
        except:
            pass
    
    logger.info("Application shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="AI POD Platform",
    description="AI-Powered Print-on-Demand Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Store service states
app.state.db_available = False
app.state.redis_available = False

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint - MUST work even if services are down
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "database": "healthy" if app.state.db_available else "unavailable",
            "redis": "healthy" if app.state.redis_available else "unavailable"
        },
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI POD Platform API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }

# Simple test endpoint
@app.get("/api/v1/test")
async def test():
    """Test endpoint"""
    return {"message": "API is working"}

# Import and register routers with error handling
try:
    from app.api.v1 import trends, products, artwork, platforms, orders, analytics
    from app.api.v1.dashboard import providers as dashboard_providers
    
    app.include_router(trends.router, prefix=f"{settings.API_V1_PREFIX}/trends", tags=["Trends"])
    app.include_router(products.router, prefix=f"{settings.API_V1_PREFIX}/products", tags=["Products"])
    app.include_router(artwork.router, prefix=f"{settings.API_V1_PREFIX}/artwork", tags=["Artwork"])
    app.include_router(platforms.router, prefix=f"{settings.API_V1_PREFIX}/platforms", tags=["Platforms"])
    app.include_router(orders.router, prefix=f"{settings.API_V1_PREFIX}/orders", tags=["Orders"])
    app.include_router(analytics.router, prefix=f"{settings.API_V1_PREFIX}/analytics", tags=["Analytics"])
    app.include_router(dashboard_providers.router, prefix=f"{settings.API_V1_PREFIX}/dashboard", tags=["Dashboard"])
    logger.info("All routers registered successfully")
except Exception as e:
    logger.error(f"Failed to register some routers: {e}")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
