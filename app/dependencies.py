from fastapi import Request, HTTPException, status
from typing import AsyncGenerator
import asyncpg

async def get_db_pool(request: Request):
    """
    Get database pool from app state
    """
    from app.database import db_pool
    
    if not db_pool.pool:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not connected"
        )
    
    return db_pool.pool
