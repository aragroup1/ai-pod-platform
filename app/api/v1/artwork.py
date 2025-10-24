from fastapi import APIRouter, Depends
from app.database import DatabasePool
from app.dependencies import get_db_pool

router = APIRouter()

@router.get("/")
async def get_artwork(db_pool: DatabasePool = Depends(get_db_pool)):
    """Get artwork"""
    query = "SELECT * FROM artwork ORDER BY created_at DESC LIMIT 20"
    results = await db_pool.fetch(query)
    return {"artwork": [dict(row) for row in results]}
