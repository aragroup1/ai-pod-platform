from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from loguru import logger

from app.core.analytics import AnalyticsEngine

router = APIRouter()
analytics_engine = AnalyticsEngine()

@router.get("/dashboard")
async def get_dashboard_metrics(days: int = Query(30, ge=1, le=365)):
    """
    Provides key performance indicators for the main dashboard.
    This is the primary endpoint for the frontend dashboard's overview.
    """
    logger.info(f"Fetching dashboard metrics for the last {days} days.")
    try:
        metrics = await analytics_engine.get_dashboard_metrics(days=days)
        if metrics is None:
            logger.warning("Analytics engine returned no data.")
            # Return a default structure to prevent frontend errors
            return {
                "revenue": 0,
                "orders": 0,
                "products": 0,
                "trends": 0,
                "profit": 0,
                "avg_order_value": 0
            }
        return metrics
    except Exception as e:
        logger.exception(f"Error fetching dashboard metrics: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Could not calculate dashboard metrics."
        )

# You can add more detailed analytics endpoints here later
@router.get("/revenue-over-time")
async def get_revenue_over_time():
    # Placeholder for a future chart endpoint
    return {"data": "coming soon"}
