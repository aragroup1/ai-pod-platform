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
    limit: int = Query(default=20, ge=1, le=50),
    background_tasks: BackgroundTasks = None,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    Fetch new trends from multiple sources and store them
    
    This endpoint:
    1. Fetches trending topics from Google Trends (FREE)
    2. Enriches with Keyword Planner data (if configured)
    3. Scores trends for POD suitability
    4. Stores high-potential trends in database
    5. Returns summary of what was found
    
    The trends are automatically scored based on:
    - Search volume
    - Rising trend status
    - Competition level
    - Visual/artistic potential
    - Commercial intent for POD
    """
    try:
        logger.info(f"🔍 Fetching trends from Google Trends for region: {region}")
        
        trend_service = TrendService(db_pool)
        
        # Fetch and store trends
        stored_trends = await trend_service.fetch_and_store_trends(
            region=region,
            min_score=min_score,
            limit=limit
        )
        
        if not stored_trends:
            # Try with fallback trends
            logger.info("No trends from Google, using proven POD keywords...")
            stored_trends = await trend_service.fetch_and_store_trends(
                region=region,
                min_score=5.0,  # Lower threshold for fallbacks
                limit=limit
            )
            
            if not stored_trends:
                return {
                    "success": False,
                    "message": "No suitable trends found. Database may already have trends.",
                    "trends_stored": 0,
                    "region": region
                }
        
        # Get top 5 for preview
        top_trends = stored_trends[:5]
        
        logger.info(f"✅ Successfully stored {len(stored_trends)} trends")
        
        return {
            "success": True,
            "message": f"Successfully fetched {len(stored_trends)} high-potential trends",
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
            ],
            "ready_for_generation": True,
            "next_step": "Click 'Generate Products' to create AI artwork for these trends"
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching trends: {e}")
        logger.exception("Full traceback:")
        
        # Return partial success if we have some data
        return {
            "success": False,
            "message": f"Error occurred but may have stored some trends: {str(e)}",
            "trends_stored": 0,
            "region": region,
            "error": str(e)
        }


@router.get("/without-products")
async def get_trends_without_products(
    limit: int = Query(default=10, ge=1, le=50),
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Get trends that haven't been generated into products yet"""
    try:
        trend_service = TrendService(db_pool)
        trends = await trend_service.get_trends_without_products(limit=limit)
        
        if not trends:
            return {
                "trends": [],
                "total": 0,
                "message": "No trends without products. Fetch new trends or all trends have products."
            }
        
        return {
            "trends": trends,
            "total": len(trends),
            "ready_for_generation": True
        }
        
    except Exception as e:
        logger.error(f"Error fetching trends without products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics")
async def get_trend_analytics(
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Get analytics about trends in the database"""
    try:
        # Get various statistics
        stats = await db_pool.fetchrow(
            """
            SELECT 
                COUNT(*) as total_trends,
                COUNT(DISTINCT category) as total_categories,
                AVG(trend_score) as avg_score,
                MAX(search_volume) as max_search_volume,
                COUNT(*) FILTER (WHERE trend_score >= 8) as high_potential_trends,
                COUNT(DISTINCT geography) as total_regions
            FROM trends
            WHERE created_at > NOW() - INTERVAL '30 days'
            """
        )
        
        # Get top categories
        categories = await db_pool.fetch(
            """
            SELECT category, COUNT(*) as count, AVG(trend_score) as avg_score
            FROM trends
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
            LIMIT 5
            """
        )
        
        # Get trends with products vs without
        product_coverage = await db_pool.fetchrow(
            """
            SELECT 
                COUNT(DISTINCT t.id) as total,
                COUNT(DISTINCT a.trend_id) as with_products
            FROM trends t
            LEFT JOIN artwork a ON t.id = a.trend_id
            """
        )
        
        return {
            "total_trends": stats["total_trends"],
            "total_categories": stats["total_categories"],
            "avg_trend_score": float(stats["avg_score"]) if stats["avg_score"] else 0,
            "max_search_volume": stats["max_search_volume"],
            "high_potential_trends": stats["high_potential_trends"],
            "total_regions": stats["total_regions"],
            "top_categories": [
                {
                    "name": cat["category"],
                    "count": cat["count"],
                    "avg_score": float(cat["avg_score"])
                }
                for cat in categories
            ],
            "product_coverage": {
                "total_trends": product_coverage["total"],
                "with_products": product_coverage["with_products"],
                "without_products": product_coverage["total"] - product_coverage["with_products"],
                "coverage_percentage": round(
                    (product_coverage["with_products"] / product_coverage["total"] * 100), 2
                ) if product_coverage["total"] > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting trend analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{trend_id}")
async def get_trend(
    trend_id: int,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Get a single trend by ID with full details"""
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
        
        # Check if trend has products
        product_count = await db_pool.fetchval(
            """
            SELECT COUNT(*)
            FROM artwork a
            JOIN products p ON p.artwork_id = a.id
            WHERE a.trend_id = $1
            """,
            trend_id
        )
        
        return {
            "id": trend["id"],
            "keyword": trend["keyword"],
            "search_volume": trend["search_volume"],
            "trend_score": float(trend["trend_score"]) if trend["trend_score"] else 0.0,
            "geography": trend["geography"],
            "category": trend["category"],
            "created_at": trend["created_at"].isoformat() if trend["created_at"] else None,
            "data": trend["data"],
            "product_count": product_count,
            "has_products": product_count > 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching trend: {e}")
        raise HTTPException(status_code=500, detail=str(e))
