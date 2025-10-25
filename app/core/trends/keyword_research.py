"""
Keyword Research API
Provides access to Google Keyword Planner data
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from loguru import logger

from app.core.trends.keyword_planner import get_keyword_planner

router = APIRouter()


class KeywordRequest(BaseModel):
    keywords: List[str]
    country_code: str = "GB"


@router.post("/analyze")
async def analyze_keywords(request: KeywordRequest):
    """
    Analyze keywords using Google Keyword Planner
    
    Returns search volume, competition, and CPC data
    """
    try:
        analyzer = get_keyword_planner()
        
        if not analyzer.is_available():
            raise HTTPException(
                status_code=503,
                detail="Google Keyword Planner not configured. Please set up Google Ads API credentials."
            )
        
        logger.info(f"📊 Analyzing {len(request.keywords)} keywords with Google Keyword Planner")
        
        results = await analyzer.analyze_trend_keywords(
            keywords=request.keywords,
            country_code=request.country_code
        )
        
        return {
            "success": True,
            "message": f"Analyzed {results['total_keywords_analyzed']} keywords",
            **results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing keywords: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/volume")
async def get_keyword_volume(
    keyword: str = Query(..., description="Keyword to check"),
    country_code: str = Query("GB", description="Country code (GB, US, CA, AU)")
):
    """
    Get search volume for a single keyword
    """
    try:
        analyzer = get_keyword_planner()
        
        if not analyzer.is_available():
            raise HTTPException(
                status_code=503,
                detail="Google Keyword Planner not configured"
            )
        
        results = await analyzer.get_keyword_volume(
            keywords=[keyword],
            country_code=country_code
        )
        
        if not results:
            return {
                "keyword": keyword,
                "avg_monthly_searches": 0,
                "competition": "UNKNOWN",
                "message": "No data available"
            }
        
        return results[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting volume: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_keyword_planner_status():
    """
    Check if Google Keyword Planner is configured and available
    """
    analyzer = get_keyword_planner()
    
    return {
        "available": analyzer.is_available(),
        "configured": analyzer.client is not None,
        "customer_id_set": analyzer.customer_id is not None,
        "message": "Ready" if analyzer.is_available() else "Not configured. Add Google Ads API credentials to .env"
    }
