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
    expiration: int = Query(3600, ge=300, le=86400),
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Get pre-signed URL for product image from S3"""
    try:
        artwork = await db_pool.fetchrow(
            "SELECT image_url FROM artwork WHERE id = $1",
            artwork_id
        )
        
        if not artwork:
            raise HTTPException(status_code=404, detail="Artwork not found")
        
        s3_key = artwork['image_url']
        
        if not s3_key:
            raise HTTPException(status_code=404, detail="No image available for this artwork")
        
        storage = get_storage_manager()
        url = storage.get_presigned_url(s3_key, expiration=expiration)
        
        if not url:
            raise HTTPException(status_code=500, detail="Failed to generate image URL")
        
        return {"url": url, "expires_in": expiration}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product image: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve image")


@router.get("")
async def get_products(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Get list of products with optional filtering"""
    try:
        # FIXED: Use correct column names from your schema
        base_query = """
            SELECT 
                p.id,
                p.title,
                p.description,
                p.base_price,
                p.category,
                p.status,
                p.created_at,
                p.updated_at,
                p.metadata,
                a.id as artwork_id,
                a.image_url,
                a.prompt,
                a.style,
                a.provider
            FROM products p
            LEFT JOIN artwork a ON p.artwork_id = a.id
            WHERE 1=1
        """
        
        params = []
        param_index = 1
        
        # Add filters
        if category:
            base_query += f" AND p.category = ${param_index}"
            params.append(category)
            param_index += 1
        
        if min_price is not None:
            base_query += f" AND p.base_price >= ${param_index}"
            params.append(min_price)
            param_index += 1
        
        if max_price is not None:
            base_query += f" AND p.base_price <= ${param_index}"
            params.append(max_price)
            param_index += 1
        
        if search:
            base_query += f" AND (p.title ILIKE ${param_index} OR p.description ILIKE ${param_index})"
            params.append(f"%{search}%")
            param_index += 1
        
        # Add ordering and pagination
        base_query += f" ORDER BY p.created_at DESC LIMIT ${param_index} OFFSET ${param_index + 1}"
        params.extend([limit, offset])
        
        # Execute query
        rows = await db_pool.fetch(base_query, *params)
        
        # Get total count for pagination
        count_query = """
            SELECT COUNT(*) as total
            FROM products p
            WHERE 1=1
        """
        
        count_params = []
        count_param_index = 1
        
        if category:
            count_query += f" AND p.category = ${count_param_index}"
            count_params.append(category)
            count_param_index += 1
        
        if min_price is not None:
            count_query += f" AND p.base_price >= ${count_param_index}"
            count_params.append(min_price)
            count_param_index += 1
        
        if max_price is not None:
            count_query += f" AND p.base_price <= ${count_param_index}"
            count_params.append(max_price)
            count_param_index += 1
        
        if search:
            count_query += f" AND (p.title ILIKE ${count_param_index} OR p.description ILIKE ${count_param_index})"
            count_params.append(f"%{search}%")
        
        total_count = await db_pool.fetchval(count_query, *count_params)
        
        # Format response
        products = []
        storage = get_storage_manager()
        
        for row in rows:
            product_dict = dict(row)
            
            # Handle metadata (already a dict from asyncpg JSONB)
            metadata = product_dict.get('metadata')
            if metadata is None:
                metadata = {}
            
            # Generate pre-signed URL for image if available
            image_url = None
            if product_dict.get('image_url'):
                try:
                    s3_key = product_dict['image_url']
                    # Handle both S3 keys and full URLs
                    if s3_key.startswith('http'):
                        image_url = s3_key
                    else:
                        image_url = storage.get_presigned_url(s3_key, expiration=3600)
                except Exception as e:
                    logger.warning(f"Failed to generate image URL for product {product_dict['id']}: {str(e)}")
            
            product = {
                "id": product_dict['id'],
                "title": product_dict['title'],
                "description": product_dict['description'],
                "price": float(product_dict['base_price']),
                "category": product_dict['category'],
                "status": product_dict['status'],
                "created_at": product_dict['created_at'].isoformat() if product_dict['created_at'] else None,
                "updated_at": product_dict['updated_at'].isoformat() if product_dict['updated_at'] else None,
                "metadata": metadata,
                "artwork": {
                    "id": product_dict.get('artwork_id'),
                    "image_url": image_url,
                    "prompt": product_dict.get('prompt'),
                    "style": product_dict.get('style'),
                    "provider": product_dict.get('provider')
                } if product_dict.get('artwork_id') else None
            }
            
            products.append(product)
        
        return {
            "products": products,
            "total": total_count,
            "limit": limit,
            "offset": offset
        }
    
    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=f"Failed to fetch products: {str(e)}")


@router.get("/{product_id}")
async def get_product(
    product_id: int,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Get a single product by ID"""
    try:
        query = """
            SELECT 
                p.id,
                p.title,
                p.description,
                p.base_price,
                p.category,
                p.status,
                p.created_at,
                p.updated_at,
                p.metadata,
                a.id as artwork_id,
                a.image_url,
                a.prompt,
                a.style,
                a.provider
            FROM products p
            LEFT JOIN artwork a ON p.artwork_id = a.id
            WHERE p.id = $1
        """
        
        row = await db_pool.fetchrow(query, product_id)
        
        if not row:
            raise HTTPException(status_code=404, detail="Product not found")
        
        product_dict = dict(row)
        
        # Handle metadata
        metadata = product_dict.get('metadata')
        if metadata is None:
            metadata = {}
        
        # Generate pre-signed URL for image
        image_url = None
        if product_dict.get('image_url'):
            try:
                storage = get_storage_manager()
                s3_key = product_dict['image_url']
                if s3_key.startswith('http'):
                    image_url = s3_key
                else:
                    image_url = storage.get_presigned_url(s3_key, expiration=3600)
            except Exception as e:
                logger.warning(f"Failed to generate image URL: {str(e)}")
        
        return {
            "id": product_dict['id'],
            "title": product_dict['title'],
            "description": product_dict['description'],
            "price": float(product_dict['base_price']),
            "category": product_dict['category'],
            "status": product_dict['status'],
            "created_at": product_dict['created_at'].isoformat() if product_dict['created_at'] else None,
            "updated_at": product_dict['updated_at'].isoformat() if product_dict['updated_at'] else None,
            "metadata": metadata,
            "artwork": {
                "id": product_dict.get('artwork_id'),
                "image_url": image_url,
                "prompt": product_dict.get('prompt'),
                "style": product_dict.get('style'),
                "provider": product_dict.get('provider')
            } if product_dict.get('artwork_id') else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product {product_id}: {str(e)}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=f"Failed to fetch product: {str(e)}")
