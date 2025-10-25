from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
from loguru import logger
import json

from app.database import DatabasePool
from app.dependencies import get_db_pool

router = APIRouter()


@router.get("/")
async def get_products(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    Get products with artwork
    
    ✅ FIXED: Properly handles JSON metadata field
    """
    try:
        logger.info(f"Fetching products with limit={limit}, offset={offset}, status={status}")
        
        # Build query based on status filter
        if status:
            query = """
                SELECT 
                    p.id, p.sku, p.title, p.description, 
                    p.base_price, p.status, p.category, p.tags,
                    p.created_at, p.updated_at,
                    a.id as artwork_id,
                    a.image_url, a.style, a.provider,
                    a.quality_score, a.generation_cost,
                    a.metadata
                FROM products p
                LEFT JOIN artwork a ON p.artwork_id = a.id
                WHERE p.status = $1::product_status
                ORDER BY p.created_at DESC
                LIMIT $2 OFFSET $3
            """
            products = await db_pool.fetch(query, status, limit, offset)
        else:
            query = """
                SELECT 
                    p.id, p.sku, p.title, p.description, 
                    p.base_price, p.status, p.category, p.tags,
                    p.created_at, p.updated_at,
                    a.id as artwork_id,
                    a.image_url, a.style, a.provider,
                    a.quality_score, a.generation_cost,
                    a.metadata
                FROM products p
                LEFT JOIN artwork a ON p.artwork_id = a.id
                ORDER BY p.created_at DESC
                LIMIT $1 OFFSET $2
            """
            products = await db_pool.fetch(query, limit, offset)
        
        # ✅ CRITICAL FIX: Properly serialize products with JSON metadata
        products_list = []
        for p in products:
            try:
                # Parse metadata if it's a JSON string
                metadata = p["metadata"]
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except json.JSONDecodeError:
                        metadata = {}
                elif metadata is None:
                    metadata = {}
                
                # Build artwork object
                artwork = None
                if p["artwork_id"]:
                    artwork = {
                        "id": p["artwork_id"],
                        "image_url": p["image_url"],
                        "style": p["style"],
                        "provider": p["provider"],
                        "quality_score": float(p["quality_score"]) if p["quality_score"] else 0,
                        "generation_cost": float(p["generation_cost"]) if p["generation_cost"] else 0,
                        "model_used": metadata.get("model_key") if isinstance(metadata, dict) else None
                    }
                
                # Build product object
                product_obj = {
                    "id": p["id"],
                    "sku": p["sku"],
                    "title": p["title"],
                    "description": p["description"],
                    "base_price": float(p["base_price"]),
                    "status": p["status"],
                    "category": p["category"],
                    "tags": p["tags"],
                    "artwork": artwork,
                    "created_at": p["created_at"].isoformat() if p["created_at"] else None,
                    "updated_at": p["updated_at"].isoformat() if p["updated_at"] else None
                }
                
                products_list.append(product_obj)
                
            except Exception as e:
                logger.error(f"Error serializing product {p['id']}: {e}")
                # Skip this product but continue with others
                continue
        
        logger.info(f"Successfully fetched {len(products_list)} products")
        
        return {
            "products": products_list,
            "total": len(products_list),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{product_id}")
async def get_product(
    product_id: int,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Get a single product by ID"""
    try:
        product = await db_pool.fetchrow(
            """
            SELECT 
                p.id, p.sku, p.title, p.description, 
                p.base_price, p.status, p.category, p.tags,
                p.created_at, p.updated_at,
                a.id as artwork_id,
                a.image_url, a.style, a.provider,
                a.quality_score, a.generation_cost,
                a.metadata
            FROM products p
            LEFT JOIN artwork a ON p.artwork_id = a.id
            WHERE p.id = $1
            """,
            product_id
        )
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Parse metadata
        metadata = product["metadata"]
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                metadata = {}
        elif metadata is None:
            metadata = {}
        
        # Build artwork object
        artwork = None
        if product["artwork_id"]:
            artwork = {
                "id": product["artwork_id"],
                "image_url": product["image_url"],
                "style": product["style"],
                "provider": product["provider"],
                "quality_score": float(product["quality_score"]) if product["quality_score"] else 0,
                "generation_cost": float(product["generation_cost"]) if product["generation_cost"] else 0,
                "model_used": metadata.get("model_key") if isinstance(metadata, dict) else None
            }
        
        return {
            "id": product["id"],
            "sku": product["sku"],
            "title": product["title"],
            "description": product["description"],
            "base_price": float(product["base_price"]),
            "status": product["status"],
            "category": product["category"],
            "tags": product["tags"],
            "artwork": artwork,
            "created_at": product["created_at"].isoformat() if product["created_at"] else None,
            "updated_at": product["updated_at"].isoformat() if product["updated_at"] else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_product(
    product_data: dict,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Create a new product"""
    try:
        product_id = await db_pool.fetchval(
            """
            INSERT INTO products (
                sku, title, description, base_price,
                artwork_id, category, tags, status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
            """,
            product_data["sku"],
            product_data["title"],
            product_data.get("description", ""),
            product_data["base_price"],
            product_data.get("artwork_id"),
            product_data.get("category", "wall-art"),
            product_data.get("tags", []),
            product_data.get("status", "active")
        )
        
        logger.info(f"Product created: {product_id}")
        
        return {
            "id": product_id,
            "message": "Product created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{product_id}")
async def update_product(
    product_id: int,
    product_data: dict,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Update a product"""
    try:
        # Check if product exists
        exists = await db_pool.fetchval(
            "SELECT id FROM products WHERE id = $1",
            product_id
        )
        
        if not exists:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Update product
        await db_pool.execute(
            """
            UPDATE products
            SET title = COALESCE($1, title),
                description = COALESCE($2, description),
                base_price = COALESCE($3, base_price),
                status = COALESCE($4::product_status, status),
                category = COALESCE($5, category),
                tags = COALESCE($6, tags),
                updated_at = NOW()
            WHERE id = $7
            """,
            product_data.get("title"),
            product_data.get("description"),
            product_data.get("base_price"),
            product_data.get("status"),
            product_data.get("category"),
            product_data.get("tags"),
            product_id
        )
        
        logger.info(f"Product updated: {product_id}")
        
        return {
            "id": product_id,
            "message": "Product updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating product: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Delete a product"""
    try:
        # Check if product exists
        exists = await db_pool.fetchval(
            "SELECT id FROM products WHERE id = $1",
            product_id
        )
        
        if not exists:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Delete product
        await db_pool.execute(
            "DELETE FROM products WHERE id = $1",
            product_id
        )
        
        logger.info(f"Product deleted: {product_id}")
        
        return {
            "id": product_id,
            "message": "Product deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        raise HTTPException(status_code=500, detail=str(e))
