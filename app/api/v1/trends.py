from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.database import db_pool

router = APIRouter()

@router.get("/")
async def get_trends(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get trending topics"""
    query = """
        SELECT * FROM trends 
        ORDER BY trend_score DESC 
        LIMIT $1 OFFSET $2
    """
    results = await db_pool.fetch(query, limit, offset)
    return {"trends": [dict(row) for row in results]}
