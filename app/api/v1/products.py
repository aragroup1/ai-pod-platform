from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from loguru import logger

from app.database import db_pool

router = APIRouter()

@router.get("/")
async def get_products(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None
):
    """
    Get a list of products with optional filtering.
    This endpoint is used by the dashboard to show recent products.
    """
    logger.info(f"Fetching products with limit={limit}, offset={offset}, status={status}")
    try:
        base_query = """
            SELECT id, title, sku, status, base_price 
            FROM products
        """
        conditions = []
        params = []
        
        if status:
            params.append(status)
            conditions.append(f"status = ${len(params)}")

        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)

        params.append(limit)
        base_query += f" ORDER BY created_at DESC LIMIT ${len(params)}"
        params.append(offset)
        base_query += f" OFFSET ${len(params)}"

        results = await db_pool.fetch(base_query, *params)
        
        # Ensure base_price is a float for JSON compatibility
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
