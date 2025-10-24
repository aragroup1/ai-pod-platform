from fastapi import APIRouter, Depends
from app.database import DatabasePool
from app.dependencies import get_db_pool

router = APIRouter()

@router.get("/")
async def get_platforms(db_pool: DatabasePool = Depends(get_db_pool)):
    """Get platform integrations"""
    return {"platforms": ["shopify", "etsy", "amazon"]}
