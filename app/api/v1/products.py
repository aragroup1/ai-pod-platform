from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
from loguru import logger
import json
from datetime import datetime, timedelta

from app.database import DatabasePool
from app.dependencies import get_db_pool
from app.utils.s3_storage import get_storage_manager

router = APIRouter()


@router.get("/image/{artwork_id}")
async def get_product_image(
    artwork_id: int,
    expiration: int = Query(3600, ge=300, le=86400),  # 5 min to 24 hours
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    Get pre-signed URL for product image from S3
    
    Args:
        artwork_id: Artwork ID
        expiration: URL expiration in seconds (default: 1 hour)
    
    Returns:
        Temporary URL to access the image from S3
    """
    try:
        # Get artwork from database (image_url contains S3 key)
        artwork = await db_pool.fetchrow(
            "SELECT image_url FROM artwork WHERE id = $1",
            artwork_id
        )
        
        if not artwork:
            raise HTTPException(status_code=404, detail="Artwork not found")
        
        s3_key = artwork['image_url']
        
        if not s3_key:
            raise HTTPException(status_code=404, detail="No image available for this artwork")
        
        # Generate pre-signed URL from S3
        storage = get_storage_manager()
        url = storage.get_presigned_url(s3_key, expiration=expiration)
        
        if not url:
            raise HTTPException(status_code=500, detail="Failed to generate image URL")
        
        expires_at = datetime.utcnow() + timedelta(seconds=expiration)
        
        logger.info(f"✅ Generated pre-signed URL for artwork {artwork_id}")
        
        return {
            "url": url,
            "expires_in_seconds": expiration,
            "expires_at": expires_at.isoformat(),
            "artwork_id": artwork_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product image: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch-images")
async def get_batch_product_images(
    artwork_ids: str = Query(..., description="Comma-separated artwork IDs"),
    expiration: int = Query(3600, ge=300, le=86400),
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    Get pre-signed URLs for multiple product images at once
    
    Args:
        artwork_ids: Comma-separated list of artwork IDs (e.g., "1,2,3,4,5")
        expiration: URL expiration in seconds
        
    Returns:
        Dict mapping artwork_id to pre-signed URL
    """
    try:
        # Parse artwork IDs
        ids = [int(id.strip()) for id in artwork_ids.split(',')]
        
        if len(ids) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 artwork IDs per request")
        
        # Get all artworks
        artworks = await db_pool.fetch(
            "SELECT id, image_url FROM artwork WHERE id = ANY($1)",
            ids
        )
        
        if not artworks:
            return {"images": {}, "message": "No artworks found"}
        
        # Generate pre-signed URLs
        storage = get_storage_manager()
        expires_at = datetime.utcnow() + timedelta(seconds=expiration)
        
        images = {}
        for artwork in artworks:
            if artwork['image_url']:
                url = storage.get_presigned_url(artwork['image_url'], expiration=expiration)
                if url:
                    images[artwork['id']] = {
                        "url": url,
                        "expires_at": expires_at.isoformat()
                    }
        
        logger.info(f"✅ Generated {len(images)} pre-signed URLs")
        
        return {
            "images": images,
            "expires_in_seconds": expiration,
            "count": len(images)
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid artwork IDs format")
    except Exception as e:
        logger.error(f"Error getting batch images: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def get_products(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    include_images: bool = Query(default=True, description="Include pre-signed image URLs"),
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    Get products with optional filters and S3 image URLs
    
    Query Parameters:
        - limit: Number of products to return (1-100)
        - offset: Pagination offset
        - status: Filter by status (active, draft, approved, rejected)
        - category: Filter by category
        - search: Search in title and description
        - include_images: If true, includes pre-signed S3 URLs
    """
    try:
        logger.info(f"Fetching products: limit={limit}, offset={offset}, status={status}, include_images={include_images}")
        
        # Build query with filters
        conditions = []
        params = []
        param_count = 0
        
        if status:
            param_count += 1
            conditions.append(f"p.status = ${param_count}::product_status")
            params.append(status)
        
        if category:
            param_count += 1
            conditions.append(f"p.category = ${param_count}")
            params.append(category)
        
        if search:
            param_count += 1
            conditions.append(f"(p.title ILIKE ${param_count} OR p.description ILIKE ${param_count})")
            params.append(f"%{search}%")
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        # Add limit and offset
        param_count += 1
        limit_param = f"${param_count}"
        params.append(limit)
        
        param_count += 1
        offset_param = f"${param_count}"
        params.append(offset)
        
        query = f"""
            SELECT 
                p.id, p.sku, p.title, p.description, 
                p.base_price, p.status, p.category, p.tags,
                p.created_at,
                a.id as artwork_id,
                a.image_url as s3_key,
                a.style, a.provider,
                a.quality_score, a.generation_cost,
                a.metadata
            FROM products p
            LEFT JOIN artwork a ON p.artwork_id = a.id
            {where_clause}
            ORDER BY p.created_at DESC
            LIMIT {limit_param} OFFSET {offset_param}
        """
        
        products = await db_pool.fetch(query, *params)
        
        # Process products and optionally add S3 URLs
        products_list = []
        storage = get_storage_manager() if include_images else None
        
        for p in products:
            try:
                # Parse metadata
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
                        "s3_key": p["s3_key"],
                        "style": p["style"],
                        "provider": p["provider"],
                        "quality_score": float(p["quality_score"]) if p["quality_score"] else 0,
                        "generation_cost": float(p["generation_cost"]) if p["generation_cost"] else 0,
                        "model_used": metadata.get("model_key") if isinstance(metadata, dict) else None
                    }
                    
                    # Add pre-signed URL if requested
                    if include_images and storage and p["s3_key"]:
                        try:
                            presigned_url = storage.get_presigned_url(p["s3_key"], expiration=3600)
                            if presigned_url:
                                artwork["image_url"] = presigned_url
                                artwork["image_expires_at"] = (datetime.utcnow() + timedelta(seconds=3600)).isoformat()
                        except Exception as img_error:
                            logger.warning(f"Failed to generate pre-signed URL for {p['s3_key']}: {img_error}")
                            artwork["image_url"] = None
                
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
                    "created_at": p["created_at"].isoformat() if p["created_at"] else None
                }
                
                products_list.append(product_obj)
                
            except Exception as e:
                logger.error(f"Error processing product {p['id']}: {e}")
                continue
        
        # Get total count for pagination
        count_query = f"""
            SELECT COUNT(*) 
            FROM products p
            LEFT JOIN artwork a ON p.artwork_id = a.id
            {where_clause}
        """
        total_count = await db_pool.fetchval(count_query, *params[:-2]) if params[:-2] else await db_pool.fetchval(count_query)
        
        logger.info(f"Successfully fetched {len(products_list)} products (total: {total_count})")
        
        return {
            "products": products_list,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count
        }
        
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{product_id}")
async def get_product(
    product_id: int,
    include_image: bool = Query(default=True, description="Include pre-signed image URL"),
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Get a single product by ID with optional S3 image URL"""
    try:
        product = await db_pool.fetchrow(
            """
            SELECT 
                p.id, p.sku, p.title, p.description, 
                p.base_price, p.status, p.category, p.tags,
                p.created_at,
                a.id as artwork_id,
                a.image_url as s3_key,
                a.style, a.provider,
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
                "s3_key": product["s3_key"],
                "style": product["style"],
                "provider": product["provider"],
                "quality_score": float(product["quality_score"]) if product["quality_score"] else 0,
                "generation_cost": float(product["generation_cost"]) if product["generation_cost"] else 0,
                "model_used": metadata.get("model_key") if isinstance(metadata, dict) else None
            }
            
            # Add pre-signed URL if requested
            if include_image and product["s3_key"]:
                storage = get_storage_manager()
                presigned_url = storage.get_presigned_url(product["s3_key"], expiration=3600)
                if presigned_url:
                    artwork["image_url"] = presigned_url
                    artwork["image_expires_at"] = (datetime.utcnow() + timedelta(seconds=3600)).isoformat()
        
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
            "created_at": product["created_at"].isoformat() if product["created_at"] else None
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
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8::product_status)
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
        
        logger.info(f"✅ Product created: {product_id}")
        
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
                tags = COALESCE($6, tags)
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
        
        logger.info(f"✅ Product updated: {product_id}")
        
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
    delete_image: bool = Query(default=False, description="Also delete S3 image"),
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Delete a product and optionally its S3 image"""
    try:
        # Get product with artwork info
        product = await db_pool.fetchrow(
            """
            SELECT p.id, a.image_url as s3_key
            FROM products p
            LEFT JOIN artwork a ON p.artwork_id = a.id
            WHERE p.id = $1
            """,
            product_id
        )
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Delete from S3 if requested
        if delete_image and product["s3_key"]:
            storage = get_storage_manager()
            try:
                storage.delete_image(product["s3_key"])
                logger.info(f"✅ Deleted S3 image: {product['s3_key']}")
            except Exception as s3_error:
                logger.warning(f"Failed to delete S3 image: {s3_error}")
        
        # Delete product from database
        await db_pool.execute(
            "DELETE FROM products WHERE id = $1",
            product_id
        )
        
        logger.info(f"✅ Product deleted: {product_id}")
        
        return {
            "id": product_id,
            "message": "Product deleted successfully",
            "image_deleted": delete_image and product["s3_key"] is not None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
async def get_product_stats(
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Get product statistics"""
    try:
        stats = await db_pool.fetchrow(
            """
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'active') as active,
                COUNT(*) FILTER (WHERE status = 'draft') as draft,
                COUNT(*) FILTER (WHERE status = 'approved') as approved,
                COUNT(*) FILTER (WHERE status = 'rejected') as rejected,
                AVG(base_price) as avg_price,
                COUNT(DISTINCT category) as total_categories
            FROM products
            """
        )
        
        return {
            "total_products": stats["total"],
            "by_status": {
                "active": stats["active"],
                "draft": stats["draft"],
                "approved": stats["approved"],
                "rejected": stats["rejected"]
            },
            "avg_price": float(stats["avg_price"]) if stats["avg_price"] else 0,
            "total_categories": stats["total_categories"]
        }
        
    except Exception as e:
        logger.error(f"Error fetching product stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
