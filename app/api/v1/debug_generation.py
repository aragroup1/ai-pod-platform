# app/api/v1/debug_generation.py
"""
Debug endpoint to trace the product generation flow
"""
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger
import json

from app.database import DatabasePool
from app.dependencies import get_db_pool
from app.core.ai.generator import get_ai_generator

router = APIRouter()


@router.post("/test-single-generation")
async def test_single_generation(
    keyword: str = "mountain sunset",
    style: str = "minimalist",
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    Test a single image generation end-to-end with detailed logging
    """
    logger.info(f"🧪 Testing generation: {keyword} - {style}")
    
    try:
        # Step 1: Test AI generation
        logger.info("Step 1: Testing AI image generation...")
        generator = get_ai_generator(testing_mode=True)
        
        result = await generator.generate_image(
            prompt=f"{keyword}, {style} style, high quality",
            style=style,
            keyword=keyword
        )
        
        logger.info(f"✅ AI Result type: {type(result)}")
        logger.info(f"✅ AI Result keys: {result.keys() if isinstance(result, dict) else 'NOT A DICT'}")
        logger.info(f"✅ Image URL type: {type(result.get('image_url')) if isinstance(result, dict) else 'N/A'}")
        logger.info(f"✅ Image URL value: {result.get('image_url', 'MISSING')[:100] if isinstance(result, dict) else 'N/A'}")
        
        # Step 2: Test S3 upload
        logger.info("Step 2: Testing S3 upload...")
        from app.utils.s3_storage import download_and_upload_from_url
        
        if isinstance(result, dict) and result.get('image_url'):
            image_url = result['image_url']
            
            # Verify it's a string
            if not isinstance(image_url, str):
                logger.error(f"❌ image_url is not a string! Type: {type(image_url)}")
                logger.error(f"❌ Value: {image_url}")
                raise ValueError(f"image_url must be string, got {type(image_url)}")
            
            logger.info(f"Uploading from URL: {image_url[:100]}...")
            
            s3_key = await download_and_upload_from_url(
                source_url=image_url,
                folder=f"debug-test/{keyword.replace(' ', '-')}",
                metadata={'test': 'true', 'keyword': keyword, 'style': style}
            )
            
            logger.info(f"✅ S3 Key: {s3_key}")
            
            # Step 3: Test database insertion
            logger.info("Step 3: Testing database insertion...")
            
            # Create images JSON
            images_json = json.dumps({
                'image_url': s3_key,
                'style': style,
                'keyword': keyword
            })
            
            product = await db_pool.fetchrow("""
                INSERT INTO products (
                    title, description, tags, category,
                    style, images, status, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
                RETURNING id, title, images
            """,
                f"DEBUG TEST: {keyword} - {style}",
                f"Debug test product for {keyword}",
                json.dumps([keyword, style, 'debug-test']),
                'debug',
                style,
                images_json,
                'active'
            )
            
            logger.info(f"✅ Product created: ID={product['id']}")
            logger.info(f"✅ Product images field: {product['images']}")
            
            return {
                "success": True,
                "steps": {
                    "ai_generation": {
                        "status": "✅ Success",
                        "image_url": image_url[:100],
                        "full_result_keys": list(result.keys())
                    },
                    "s3_upload": {
                        "status": "✅ Success",
                        "s3_key": s3_key
                    },
                    "database": {
                        "status": "✅ Success",
                        "product_id": product['id'],
                        "images_field": product['images']
                    }
                },
                "product_id": product['id'],
                "view_url": f"Check Railway dashboard products table for ID {product['id']}"
            }
        else:
            raise ValueError("AI generation did not return image_url")
            
    except Exception as e:
        logger.error(f"❌ Debug test failed: {e}")
        logger.exception("Full traceback:")
        
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "message": "Check Railway logs for full traceback"
        }


@router.get("/check-recent-products")
async def check_recent_products(
    limit: int = 10,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    Check recent products and their image fields
    """
    try:
        products = await db_pool.fetch("""
            SELECT 
                id, title, style, status, created_at,
                images,
                CASE 
                    WHEN images IS NULL THEN 'NULL'
                    WHEN images::text = '{}' THEN 'EMPTY_OBJECT'
                    WHEN images::text = '[]' THEN 'EMPTY_ARRAY'
                    ELSE 'HAS_DATA'
                END as images_status,
                LENGTH(images::text) as images_length
            FROM products
            ORDER BY created_at DESC
            LIMIT $1
        """, limit)
        
        return {
            "total": len(products),
            "products": [
                {
                    "id": p['id'],
                    "title": p['title'],
                    "style": p['style'],
                    "status": p['status'],
                    "images_status": p['images_status'],
                    "images_length": p['images_length'],
                    "images_raw": p['images'][:200] if p['images'] else None
                }
                for p in products
            ]
        }
        
    except Exception as e:
        logger.error(f"Error checking products: {e}")
        raise HTTPException(status_code=500, detail=str(e))
