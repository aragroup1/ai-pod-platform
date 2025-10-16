import os
import sys
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

# --- Step 1: Configure Logging Immediately ---
# This ensures we capture logs from the very start.
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
logger.add("logs/app.log", rotation="10 MB", retention="7 days", level="INFO")

logger.info("Application starting up...")

# --- Step 2: Create the FastAPI App ---
# This is lightweight and won't fail.
app = FastAPI(
    title="AI POD Platform",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# --- Step 3: Define a Minimal, Dependency-Free Health Check ---
# This endpoint MUST work for Railway to consider the deployment healthy.
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

# --- Step 4: Add Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"Request: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.4f}s")
    return response


# --- Step 5: Lifespan Manager for Heavy Lifting ---
# All connections and complex initializations happen here, after the app is running.
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Executing lifespan startup...")
    
    # Delayed imports
    from app.config import settings
    from app.database import db_pool
    from app.utils.cache import redis_client

    # Initialize Database Pool
    try:
        await db_pool.initialize()
        app.state.db_pool = db_pool
        logger.info("Database pool connected.")
    except Exception as e:
        logger.error(f"Failed to connect to the database: {e}")
        app.state.db_pool = None

    # Initialize Redis Client
    try:
        await redis_client.initialize()
        app.state.redis_client = redis_client
        logger.info("Redis client connected.")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        app.state.redis_client = None

    # Load and register API routers here
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
        logger.info("All API routers have been included.")
    except Exception as e:
        logger.error(f"Failed to include routers: {e}")
        # This will prevent the app from serving these routes but won't crash the startup

    logger.info("Lifespan startup complete. Application is ready.")
    yield
    
    # Shutdown logic
    logger.info("Executing lifespan shutdown...")
    if app.state.db_pool:
        await app.state.db_pool.close()
        logger.info("Database pool closed.")
    if app.state.redis_client:
        await app.state.redis_client.close()
        logger.info("Redis client closed.")
    logger.info("Lifespan shutdown complete.")

# Assign the lifespan manager to the app
app.router.lifespan_context = lifespan

# --- Step 6: Root Endpoint and Final Handlers ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the AI POD Platform"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"An unhandled error occurred for request {request.method} {request.url}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."},
    )
