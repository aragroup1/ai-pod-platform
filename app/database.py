import asyncpg
from loguru import logger
from typing import Optional
import os

class DatabasePool:
    def __init__(self):
        self.pool = None
        self.is_connected = False
    
    async def initialize(self):
        """Initialize database connection pool"""
        database_url = os.getenv("DATABASE_URL", "")
        
        if not database_url:
            logger.warning("No DATABASE_URL provided, database features disabled")
            return
        
        try:
            self.pool = await asyncpg.create_pool(
                database_url,
                min_size=2,
                max_size=10,
                timeout=10,
                command_timeout=10,
            )
            self.is_connected = True
            logger.info("Database pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            self.is_connected = False
    
    async def close(self):
        """Close database pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")
    
    async def execute(self, query: str, *args):
        """Execute query with error handling"""
        if not self.pool:
            logger.warning("Database not available")
            return None
        
        try:
            async with self.pool.acquire() as connection:
                return await connection.execute(query, *args)
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return None
    
    async def fetch(self, query: str, *args):
        """Fetch results with error handling"""
        if not self.pool:
            return []
        
        try:
            async with self.pool.acquire() as connection:
                return await connection.fetch(query, *args)
        except Exception as e:
            logger.error(f"Database fetch failed: {e}")
            return []
    
    async def fetchrow(self, query: str, *args):
        """Fetch single row with error handling"""
        if not self.pool:
            return None
        
        try:
            async with self.pool.acquire() as connection:
                return await connection.fetchrow(query, *args)
        except Exception as e:
            logger.error(f"Database fetchrow failed: {e}")
            return None
    
    async def fetchval(self, query: str, *args):
        """Fetch single value with error handling"""
        if not self.pool:
            return None
        
        try:
            async with self.pool.acquire() as connection:
                return await connection.fetchval(query, *args)
        except Exception as e:
            logger.error(f"Database fetchval failed: {e}")
            return None

# Global database pool instance
db_pool = DatabasePool()

# Dummy for imports that expect these
Base = object
engine = None

async def get_db():
    """Dummy function for compatibility"""
    yield None
