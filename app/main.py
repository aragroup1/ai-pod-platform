# app/database.py
"""
Database connection pool management
"""
import asyncpg
from loguru import logger
from typing import Optional
from app.config import settings


class DatabasePool:
    """Manages PostgreSQL connection pool"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            if not settings.DATABASE_URL:
                raise ValueError("DATABASE_URL is not set in environment variables")
            
            self.pool = await asyncpg.create_pool(
                dsn=settings.DATABASE_URL,
                min_size=2,
                max_size=10,
                command_timeout=60,
                timeout=30
            )
            logger.info("Database pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")
    
    def get_pool(self) -> asyncpg.Pool:
        """Get the connection pool"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized. Call initialize() first.")
        return self.pool


# Global database pool instance
db_pool = DatabasePool()


# Helper function to get database connection
async def get_db():
    """Dependency to get database connection"""
    pool = db_pool.get_pool()
    async with pool.acquire() as connection:
        yield connection
