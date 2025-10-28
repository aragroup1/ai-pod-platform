import redis.asyncio as redis
from loguru import logger
import os
import json
from typing import Optional, Any
from app.config import settings

class RedisClient:
    def __init__(self):
        self.client = None
        self.is_connected = False
    
    async def initialize(self):
        """Initialize Redis connection"""
        redis_url = os.getenv("REDIS_URL", "")
        
        if not redis_url:
            logger.warning("No REDIS_URL provided, caching disabled")
            return
        
        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
            await self.client.ping()
            self.is_connected = True
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self.is_connected = False
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        if not self.client or not self.is_connected:
            return None
        
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Redis get failed: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache"""
        if not self.client or not self.is_connected:
            return
        
        try:
            await self.client.set(key, json.dumps(value), ex=ttl)
        except Exception as e:
            logger.error(f"Redis set failed: {e}")
    
    async def ping(self) -> bool:
        """Check Redis connection"""
        if not self.client:
            return False
        
        try:
            await self.client.ping()
            return True
        except:
            return False

# Global Redis client instance
redis_client = RedisClient()

# Dummy cache decorator for when Redis is not available
def cache_result(ttl: int = 300):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Just call the function without caching if Redis is not available
            return await func(*args, **kwargs)
        return wrapper
    return decorator

class CacheClient:
    """Manages Redis connection for caching"""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
            # Test connection
            await self.client.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed")


# Global cache client instance
cache_client = CacheClient()
