import redis.asyncio as redis
from functools import wraps
import json
import hashlib
from typing import Optional, Any
from app.config import settings

class RedisClient:
    def __init__(self):
        self.client = None
    
    async def initialize(self):
        self.client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
    
    async def close(self):
        if self.client:
            await self.client.close()
    
    async def get(self, key: str) -> Optional[str]:
        if self.client:
            return await self.client.get(key)
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        if self.client:
            await self.client.set(key, json.dumps(value), ex=ttl)
    
    async def delete(self, key: str):
        if self.client:
            await self.client.delete(key)
    
    async def ping(self) -> bool:
        if self.client:
            return await self.client.ping()
        return False

redis_client = RedisClient()

def cache_result(ttl: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}:{hashlib.md5(str(args).encode()).hexdigest()}"
            
            # Try to get from cache
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Call function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await redis_client.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator
