import os
import sys
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from app.api.v1 import trends, products, artwork, platforms, orders, analytics, test
from app.api.v1.dashboard import providers as dashboard_providers
# --- Step 1: Configure Logging Immediately ---
# This ensures we capture logs from the very start.
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
logger.add("logs/app.log", rotation="10 MB", retention="7 days", level="INFO")

logger.info("Application starting up...")


# --- Step 2: Lifespan Manager for Heavy Lifting ---
# All connections and complex initializations happen here, after the app is running.
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Executing lifespan startup...")
    
    # Delayed imports to prevent crashing on startup if a module has an issue
    from app.config import settings
    from app.database import db_pool
    from app.utils.cache import redis_client

    # Initialize Database Pool
    app.state.db_pool = db_pool
    try:
        await app.state.db_pool.initialize()
        if app.state.db_pool.is_connected:
            logger.info("Database pool connected successfully.")
        else:
            logger.warning("Database initialization ran but failed to connect (check DATABASE_URL).")
    except Exception as e:
        logger.error(f"A critical error occurred during database initialization: {e}")
        app.state.db_pool.is_connected = False

    # Initialize Redis Client
    app.state.redis_client = redis_client
    try:
        await app.state.redis_client.initialize()
        if app.state.redis_client.is_connected:
            logger.info("Redis client connected successfully.")
        else:
            logger.warning("Redis initialization ran but failed to connect (check REDIS_URL).")
    except Exception as e:
        logger.error(f"A critical error occurred during Redis initialization: {e}")
        app.state.redis_client.is_connected = False

    # Load and register API routers here
    try:
        from app.api.v1 import trends, products, artwork, platforms, orders, analytics
        from app.api.v1.dashboard import providers as dashboard_providers
        
        app.include_router(trends.router, prefix=f"{settings.API_V1_PREFIX}/trends", tags=["Trends"])
        app.include_router(products.router, prefix=f"{settings.API_V1_PREFIX}/products", tags=["Products"])
        app.include_router(artwork.router, prefix=f"{settings.API_V1_PREFIX}/artwork", tags=["Artwork"])
        app.include_router(platforms.router, prefix=f"{settings.API_V1_PREFIX}/platforms", tags=["Platforms"])
        app.include_router(orders.router, prefix=f"{settings.API_V1_PREFIX}/orders", tags=["Orders"])
        app.include_router(test.router, prefix=f"{settings.API_V1_PREFIX}/test", tags=["Test"])
```

## Deployment Steps:

1. **Push all these fixed files to your repository**

2. **In Railway, for your backend service, set this environment variable temporarily:**
```
   SEED_DATA=true
        app.include_router(analytics.router, prefix=f"{settings.API_V1_PREFIX}/analytics", tags=["Analytics"])
        app.include_router(dashboard_providers.router, prefix=f"{settings.API_V1_PREFIX}/dashboard", tags=["Dashboard"])
        logger.info("All API routers have been included.")
    except Exception as e:
        logger.error(f"Failed to include some routers: {e}")
        # This will prevent some routes from working but won't crash the startup

    logger.info("Lifespan startup complete. Application is ready.")
    yield
    
    # Shutdown logic
    logger.info("Executing lifespan shutdown...")
    if hasattr(app.state, 'db_pool') and app.state.db_pool and app.state.db_pool.is_connected:
        await app.state.db_pool.close()
        logger.info("Database pool closed.")
    if hasattr(app.state, 'redis_client') and app.state.redis_client and app.state.redis_client.is_connected:
        await app.state.redis_client.close()
        logger.info("Redis client closed.")
    logger.info("Lifespan shutdown complete.")


# --- Step 3: Create the FastAPI App and Assign Lifespan ---
app = FastAPI(
    title="AI POD Platform",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)


# --- Step 4: Add Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your frontend domain
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


# --- Step 5: Define a Minimal, Dependency-Free Health Check ---
# This endpoint MUST work for Railway to consider the deployment healthy.
@app.get("/health", tags=["Health"])
async def health_check():
    # This simple check is enough for Railway. The lifespan logs will tell us about services.
    return {"status": "healthy", "version": "1.0.0"}


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
