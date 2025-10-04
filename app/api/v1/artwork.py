from fastapi import APIRouter
from app.database import db_pool

router = APIRouter()

@router.get("/")
async def get_artwork():
    """Get artwork"""
    query = "SELECT * FROM artwork ORDER BY created_at DESC LIMIT 20"
    results = await db_pool.fetch(query)
    return {"artwork": [dict(row) for row in results]}
