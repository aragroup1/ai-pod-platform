from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, List
from datetime import datetime, timedelta
from loguru import logger

from app.database import DatabasePool
from app.dependencies import get_db_pool

router = APIRouter()


@router.get("/generation-stats")
async def get_generation_stats(
    days: int = Query(7, ge=1, le=90),
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Get AI generation statistics"""
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        # Total images generated
        total_generated = await db_pool.fetchval(
            "SELECT COUNT(*) FROM artwork WHERE created_at >= $1",
            start_date
        )
        
        # Cost calculation
        total_cost = await db_pool.fetchval(
            "SELECT SUM(generation_cost) FROM artwork WHERE created_at >= $1",
            start_date
        )
        
        # By style breakdown
        by_style = await db_pool.fetch(
            """
            SELECT style, COUNT(*) as count, AVG(quality_score) as avg_quality
            FROM artwork
            WHERE created_at >= $1
            GROUP BY style
            ORDER BY count DESC
            """,
            start_date
        )
        
        # Daily generation counts
        daily_counts = await db_pool.fetch(
            """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as count,
                SUM(generation_cost) as cost
            FROM artwork
            WHERE created_at >= $1
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            """,
            start_date
        )
        
        return {
            "period_days": days,
            "total_generated": total_generated,
            "total_cost": float(total_cost or 0),
            "avg_cost_per_image": float(total_cost / total_generated) if total_generated > 0 else 0,
            "by_style": [
                {
                    "style": row["style"],
                    "count": row["count"],
                    "avg_quality": float(row["avg_quality"] or 0)
                }
                for row in by_style
            ],
            "daily_generation": [
                {
                    "date": row["date"].isoformat(),
                    "count": row["count"],
                    "cost": float(row["cost"] or 0)
                }
                for row in daily_counts
            ]
        }
        
    except Exception as e:
        logger.error(f"Error fetching generation stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trend-performance")
async def get_trend_performance(
    limit: int = Query(10, ge=1, le=50),
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Get performance of trends (which have products)"""
    try:
        results = await db_pool.fetch(
            """
            SELECT 
                t.id,
                t.keyword,
                t.trend_score,
                COUNT(DISTINCT a.id) as artwork_count,
                COUNT(DISTINCT p.id) as product_count,
                AVG(p.base_price) as avg_price
            FROM trends t
            LEFT JOIN artwork a ON a.trend_id = t.id
            LEFT JOIN products p ON p.artwork_id = a.id
            GROUP BY t.id, t.keyword, t.trend_score
            HAVING COUNT(DISTINCT a.id) > 0
            ORDER BY t.trend_score DESC
            LIMIT $1
            """,
            limit
        )
        
        return {
            "trends": [
                {
                    "id": row["id"],
                    "keyword": row["keyword"],
                    "trend_score": float(row["trend_score"] or 0),
                    "artwork_count": row["artwork_count"],
                    "product_count": row["product_count"],
                    "avg_price": float(row["avg_price"] or 0)
                }
                for row in results
            ]
        }
        
    except Exception as e:
        logger.error(f"Error fetching trend performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-health")
async def get_system_health(db_pool: DatabasePool = Depends(get_db_pool)):
    """Get system health metrics"""
    try:
        # Check how many trends need products
        trends_awaiting = await db_pool.fetchval(
            """
            SELECT COUNT(*)
            FROM trends t
            LEFT JOIN artwork a ON a.trend_id = t.id
            WHERE a.id IS NULL AND t.trend_score >= 6.0
            """
        )
        
        # Check recent generation activity
        recent_generation = await db_pool.fetchval(
            """
            SELECT COUNT(*)
            FROM artwork
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            """
        )
        
        # Check product activation rate
        product_stats = await db_pool.fetchrow(
            """
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'active') as active,
                COUNT(*) FILTER (WHERE status = 'draft') as draft
            FROM products
            """
        )
        
        return {
            "trends_awaiting_generation": trends_awaiting,
            "images_generated_24h": recent_generation,
            "products": {
                "total": product_stats["total"],
                "active": product_stats["active"],
                "draft": product_stats["draft"],
                "activation_rate": (product_stats["active"] / product_stats["total"] * 100) if product_stats["total"] > 0 else 0
            },
            "status": "healthy" if trends_awaiting < 20 else "attention_needed"
        }
        
    except Exception as e:
        logger.error(f"Error fetching system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))
