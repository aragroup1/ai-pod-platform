"""
Database connection and pool management using asyncpg
"""
import asyncpg
from loguru import logger
from typing import Optional
from app.config import settings


class DatabasePool:
    """Manages asyncpg connection pool"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self):
        """Initialize the database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                dsn=settings.DATABASE_URL,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("Database pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close(self):
        """Close the database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")


# Global database pool instance
db_pool = DatabasePool()


async def get_db_pool() -> asyncpg.Pool:
    """
    Dependency function to get the database pool.
    Used in FastAPI dependency injection.
    """
    if not db_pool.pool:
        raise RuntimeError("Database pool not initialized")
    return db_pool.pool
