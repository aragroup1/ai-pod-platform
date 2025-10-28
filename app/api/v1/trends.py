# ========================================
# CORRECTED ENDPOINTS FOR YOUR PROJECT
# Add these to: app/api/v1/trends.py
# ========================================
# Your project uses direct database queries (asyncpg), NOT SQLAlchemy models

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from app.database import get_db_pool

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class ManualKeywordInput(BaseModel):
    keywords_text: str
    category: Optional[str] = "general"

class KeywordCreate(BaseModel):
    keyword: str
    search_volume: Optional[int] = None
    category: Optional[str] = "general"
    designs_allocated: Optional[int] = None
    trend_score: Optional[float] = 5.0

class BatchKeywordImport(BaseModel):
    keywords: List[KeywordCreate]

# ========================================
# ENDPOINT 1: MANUAL KEYWORD INPUT
# ========================================
@router.post("/manual-add")
async def add_manual_keywords(input_data: ManualKeywordInput):
    """
    Add keywords manually from dashboard
    Accepts comma or newline separated keywords
    """
    try:
        db_pool = get_db_pool()
        
        # Parse keywords
        keywords_text = input_data.keywords_text
        category = input_data.category or "general"
        
        if "," in keywords_text:
            keyword_list = [k.strip() for k in keywords_text.split(",") if k.strip()]
        else:
            keyword_list = [k.strip() for k in keywords_text.split("\n") if k.strip()]
        
        if not keyword_list:
            raise HTTPException(status_code=400, detail="No valid keywords found")
        
        logger.info(f"📝 Manual add: {len(keyword_list)} keywords")
        
        # Smart volume estimation
        def estimate_volume(keyword: str) -> int:
            word_count = len(keyword.split())
            if word_count <= 2:
                return 50000
            elif word_count <= 3:
                return 30000
            else:
                return 15000
        
        # Smart design allocation
        def calculate_designs(volume: int) -> int:
            if volume >= 150000:
                return 250
            elif volume >= 100000:
                return 200
            elif volume >= 50000:
                return 150
            elif volume >= 30000:
                return 100
            elif volume >= 20000:
                return 75
            elif volume >= 10000:
                return 50
            else:
                return 30
        
        # Store keywords
        stored_keywords = []
        total_designs = 0
        
        for keyword in keyword_list:
            keyword_lower = keyword.lower()
            
            # Check if exists
            existing = await db_pool.fetchrow(
                "SELECT * FROM keywords WHERE keyword = $1",
                keyword_lower
            )
            
            if existing:
                logger.info(f"⏭️  Already exists: {keyword_lower}")
                stored_keywords.append(dict(existing))
                total_designs += existing['designs_allocated']
                continue
            
            # Create new
            estimated_volume = estimate_volume(keyword_lower)
            designs = calculate_designs(estimated_volume)
            
            new_keyword = await db_pool.fetchrow(
                """
                INSERT INTO keywords (keyword, search_volume, category, designs_allocated, trend_score, created_at)
                VALUES ($1, $2, $3, $4, $5, NOW())
                RETURNING *
                """,
                keyword_lower,
                estimated_volume,
                category,
                designs,
                7.0
            )
            
            stored_keywords.append(dict(new_keyword))
            total_designs += designs
        
        return {
            "success": True,
            "message": f"Added {len(stored_keywords)} keywords",
            "keywords_stored": len(stored_keywords),
            "potential_listings": total_designs * 8,
            "keywords": stored_keywords
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error adding manual keywords: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# ENDPOINT 2: BATCH IMPORT
# ========================================
@router.post("/batch-import")
async def batch_import_keywords(batch: BatchKeywordImport):
    """Import multiple keywords at once"""
    try:
        db_pool = get_db_pool()
        logger.info(f"📦 Batch import: {len(batch.keywords)} keywords")
        
        stored_keywords = []
        total_designs = 0
        
        # Smart design allocation
        def calculate_designs(volume: int) -> int:
            if volume >= 150000:
                return 250
            elif volume >= 100000:
                return 200
            elif volume >= 50000:
                return 150
            elif volume >= 30000:
                return 100
            elif volume >= 20000:
                return 75
            elif volume >= 10000:
                return 50
            else:
                return 30
        
        for kw_data in batch.keywords:
            keyword_lower = kw_data.keyword.lower()
            
            # Check if exists
            existing = await db_pool.fetchrow(
                "SELECT * FROM keywords WHERE keyword = $1",
                keyword_lower
            )
            
            if existing:
                stored_keywords.append(dict(existing))
                total_designs += existing['designs_allocated']
                continue
            
            # Calculate designs
            designs = kw_data.designs_allocated
            if designs is None:
                volume = kw_data.search_volume or 20000
                designs = calculate_designs(volume)
            
            # Create keyword
            new_keyword = await db_pool.fetchrow(
                """
                INSERT INTO keywords (keyword, search_volume, category, designs_allocated, trend_score, created_at)
                VALUES ($1, $2, $3, $4, $5, NOW())
                RETURNING *
                """,
                keyword_lower,
                kw_data.search_volume or 20000,
                kw_data.category or "general",
                designs,
                kw_data.trend_score or 5.0
            )
            
            stored_keywords.append(dict(new_keyword))
            total_designs += designs
        
        return {
            "success": True,
            "message": f"Imported {len(stored_keywords)} keywords",
            "keywords_stored": len(stored_keywords),
            "potential_listings": total_designs * 8,
            "keywords": stored_keywords
        }
        
    except Exception as e:
        logger.error(f"❌ Batch import error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# ENDPOINT 3: GET STATISTICS
# ========================================
@router.get("/stats")
async def get_trend_stats():
    """Get statistics about stored keywords"""
    try:
        db_pool = get_db_pool()
        
        # Total keywords
        total = await db_pool.fetchval("SELECT COUNT(*) FROM keywords")
        
        # Category breakdown
        categories = await db_pool.fetch(
            """
            SELECT 
                category,
                COUNT(*) as count,
                SUM(designs_allocated) as designs
            FROM keywords
            GROUP BY category
            ORDER BY count DESC
            """
        )
        
        # Total designs
        total_designs = await db_pool.fetchval(
            "SELECT SUM(designs_allocated) FROM keywords"
        ) or 0
        
        return {
            "total_keywords": total or 0,
            "total_potential_listings": total_designs * 8,
            "categories": [
                {
                    "category": cat['category'],
                    "count": cat['count'],
                    "designs": cat['designs'] or 0
                }
                for cat in categories
            ]
        }
    except Exception as e:
        logger.error(f"❌ Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# ENDPOINT 4: GET ALL KEYWORDS
# ========================================
@router.get("/")
async def get_trends(
    category: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500)
):
    """Get stored keywords with optional category filter"""
    try:
        db_pool = get_db_pool()
        
        if category:
            keywords = await db_pool.fetch(
                """
                SELECT * FROM keywords
                WHERE category = $1
                ORDER BY search_volume DESC
                LIMIT $2
                """,
                category, limit
            )
        else:
            keywords = await db_pool.fetch(
                """
                SELECT * FROM keywords
                ORDER BY search_volume DESC
                LIMIT $1
                """,
                limit
            )
        
        return [dict(kw) for kw in keywords]
        
    except Exception as e:
        logger.error(f"❌ Error fetching keywords: {e}")
        raise HTTPException(status_code=500, detail=str(e))
