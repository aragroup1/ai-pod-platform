from fastapi import APIRouter, HTTPException
from app.database import db_pool

router = APIRouter()

@router.get("/")
async def get_products():
    """Get products"""
    query = "SELECT * FROM products ORDER BY created_at DESC LIMIT 20"
    results = await db_pool.fetch(query)
    return {"products": [dict(row) for row in results]}
