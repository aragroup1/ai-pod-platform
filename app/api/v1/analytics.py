from fastapi import APIRouter
from app.database import db_pool

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard_metrics():
    """Get dashboard metrics"""
    return {
        "revenue": 0,
        "orders": 0,
        "products": 0
    }
