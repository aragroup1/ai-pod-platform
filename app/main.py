// ... (keep the imports at the top)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Executing lifespan startup...")
    
    # Delayed imports
    from app.config import settings
    from app.database import db_pool, DatabasePool # Import the class
    from app.utils.cache import redis_client

    # Initialize Database Pool
    app.state.db_pool = db_pool # Make it available globally
    try:
        await app.state.db_pool.initialize()
        if app.state.db_pool.is_connected:
            logger.info("Database pool connected successfully.")
        else:
            # This handles the case where initialize() runs but fails internally
            logger.warning("Database initialization ran but failed to connect.")
    except Exception as e:
        logger.error(f"A critical error occurred during database initialization: {e}")
        app.state.db_pool.is_connected = False # Ensure state is false

    # Initialize Redis Client
    app.state.redis_client = redis_client # Make it available globally
    try:
        await app.state.redis_client.initialize()
        if app.state.redis_client.is_connected:
            logger.info("Redis client connected successfully.")
        else:
            logger.warning("Redis initialization ran but failed to connect.")
    except Exception as e:
        logger.error(f"A critical error occurred during Redis initialization: {e}")
        app.state.redis_client.is_connected = False # Ensure state is false

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

    logger.info("Lifespan startup complete. Application is ready.")
    yield
    
    # Shutdown logic
    logger.info("Executing lifespan shutdown...")
    if hasattr(app.state, 'db_pool') and app.state.db_pool:
        await app.state.db_pool.close()
        logger.info("Database pool closed.")
    if hasattr(app.state, 'redis_client') and app.state.redis_client:
        await app.state.redis_client.close()
        logger.info("Redis client closed.")
    logger.info("Lifespan shutdown complete.")
