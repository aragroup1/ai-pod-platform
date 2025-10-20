from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from loguru import logger

from app.database import DatabasePool
from app.dependencies import get_db_pool

router = APIRouter()

@router.get("")  # <-- No trailing slash!
async def get_products(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    Get a list of products with optional filtering.
    """
    logger.info(f"Fetching products with limit={limit}, offset={offset}, status={status}")
    try:
        # Build query with optional status filter
        if status:
            query = """
                SELECT id, title, sku, status, base_price 
                FROM products 
                WHERE status = $1::product_status
                ORDER BY created_at DESC 
                LIMIT $2 OFFSET $3
            """
            results = await db_pool.fetch(query, status, limit, offset)
        else:
            query = """
                SELECT id, title, sku, status, base_price 
                FROM products 
                ORDER BY created_at DESC 
                LIMIT $1 OFFSET $2
            """
            results = await db_pool.fetch(query, limit, offset)
        
        products_list = [
            {
                "id": row["id"],
                "title": row["title"],
                "sku": row["sku"],
                "status": row["status"],
                "base_price": float(row["base_price"]) if row["base_price"] else 0
            }
            for row in results
        ]

        return {"products": products_list}
    
    except Exception as e:
        logger.exception(f"Error fetching products: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Could not fetch products from the database: {str(e)}"
        )
