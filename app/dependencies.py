# app/dependencies.py
"""
Dependency injection for FastAPI routes
Matches your existing repo structure
"""
from fastapi import Request, HTTPException, status
from typing import Optional

async def get_db_pool(request: Request):
    """
    Dependency to get the database pool from app state.
    Raises 503 error if database is not connected.
    
    Usage in routes:
        @router.get("/")
        async def endpoint(db_pool: DatabasePool = Depends(get_db_pool)):
            ...
    """
    if not hasattr(request.app.state, 'db_pool'):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database pool not initialized",
        )
    
    if not request.app.state.db_pool.is_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is not available",
        )
    
    return request.app.state.db_pool


# Optional: Admin user authentication (placeholder for future implementation)
async def get_current_admin_user():
    """
    Placeholder for admin user authentication.
    Implement proper auth when needed.
    """
    return {"username": "admin", "roles": ["admin"]}
