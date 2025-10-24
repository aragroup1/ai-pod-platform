from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from typing import List, Optional
from loguru import logger

from app.database import DatabasePool
from app.dependencies import get_db_pool
from app.core.trends.service import TrendService

router = APIRouter()


@router.get("/")
async def get_trends(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    min_score: float = Query(0.0, ge=0.0, le=10.0),
    category: Optional[str] = None,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Get trending topics from database"""
    try:
        trend_service = TrendService(db_pool)
        trends = await trend_service.get_top_trends(
            limit=limit,
            min_score=min_score,
            category=category
        )
        
        return {
            "trends": [
                {
                    "id": t["id"],
                    "keyword": t["keyword"],
                    "search_volume": t["search_volume"],
                    "trend_score": float(t["trend_score"]) if t["trend_score"] else 0,
                    "geography": t["geography"],
                    "category": t["category"],
                    "created_at": t["created_at"].isoformat() if t["created_at"] else None
                }
                for t in trends
            ],
            "total": len(trends)
        }
        
    except Exception as e:
        logger.exception(f"Error fetching trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trends")


@router.post("/fetch")
async def fetch_new_trends(
    background_tasks: BackgroundTasks,
    region: str = Query("GB", description="Country code"),
    min_score: float = Query(6.0, ge=0.0, le=10.0),
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    Manually trigger trend fetching from Google Trends
    This runs in the background
    """
    try:
        trend_service = TrendService(db_pool)
        
        # Run in background
        background_tasks.add_task(
            trend_service.fetch_and_store_trends,
            region=region,
            min_score=min_score
        )
        
        return {
            "message": "Trend fetching started in background",
            "region": region,
            "min_score": min_score
        }
        
    except Exception as e:
        logger.exception(f"Error starting trend fetch: {e}")
        raise HTTPException(status_code=500, detail="Failed to start trend fetching")


@router.get("/without-products")
async def get_trends_without_products(
    limit: int = Query(10, ge=1, le=50),
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Get trends that don't have products generated yet"""
    try:
        trend_service = TrendService(db_pool)
        trends = await trend_service.get_trends_without_products(limit=limit)
        
        return {
            "trends": trends,
            "total": len(trends)
        }
        
    except Exception as e:
        logger.exception(f"Error fetching trends without products: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trends")
