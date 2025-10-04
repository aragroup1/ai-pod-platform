from fastapi import APIRouter
from app.database import db_pool

router = APIRouter()

@router.get("/")
async def get_platforms():
    """Get platform integrations"""
    return {"platforms": ["shopify", "etsy", "amazon"]}
