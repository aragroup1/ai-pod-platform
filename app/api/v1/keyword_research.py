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
    
    Example request:
    {
        "keywords": ["wall art", "canvas prints", "vintage posters"],
        "country_code": "GB"
    }
    """
    try:
        analyzer = get_keyword_planner()
        
        if not analyzer.is_available():
            status = analyzer.get_setup_status()
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Google Keyword Planner not configured",
                    "setup_status": status,
                    "help": "Add Google Ads API credentials to Railway environment variables"
                }
            )
        
        logger.info(f"📊 Analyzing {len(request.keywords)} keywords with Google Keyword Planner")
        
        results = await analyzer.analyze_trend_keywords(
            keywords=request.keywords,
            country_code=request.country_code
        )
        
        return {
            "success": True,
            "message": f"Analyzed {results['total_keywords_analyzed']} keywords",
            "country": request.country_code,
            "total_volume": results['total_volume'],
            "avg_volume_per_keyword": results['avg_volume_per_keyword'],
            "avg_competition": results['avg_competition'],
            "keywords": results['keywords'],
            "high_volume_keywords": results['high_volume_keywords'],
            "low_competition_keywords": results['low_competition_keywords']
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
    
    Example: /api/v1/keyword-research/volume?keyword=wall%20art&country_code=GB
    """
    try:
        analyzer = get_keyword_planner()
        
        if not analyzer.is_available():
            raise HTTPException(
                status_code=503,
                detail="Google Keyword Planner not configured. Add credentials to Railway."
            )
        
        logger.info(f"📊 Getting volume for keyword: {keyword}")
        
        results = await analyzer.get_keyword_volume(
            keywords=[keyword],
            country_code=country_code
        )
        
        if not results:
            return {
                "keyword": keyword,
                "avg_monthly_searches": 0,
                "competition": "UNKNOWN",
                "message": "No data available for this keyword"
            }
        
        return {
            "success": True,
            "keyword": results[0]['keyword'],
            "avg_monthly_searches": results[0]['avg_monthly_searches'],
            "competition": results[0]['competition'],
            "competition_index": results[0]['competition_index'],
            "low_top_of_page_bid": results[0]['low_top_of_page_bid'],
            "high_top_of_page_bid": results[0]['high_top_of_page_bid'],
            "country": country_code
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting volume: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_analyze_keywords(
    keywords: List[str],
    country_code: str = "GB"
):
    """
    Analyze multiple keywords in batch
    
    Example request body:
    ["wall art", "canvas prints", "vintage posters", "modern art", "abstract prints"]
    """
    try:
        analyzer = get_keyword_planner()
        
        if not analyzer.is_available():
            raise HTTPException(
                status_code=503,
                detail="Google Keyword Planner not configured"
            )
        
        logger.info(f"📊 Batch analyzing {len(keywords)} keywords")
        
        results = await analyzer.get_keyword_volume(
            keywords=keywords,
            country_code=country_code
        )
        
        return {
            "success": True,
            "total_keywords": len(results),
            "country": country_code,
            "keywords": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_keyword_planner_status():
    """
    Check if Google Keyword Planner is configured and available
    Returns detailed setup status for troubleshooting
    
    Example: /api/v1/keyword-research/status
    """
    analyzer = get_keyword_planner()
    status = analyzer.get_setup_status()
    
    # Add helpful message
    if not status['ready']:
        missing = []
        if not status['developer_token_set']:
            missing.append('GOOGLE_ADS_DEVELOPER_TOKEN')
        if not status['client_id_set']:
            missing.append('GOOGLE_ADS_CLIENT_ID')
        if not status['client_secret_set']:
            missing.append('GOOGLE_ADS_CLIENT_SECRET')
        if not status['refresh_token_set']:
            missing.append('GOOGLE_ADS_REFRESH_TOKEN')
        if not status['customer_id_set']:
            missing.append('GOOGLE_ADS_CUSTOMER_ID')
        
        status['missing_env_vars'] = missing
        status['help'] = {
            "message": "Follow the OAuth Playground method to get your refresh token",
            "steps": [
                "1. Go to https://developers.google.com/oauthplayground",
                "2. Click settings icon, enable 'Use your own OAuth credentials'",
                "3. Enter your Client ID and Client Secret",
                "4. Select Google Ads API scope: https://www.googleapis.com/auth/adwords",
                "5. Click 'Authorize APIs' and sign in",
                "6. Click 'Exchange authorization code for tokens'",
                "7. Copy the refresh_token and add to Railway"
            ],
            "your_credentials": {
                "client_id": "437435525064-f4lkgsme096t4jlop826foog02j6d69s.apps.googleusercontent.com",
                "client_secret": "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",
                "developer_token": "tbWEP6dGtUdVRGOBFl2Wzg",
                "customer_id": "9735349933"
            }
        }
    else:
        status['message'] = "✅ Google Keyword Planner is ready!"
    
    return status


@router.get("/test")
async def test_keyword_planner():
    """
    Quick test endpoint to verify Google Keyword Planner is working
    Tests with a simple keyword: "wall art"
    """
    try:
        analyzer = get_keyword_planner()
        
        if not analyzer.is_available():
            return {
                "success": False,
                "message": "Google Keyword Planner not configured",
                "status": analyzer.get_setup_status()
            }
        
        # Test with a simple keyword
        results = await analyzer.get_keyword_volume(
            keywords=["wall art"],
            country_code="GB"
        )
        
        if results:
            return {
                "success": True,
                "message": "✅ Google Keyword Planner is working!",
                "test_keyword": "wall art",
                "avg_monthly_searches": results[0]['avg_monthly_searches'],
                "competition": results[0]['competition']
            }
        else:
            return {
                "success": False,
                "message": "API call succeeded but no data returned"
            }
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return {
            "success": False,
            "message": f"Test failed: {str(e)}"
        }
