# app/main.py
"""
Main FastAPI application
Matches your existing GitHub repo structure
"""
import os
import sys
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from app.database import db_pool
from app.utils.cache import cache_client


# Import settings at top level (as in your repo)
from app.config import settings

# Configure logging
logger.remove()
logger.add(
    sys.stderr, 
    level="INFO", 
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
logger.add("logs/app.log", rotation="10 MB", retention="7 days", level="INFO")

logger.info("Application starting up...")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager - matches your repo's pattern"""
    logger.info("Executing lifespan startup...")
    
    # Initialize Database Pool
    app.state.db_pool = db_pool
    try:
        await app.state.db_pool.initialize()
        logger.info("✅ Database pool connected successfully.")
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}")
        raise

    # Initialize Redis Client
    app.state.cache_client = cache_client
    try:
        await app.state.cache_client.initialize()
        logger.info("✅ Redis client connected successfully.")
    except Exception as e:
        logger.error(f"❌ Redis initialization error: {e}")
        raise

    # Load and register API routers (matches your existing imports)
    try:
        from app.api.v1 import (
            trends, products, artwork, platforms, 
            orders, analytics, test, generation, 
            keyword_research, product_feedback
        )
        from app.api.v1.dashboard import providers as dashboard_providers
        
        # Register routers (matches your pattern)
        app.include_router(trends.router, prefix=f"{settings.API_V1_PREFIX}/trends", tags=["Trends"])
        app.include_router(products.router, prefix=f"{settings.API_V1_PREFIX}/products", tags=["Products"])
        app.include_router(artwork.router, prefix=f"{settings.API_V1_PREFIX}/artwork", tags=["Artwork"])
        app.include_router(platforms.router, prefix=f"{settings.API_V1_PREFIX}/platforms", tags=["Platforms"])
        app.include_router(orders.router, prefix=f"{settings.API_V1_PREFIX}/orders", tags=["Orders"])
        app.include_router(analytics.router, prefix=f"{settings.API_V1_PREFIX}/analytics", tags=["Analytics"])
        app.include_router(test.router, prefix=f"{settings.API_V1_PREFIX}/test", tags=["Test"])
        app.include_router(generation.router, prefix=f"{settings.API_V1_PREFIX}/generation", tags=["Generation"])
        app.include_router(keyword_research.router, prefix=f"{settings.API_V1_PREFIX}/keyword-research", tags=["Keyword Research"])
        app.include_router(product_feedback.router, prefix=f"{settings.API_V1_PREFIX}/product-feedback", tags=["Product Feedback"])
        app.include_router(dashboard_providers.router, prefix=f"{settings.API_V1_PREFIX}/dashboard", tags=["Dashboard"])

        logger.info("✅ All API routers loaded successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to load routers: {e}")
        logger.exception("Full traceback:")
        raise

    logger.info("🚀 Lifespan startup complete. Application is ready!")
    yield
    
    # Shutdown logic
    logger.info("Shutting down...")
    if hasattr(app.state, 'db_pool') and app.state.db_pool:
        await app.state.db_pool.close()
        logger.info("Database pool closed.")
    if hasattr(app.state, 'cache_client') and app.state.cache_client:
        await app.state.cache_client.close()
        logger.info("Cache client closed.")
    logger.info("✅ Shutdown complete.")


# Create FastAPI app (matches your pattern)
app = FastAPI(
    title="AI POD Platform",
    description="AI-Powered Print-on-Demand Platform with Google Trends Integration",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)


# Add Middleware (matches your pattern)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"Request: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.4f}s")
    return response


# Health Check (matches your pattern)
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}


# Root Endpoint (matches your pattern)
@app.get("/")
def read_root():
    """Root endpoint with API info"""
    return {
        "message": "Welcome to the AI POD Platform",
        "version": "1.0.0",
        "docs": "/api/docs"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.exception(f"Unhandled error for {request.method} {request.url}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."},
    )
