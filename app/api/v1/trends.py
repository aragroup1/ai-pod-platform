from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from typing import List, Optional
from loguru import logger

from app.database import DatabasePool
from app.dependencies import get_db_pool
from app.core.trends.service import TrendService
from app.core.trends.intelligent_trend_analyzer import get_intelligent_analyzer

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


@router.post("/analyze-intelligent")
async def analyze_trends_intelligently(
    background_tasks: BackgroundTasks,
    min_search_volume: int = Query(1000, description="Minimum search volume"),
    max_trends: int = Query(50, description="Maximum trends to store"),
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    🧠 NEW: Intelligent multi-source trend analysis
    
    This is the advanced system that:
    - Fetches from multiple sources (Google Trends, Etsy, Pinterest)
    - Prioritizes by search volume (most important)
    - Scores intelligently based on multiple factors
    - Stores only the best opportunities
    
    Run this instead of regular /fetch for better results!
    """
    try:
        analyzer = get_intelligent_analyzer(db_pool)
        
        # Run in background
        background_tasks.add_task(
            analyzer.run_intelligent_analysis,
            min_search_volume=min_search_volume,
            max_trends=max_trends
        )
        
        return {
            "message": "Intelligent trend analysis started",
            "min_search_volume": min_search_volume,
            "max_trends": max_trends,
            "status": "processing",
            "description": "Multi-source analysis with intelligent prioritization"
        }
        
    except Exception as e:
        logger.exception(f"Error starting intelligent analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to start analysis")


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


@router.get("/analysis-status")
async def get_analysis_status(db_pool: DatabasePool = Depends(get_db_pool)):
    """
    Get status of trend analysis and recommendations
    """
    try:
        # Get trends with high scores
        high_value = await db_pool.fetch(
            """
            SELECT keyword, search_volume, trend_score, data
            FROM trends
            WHERE trend_score >= 7.0
            ORDER BY trend_score DESC
            LIMIT 10
            """
        )
        
        # Get trends awaiting generation
        awaiting = await db_pool.fetchval(
            """
            SELECT COUNT(*)
            FROM trends t
            LEFT JOIN artwork a ON a.trend_id = t.id
            WHERE a.id IS NULL
            AND t.trend_score >= 6.0
            """
        )
        
        # Get recent analysis runs
        recent_trends = await db_pool.fetchval(
            """
            SELECT COUNT(*)
            FROM trends
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            """
        )
        
        return {
            "high_value_trends": [
                {
                    "keyword": t["keyword"],
                    "search_volume": t["search_volume"],
                    "score": float(t["trend_score"]),
                    "sources": t["data"].get("sources", []) if t["data"] else []
                }
                for t in high_value
            ],
            "trends_awaiting_generation": awaiting,
            "trends_added_24h": recent_trends,
            "recommendation": "Run intelligent analysis for best results" if awaiting < 5 else "Ready to generate products"
        }
        
    except Exception as e:
        logger.exception(f"Error fetching analysis status: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch status")
