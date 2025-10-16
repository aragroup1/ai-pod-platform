from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from loguru import logger

from app.database import DatabasePool # <--- IMPORT THIS
from app.dependencies import get_db_pool # <--- IMPORT THIS

router = APIRouter()

@router.get(
    "/",
    dependencies=[Depends(get_db_pool)] # <--- ADD THIS
)
async def get_products(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    db_pool: DatabasePool = Depends(get_db_pool) # <--- ADD THIS to get the pool
):
    """
    Get a list of products with optional filtering.
    """
    logger.info(f"Fetching products with limit={limit}, offset={offset}, status={status}")
    try:
        # We get db_pool from the dependency now
        results = await db_pool.fetch("SELECT id, title, sku, status, base_price FROM products ORDER BY created_at DESC LIMIT $1 OFFSET $2", limit, offset)
        
        products_list = [
            {**dict(row), "base_price": float(row["base_price"])}
            for row in results
        ]

        return {"products": products_list}
    
    except Exception as e:
        logger.exception(f"Error fetching products: {e}")
        raise HTTPException(
            status_code=500,
            detail="Could not fetch products from the database."
        )
