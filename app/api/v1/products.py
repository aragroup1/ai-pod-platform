from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from loguru import logger

from app.database import DatabasePool
from app.dependencies import get_db_pool

router = APIRouter()

@router.get("/")
async def get_products(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    Get a list of products with their artwork images
    """
    logger.info(f"Fetching products with limit={limit}, offset={offset}, status={status}")
    try:
        # Build query with optional status filter and JOIN artwork
        if status:
            query = """
                SELECT 
                    p.id, p.title, p.sku, p.status, p.base_price, p.description,
                    p.created_at, p.category, p.tags,
                    a.image_url, a.style, a.provider, a.quality_score,
                    a.metadata as artwork_metadata
                FROM products p
                LEFT JOIN artwork a ON p.artwork_id = a.id
                WHERE p.status = $1::product_status
                ORDER BY p.created_at DESC 
                LIMIT $2 OFFSET $3
            """
            results = await db_pool.fetch(query, status, limit, offset)
        else:
            query = """
                SELECT 
                    p.id, p.title, p.sku, p.status, p.base_price, p.description,
                    p.created_at, p.category, p.tags,
                    a.image_url, a.style, a.provider, a.quality_score,
                    a.metadata as artwork_metadata
                FROM products p
                LEFT JOIN artwork a ON p.artwork_id = a.id
                ORDER BY p.created_at DESC 
                LIMIT $1 OFFSET $2
            """
            results = await db_pool.fetch(query, limit, offset)
        
        products_list = [
            {
                "id": row["id"],
                "title": row["title"],
                "sku": row["sku"],
                "status": row["status"],
                "base_price": float(row["base_price"]) if row["base_price"] else 0,
                "description": row["description"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "category": row["category"],
                "tags": row["tags"],
                "artwork": {
                    "image_url": row["image_url"],
                    "style": row["style"],
                    "provider": row["provider"],
                    "quality_score": float(row["quality_score"]) if row["quality_score"] else 0,
                    "model_used": row["artwork_metadata"].get("model_key") if row["artwork_metadata"] else None
                } if row["image_url"] else None
            }
            for row in results
        ]

        return {"products": products_list, "total": len(products_list)}
    
    except Exception as e:
        logger.exception(f"Error fetching products: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Could not fetch products from the database: {str(e)}"
        )


@router.get("/{product_id}")
async def get_product_detail(
    product_id: int,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    Get detailed information about a single product including artwork
    """
    try:
        query = """
            SELECT 
                p.id, p.title, p.sku, p.status, p.base_price, p.description,
                p.created_at, p.category, p.tags, p.metadata as product_metadata,
                a.id as artwork_id, a.image_url, a.style, a.prompt, 
                a.provider, a.quality_score, a.generation_cost,
                a.metadata as artwork_metadata,
                t.keyword as trend_keyword, t.trend_score
            FROM products p
            LEFT JOIN artwork a ON p.artwork_id = a.id
            LEFT JOIN trends t ON a.trend_id = t.id
            WHERE p.id = $1
        """
        
        result = await db_pool.fetchrow(query, product_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return {
            "id": result["id"],
            "title": result["title"],
            "sku": result["sku"],
            "status": result["status"],
            "base_price": float(result["base_price"]) if result["base_price"] else 0,
            "description": result["description"],
            "created_at": result["created_at"].isoformat() if result["created_at"] else None,
            "category": result["category"],
            "tags": result["tags"],
            "artwork": {
                "id": result["artwork_id"],
                "image_url": result["image_url"],
                "style": result["style"],
                "prompt": result["prompt"],
                "provider": result["provider"],
                "quality_score": float(result["quality_score"]) if result["quality_score"] else 0,
                "generation_cost": float(result["generation_cost"]) if result["generation_cost"] else 0,
                "model_used": result["artwork_metadata"].get("model_key") if result["artwork_metadata"] else None,
                "selection_reasoning": result["artwork_metadata"].get("selection_reasoning") if result["artwork_metadata"] else None
            } if result["image_url"] else None,
            "trend": {
                "keyword": result["trend_keyword"],
                "trend_score": float(result["trend_score"]) if result["trend_score"] else 0
            } if result["trend_keyword"] else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error fetching product detail: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Could not fetch product details: {str(e)}"
        )


@router.get("/gallery/all")
async def get_product_gallery(
    limit: int = Query(50, ge=1, le=200),
    style: Optional[str] = None,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    Get a gallery view of all products with their images
    Optimized for displaying image thumbnails
    """
    try:
        if style:
            query = """
                SELECT 
                    p.id, p.title, p.base_price,
                    a.image_url, a.style, a.quality_score
                FROM products p
                INNER JOIN artwork a ON p.artwork_id = a.id
                WHERE p.status = 'active' AND a.style = $1
                ORDER BY p.created_at DESC
                LIMIT $2
            """
            results = await db_pool.fetch(query, style, limit)
        else:
            query = """
                SELECT 
                    p.id, p.title, p.base_price,
                    a.image_url, a.style, a.quality_score
                FROM products p
                INNER JOIN artwork a ON p.artwork_id = a.id
                WHERE p.status = 'active'
                ORDER BY p.created_at DESC
                LIMIT $1
            """
            results = await db_pool.fetch(query, limit)
        
        gallery = [
            {
                "id": row["id"],
                "title": row["title"],
                "price": float(row["base_price"]) if row["base_price"] else 0,
                "image_url": row["image_url"],
                "style": row["style"],
                "quality_score": float(row["quality_score"]) if row["quality_score"] else 0
            }
            for row in results
        ]
        
        return {
            "gallery": gallery,
            "total": len(gallery),
            "style_filter": style
        }
        
    except Exception as e:
        logger.exception(f"Error fetching gallery: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Could not fetch gallery: {str(e)}"
        )
