from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from typing import Optional, List
from loguru import logger
import json

from app.database import DatabasePool
from app.dependencies import get_db_pool
from app.core.trends.service import TrendService

router = APIRouter()


@router.get("/")
async def get_trends(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    min_score: float = Query(default=0.0, ge=0.0, le=10.0),
    category: Optional[str] = None,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    Get stored trends from database
    """
    try:
        logger.info(f"Fetching trends with limit={limit}, offset={offset}, min_score={min_score}")
        
        # Build query
        if category:
            query = """
                SELECT id, keyword, search_volume, trend_score, 
                       geography, category, created_at, data
                FROM trends
                WHERE trend_score >= $1 AND category = $2
                ORDER BY trend_score DESC, created_at DESC
                LIMIT $3 OFFSET $4
            """
            trends = await db_pool.fetch(query, min_score, category, limit, offset)
        else:
            query = """
                SELECT id, keyword, search_volume, trend_score, 
                       geography, category, created_at, data
                FROM trends
                WHERE trend_score >= $1
                ORDER BY trend_score DESC, created_at DESC
                LIMIT $2 OFFSET $3
            """
            trends = await db_pool.fetch(query, min_score, limit, offset)
        
        # Format results
        trends_list = []
        for t in trends:
            trends_list.append({
                "id": t["id"],
                "keyword": t["keyword"],
                "search_volume": t["search_volume"],
                "trend_score": float(t["trend_score"]) if t["trend_score"] else 0.0,
                "geography": t["geography"],
                "category": t["category"],
                "created_at": t["created_at"].isoformat() if t["created_at"] else None,
                "data": t["data"]
            })
        
        logger.info(f"Successfully fetched {len(trends_list)} trends")
        
        return {
            "trends": trends_list,
            "total": len(trends_list),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error fetching trends: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch")
async def fetch_trends_from_google(
    region: str = Query(default="GB"),
    min_score: float = Query(default=6.0, ge=0.0, le=10.0),
    background_tasks: BackgroundTasks = None,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    Fetch new trends from Google Trends and store them
    
    This endpoint:
    1. Fetches trending topics from Google Trends
    2. Filters for POD-suitable keywords
    3. Stores them in the database
    4. Returns summary of what was found
    """
    try:
        logger.info(f"🔍 Fetching trends from Google Trends for region: {region}")
        
        trend_service = TrendService(db_pool)
        
        # Fetch and store trends
        stored_trends = await trend_service.fetch_and_store_trends(
            region=region,
            min_score=min_score
        )
        
        if not stored_trends:
            return {
                "success": False,
                "message": "No suitable trends found",
                "trends_stored": 0,
                "region": region
            }
        
        # Get top 5 for preview
        top_trends = stored_trends[:5]
        
        logger.info(f"✅ Successfully stored {len(stored_trends)} trends")
        
        return {
            "success": True,
            "message": f"Successfully fetched {len(stored_trends)} trends from Google",
            "trends_stored": len(stored_trends),
            "region": region,
            "top_trends": [
                {
                    "keyword": t["keyword"],
                    "search_volume": t["search_volume"],
                    "trend_score": t["trend_score"],
                    "category": t["category"]
                }
                for t in top_trends
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching trends: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/without-products")
async def get_trends_without_products(
    limit: int = Query(default=10, ge=1, le=50),
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Get trends that haven't been generated into products yet"""
    try:
        trend_service = TrendService(db_pool)
        trends = await trend_service.get_trends_without_products(limit=limit)
        
        return {
            "trends": trends,
            "total": len(trends)
        }
        
    except Exception as e:
        logger.error(f"Error fetching trends without products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{trend_id}")
async def get_trend(
    trend_id: int,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Get a single trend by ID"""
    try:
        trend = await db_pool.fetchrow(
            """
            SELECT id, keyword, search_volume, trend_score,
                   geography, category, created_at, data
            FROM trends
            WHERE id = $1
            """,
            trend_id
        )
        
        if not trend:
            raise HTTPException(status_code=404, detail="Trend not found")
        
        return {
            "id": trend["id"],
            "keyword": trend["keyword"],
            "search_volume": trend["search_volume"],
            "trend_score": float(trend["trend_score"]) if trend["trend_score"] else 0.0,
            "geography": trend["geography"],
            "category": trend["category"],
            "created_at": trend["created_at"].isoformat() if trend["created_at"] else None,
            "data": trend["data"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching trend: {e}")
        raise HTTPException(status_code=500, detail=str(e))
