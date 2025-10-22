from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Optional
from loguru import logger

from app.database import DatabasePool
from app.dependencies import get_db_pool
from app.core.products.generator import ProductGenerator

router = APIRouter()


class GenerateRequest(BaseModel):
    trend_id: int
    styles: Optional[List[str]] = None
    upscale: bool = False


class BatchGenerateRequest(BaseModel):
    limit: int = 10
    min_trend_score: float = 6.0
    upscale: bool = False
    testing_mode: bool = True  # Start with testing mode


@router.post("/generate")
async def generate_products_from_trend(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    Generate products from a single trend
    Runs in background
    """
    try:
        generator = ProductGenerator(db_pool, testing_mode=False)
        
        background_tasks.add_task(
            generator.generate_products_from_trend,
            trend_id=request.trend_id,
            styles=request.styles,
            upscale=request.upscale
        )
        
        return {
            "message": "Product generation started",
            "trend_id": request.trend_id,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error starting generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-generate")
async def batch_generate_products(
    request: BatchGenerateRequest,
    background_tasks: BackgroundTasks,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    Generate products for multiple trends
    This will create LIMIT × 8 products (8 styles per trend)
    """
    try:
        generator = ProductGenerator(
            db_pool,
            testing_mode=request.testing_mode
        )
        
        background_tasks.add_task(
            generator.batch_generate_from_trends,
            limit=request.limit,
            min_trend_score=request.min_trend_score,
            upscale=request.upscale
        )
        
        expected_products = request.limit * 8  # 8 styles per trend
        
        return {
            "message": "Batch generation started",
            "expected_products": expected_products,
            "trends_to_process": request.limit,
            "testing_mode": request.testing_mode,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error starting batch generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_generation_status(db_pool: DatabasePool = Depends(get_db_pool)):
    """Get statistics about generated products"""
    try:
        stats = await db_pool.fetchrow(
            """
            SELECT 
                COUNT(DISTINCT p.id) as total_products,
                COUNT(DISTINCT a.trend_id) as trends_with_products,
                COUNT(DISTINCT a.id) as total_artwork
            FROM products p
            LEFT JOIN artwork a ON p.artwork_id = a.id
            """
        )
        
        trends_without = await db_pool.fetchval(
            """
            SELECT COUNT(*)
            FROM trends t
            LEFT JOIN artwork a ON a.trend_id = t.id
            WHERE a.id IS NULL
            AND t.trend_score >= 6.0
            """
        )
        
        return {
            "total_products": stats['total_products'],
            "trends_with_products": stats['trends_with_products'],
            "total_artwork": stats['total_artwork'],
            "trends_awaiting_generation": trends_without
        }
        
    except Exception as e:
        logger.error(f"Error getting generation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
