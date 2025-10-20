# app/api/v1/trends.py
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from app.database import DatabasePool
from app.dependencies import get_db_pool

router = APIRouter()

@router.get("")  # No trailing slash
async def get_trends(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Get trending topics"""
    query = """
        SELECT id, keyword, search_volume, trend_score, geography, category, created_at 
        FROM trends 
        ORDER BY trend_score DESC 
        LIMIT $1 OFFSET $2
    """
    results = await db_pool.fetch(query, limit, offset)
    return {
        "trends": [
            {
                "id": row["id"],
                "keyword": row["keyword"],
                "search_volume": row["search_volume"],
                "trend_score": float(row["trend_score"]) if row["trend_score"] else 0,
                "geography": row["geography"],
                "category": row["category"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None
            }
            for row in results
        ]
    }

# ===================================
# app/api/v1/orders.py
from fastapi import APIRouter, Depends, Query
from app.database import DatabasePool
from app.dependencies import get_db_pool

router = APIRouter()

@router.get("")  # No trailing slash
async def get_orders(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Get orders"""
    query = """
        SELECT id, platform_order_id, platform, order_value, profit, status, created_at 
        FROM orders 
        ORDER BY created_at DESC 
        LIMIT $1 OFFSET $2
    """
    results = await db_pool.fetch(query, limit, offset)
    return {
        "orders": [
            {
                "id": row["id"],
                "platform_order_id": row["platform_order_id"],
                "platform": row["platform"],
                "order_value": float(row["order_value"]) if row["order_value"] else 0,
                "profit": float(row["profit"]) if row["profit"] else 0,
                "status": row["status"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None
            }
            for row in results
        ]
    }

# ===================================
# app/api/v1/artwork.py
from fastapi import APIRouter, Depends, Query
from app.database import DatabasePool
from app.dependencies import get_db_pool

router = APIRouter()

@router.get("")  # No trailing slash
async def get_artwork(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Get artwork"""
    query = """
        SELECT id, prompt, provider, style, image_url, generation_cost, quality_score, created_at 
        FROM artwork 
        ORDER BY created_at DESC 
        LIMIT $1 OFFSET $2
    """
    results = await db_pool.fetch(query, limit, offset)
    return {
        "artwork": [
            {
                "id": row["id"],
                "prompt": row["prompt"],
                "provider": row["provider"],
                "style": row["style"],
                "image_url": row["image_url"],
                "generation_cost": float(row["generation_cost"]) if row["generation_cost"] else 0,
                "quality_score": float(row["quality_score"]) if row["quality_score"] else 0,
                "created_at": row["created_at"].isoformat() if row["created_at"] else None
            }
            for row in results
        ]
    }

# ===================================
# app/api/v1/platforms.py
from fastapi import APIRouter, Depends
from app.database import DatabasePool
from app.dependencies import get_db_pool

router = APIRouter()

@router.get("")  # No trailing slash
async def get_platforms(
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Get platform integrations"""
    # For now, return static list. Later can be from database
    return {
        "platforms": [
            {"name": "shopify", "enabled": True, "order_count": 0},
            {"name": "etsy", "enabled": False, "order_count": 0},
            {"name": "amazon", "enabled": True, "order_count": 0}
        ]
    }
