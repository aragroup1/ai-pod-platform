from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from loguru import logger

from app.core.analytics import AnalyticsEngine
from app.dependencies import get_db_pool
from app.database import DatabasePool

router = APIRouter()

# REMOVE THIS LINE - it's causing the error:
# analytics_engine = AnalyticsEngine()

@router.get("/dashboard")
async def get_dashboard_metrics(
    days: int = Query(30, ge=1, le=365),
    db_pool = Depends(get_db_pool)
):
    """
    Provides key performance indicators for the main dashboard.
    """
    logger.info(f"Fetching dashboard metrics for the last {days} days.")
    try:
        # Create the engine here with db_pool
        analytics_engine = AnalyticsEngine(db_pool)
        metrics = await analytics_engine.get_dashboard_metrics(days=days)
        return metrics
    except Exception as e:
        logger.exception(f"Error fetching dashboard metrics: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Could not calculate dashboard metrics."
        )
