from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.core.trends.service import TrendService
from app.models.keyword import Keyword
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trends", tags=["trends"])

# Pydantic models
class KeywordCreate(BaseModel):
    keyword: str
    search_volume: Optional[int] = None
    category: Optional[str] = "general"
    designs_allocated: Optional[int] = None
    trend_score: Optional[float] = 5.0

class BatchKeywordImport(BaseModel):
    keywords: List[KeywordCreate]

class KeywordResponse(BaseModel):
    id: int
    keyword: str
    search_volume: int
    category: str
    designs_allocated: int
    trend_score: float
    created_at: datetime

    class Config:
        from_attributes = True

class TrendResponse(BaseModel):
    success: bool
    message: str
    keywords_stored: int
    potential_listings: int
    keywords: List[KeywordResponse]

@router.post("/fetch", response_model=TrendResponse)
async def fetch_trends(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Fetch and store trending keywords"""
    service = TrendService(db)
    result = service.fetch_and_store_trends(limit=limit)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result

@router.post("/manual-add", response_model=TrendResponse)
async def add_manual_keywords(
    keywords_text: str,
    category: Optional[str] = "general",
    db: Session = Depends(get_db)
):
    """
    Add keywords manually from a comma or newline separated list
    Example: "dog mom, cat dad, coffee lover"
    """
    try:
        # Parse keywords
        if "," in keywords_text:
            keyword_list = [k.strip() for k in keywords_text.split(",") if k.strip()]
        else:
            keyword_list = [k.strip() for k in keywords_text.split("\n") if k.strip()]
        
        if not keyword_list:
            raise HTTPException(status_code=400, detail="No valid keywords found")
        
        logger.info(f"📝 Manual keyword add: {len(keyword_list)} keywords")
        
        # Calculate designs based on estimated volume
        def estimate_volume(keyword: str) -> int:
            """Rough estimation - you can enhance this"""
            word_count = len(keyword.split())
            if word_count <= 2:
                return 50000  # Short, likely high volume
            elif word_count <= 3:
                return 30000  # Medium
            else:
                return 15000  # Longer, niche
        
        def calculate_designs(volume: int) -> int:
            """Smart design allocation"""
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
                return 30  # Generous default
        
        # Create keyword objects
        keywords_to_add = []
        for keyword in keyword_list:
            estimated_volume = estimate_volume(keyword)
            designs = calculate_designs(estimated_volume)
            
            keywords_to_add.append({
                "keyword": keyword.lower(),
                "search_volume": estimated_volume,
                "category": category,
                "designs_allocated": designs,
                "trend_score": 7.0  # Manual adds get good score
            })
        
        # Store keywords
        stored_keywords = []
        total_designs = 0
        
        for kw_data in keywords_to_add:
            # Check if exists
            existing = db.query(Keyword).filter(
                Keyword.keyword == kw_data["keyword"]
            ).first()
            
            if existing:
                logger.info(f"⏭️  Keyword already exists: {kw_data['keyword']}")
                stored_keywords.append(existing)
                total_designs += existing.designs_allocated
                continue
            
            # Create new
            new_keyword = Keyword(
                keyword=kw_data["keyword"],
                search_volume=kw_data["search_volume"],
                category=kw_data["category"],
                designs_allocated=kw_data["designs_allocated"],
                trend_score=kw_data["trend_score"]
            )
            db.add(new_keyword)
            stored_keywords.append(new_keyword)
            total_designs += kw_data["designs_allocated"]
        
        db.commit()
        
        # Refresh to get IDs
        for kw in stored_keywords:
            db.refresh(kw)
        
        return {
            "success": True,
            "message": f"Added {len(stored_keywords)} keywords",
            "keywords_stored": len(stored_keywords),
            "potential_listings": total_designs * 8,  # 8 styles
            "keywords": stored_keywords
        }
        
    except Exception as e:
        logger.error(f"❌ Error adding manual keywords: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-import", response_model=TrendResponse)
async def batch_import_keywords(
    batch: BatchKeywordImport,
    db: Session = Depends(get_db)
):
    """Import multiple keywords at once with full control"""
    try:
        logger.info(f"📦 Batch import: {len(batch.keywords)} keywords")
        
        stored_keywords = []
        total_designs = 0
        
        for kw_data in batch.keywords:
            # Check if exists
            existing = db.query(Keyword).filter(
                Keyword.keyword == kw_data.keyword.lower()
            ).first()
            
            if existing:
                logger.info(f"⏭️  Keyword exists: {kw_data.keyword}")
                stored_keywords.append(existing)
                total_designs += existing.designs_allocated
                continue
            
            # Calculate designs if not provided
            designs = kw_data.designs_allocated
            if designs is None:
                volume = kw_data.search_volume or 20000
                if volume >= 150000:
                    designs = 250
                elif volume >= 100000:
                    designs = 200
                elif volume >= 50000:
                    designs = 150
                elif volume >= 30000:
                    designs = 100
                elif volume >= 20000:
                    designs = 75
                elif volume >= 10000:
                    designs = 50
                else:
                    designs = 30
            
            # Create keyword
            new_keyword = Keyword(
                keyword=kw_data.keyword.lower(),
                search_volume=kw_data.search_volume or 20000,
                category=kw_data.category,
                designs_allocated=designs,
                trend_score=kw_data.trend_score
            )
            db.add(new_keyword)
            stored_keywords.append(new_keyword)
            total_designs += designs
        
        db.commit()
        
        # Refresh
        for kw in stored_keywords:
            db.refresh(kw)
        
        return {
            "success": True,
            "message": f"Imported {len(stored_keywords)} keywords",
            "keywords_stored": len(stored_keywords),
            "potential_listings": total_designs * 8,
            "keywords": stored_keywords
        }
        
    except Exception as e:
        logger.error(f"❌ Batch import error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[KeywordResponse])
async def get_trends(
    category: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get stored keywords with optional category filter"""
    query = db.query(Keyword)
    
    if category:
        query = query.filter(Keyword.category == category)
    
    keywords = query.order_by(Keyword.search_volume.desc()).limit(limit).all()
    return keywords

@router.get("/stats")
async def get_trend_stats(db: Session = Depends(get_db)):
    """Get statistics about stored keywords"""
    total = db.query(Keyword).count()
    
    # Category breakdown
    categories = db.query(
        Keyword.category,
        db.func.count(Keyword.id).label("count"),
        db.func.sum(Keyword.designs_allocated).label("designs")
    ).group_by(Keyword.category).all()
    
    return {
        "total_keywords": total,
        "categories": [
            {
                "category": cat,
                "count": count,
                "designs": designs or 0
            }
            for cat, count, designs in categories
        ],
        "total_potential_listings": db.query(
            db.func.sum(Keyword.designs_allocated)
        ).scalar() * 8 if total > 0 else 0
    }

@router.delete("/{keyword_id}")
async def delete_keyword(keyword_id: int, db: Session = Depends(get_db)):
    """Delete a keyword"""
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    
    db.delete(keyword)
    db.commit()
    
    return {"success": True, "message": f"Deleted keyword: {keyword.keyword}"}
