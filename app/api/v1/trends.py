# ========================================
# ADD THESE ENDPOINTS TO: app/api/v1/trends.py
# ========================================

# Add these imports at the top:
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.keyword import Keyword
import logging

logger = logging.getLogger(__name__)

# Add these Pydantic models:
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
# NEW ENDPOINT 1: MANUAL KEYWORD INPUT
# ========================================
@router.post("/manual-add")
async def add_manual_keywords(
    input_data: ManualKeywordInput,
    db: Session = Depends(get_db)
):
    """
    Add keywords manually from dashboard
    Accepts comma or newline separated keywords
    """
    try:
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
        
        # Smart design allocation based on volume
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
            existing = db.query(Keyword).filter(
                Keyword.keyword == keyword_lower
            ).first()
            
            if existing:
                logger.info(f"⏭️  Already exists: {keyword_lower}")
                stored_keywords.append(existing)
                total_designs += existing.designs_allocated
                continue
            
            # Create new
            estimated_volume = estimate_volume(keyword_lower)
            designs = calculate_designs(estimated_volume)
            
            new_keyword = Keyword(
                keyword=keyword_lower,
                search_volume=estimated_volume,
                category=category,
                designs_allocated=designs,
                trend_score=7.0
            )
            db.add(new_keyword)
            stored_keywords.append(new_keyword)
            total_designs += designs
        
        db.commit()
        
        for kw in stored_keywords:
            db.refresh(kw)
        
        return {
            "success": True,
            "message": f"Added {len(stored_keywords)} keywords",
            "keywords_stored": len(stored_keywords),
            "potential_listings": total_designs * 8,
            "keywords": [
                {
                    "id": kw.id,
                    "keyword": kw.keyword,
                    "search_volume": kw.search_volume,
                    "category": kw.category,
                    "designs_allocated": kw.designs_allocated,
                    "trend_score": kw.trend_score,
                    "created_at": kw.created_at
                }
                for kw in stored_keywords
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error adding manual keywords: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# NEW ENDPOINT 2: BATCH IMPORT
# ========================================
@router.post("/batch-import")
async def batch_import_keywords(
    batch: BatchKeywordImport,
    db: Session = Depends(get_db)
):
    """
    Import multiple keywords at once
    Used by external scripts or bulk operations
    """
    try:
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
            existing = db.query(Keyword).filter(
                Keyword.keyword == keyword_lower
            ).first()
            
            if existing:
                stored_keywords.append(existing)
                total_designs += existing.designs_allocated
                continue
            
            # Calculate designs if not provided
            designs = kw_data.designs_allocated
            if designs is None:
                volume = kw_data.search_volume or 20000
                designs = calculate_designs(volume)
            
            # Create keyword
            new_keyword = Keyword(
                keyword=keyword_lower,
                search_volume=kw_data.search_volume or 20000,
                category=kw_data.category or "general",
                designs_allocated=designs,
                trend_score=kw_data.trend_score or 5.0
            )
            db.add(new_keyword)
            stored_keywords.append(new_keyword)
            total_designs += designs
        
        db.commit()
        
        for kw in stored_keywords:
            db.refresh(kw)
        
        return {
            "success": True,
            "message": f"Imported {len(stored_keywords)} keywords",
            "keywords_stored": len(stored_keywords),
            "potential_listings": total_designs * 8,
            "keywords": [
                {
                    "id": kw.id,
                    "keyword": kw.keyword,
                    "search_volume": kw.search_volume,
                    "category": kw.category,
                    "designs_allocated": kw.designs_allocated
                }
                for kw in stored_keywords
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Batch import error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# NEW ENDPOINT 3: GET TRENDS WITH STATS
# ========================================
@router.get("/stats")
async def get_trend_stats(db: Session = Depends(get_db)):
    """Get statistics about stored keywords"""
    try:
        total = db.query(Keyword).count()
        
        # Category breakdown
        from sqlalchemy import func
        categories = db.query(
            Keyword.category,
            func.count(Keyword.id).label("count"),
            func.sum(Keyword.designs_allocated).label("designs")
        ).group_by(Keyword.category).all()
        
        total_designs = db.query(func.sum(Keyword.designs_allocated)).scalar() or 0
        
        return {
            "total_keywords": total,
            "total_potential_listings": total_designs * 8,
            "categories": [
                {
                    "category": cat,
                    "count": count,
                    "designs": designs or 0
                }
                for cat, count, designs in categories
            ]
        }
    except Exception as e:
        logger.error(f"❌ Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
