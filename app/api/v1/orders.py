from fastapi import APIRouter, Depends
from app.database import DatabasePool
from app.dependencies import get_db_pool

router = APIRouter()

@router.get("/")
async def get_orders(db_pool: DatabasePool = Depends(get_db_pool)):
    """Get orders"""
    query = "SELECT * FROM orders ORDER BY created_at DESC LIMIT 20"
    results = await db_pool.fetch(query)
    return {"orders": [dict(row) for row in results]}
