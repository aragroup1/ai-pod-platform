from fastapi import APIRouter
from app.database import db_pool

router = APIRouter()

@router.get("/")
async def get_orders():
    """Get orders"""
    query = "SELECT * FROM orders ORDER BY created_at DESC LIMIT 20"
    results = await db_pool.fetch(query)
    return {"orders": [dict(row) for row in results]}
