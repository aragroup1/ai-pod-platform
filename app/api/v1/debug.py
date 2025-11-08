from fastapi import APIRouter, Depends
from loguru import logger
import json

from app.database import DatabasePool
from app.dependencies import get_db_pool
from app.core.ai.generator import get_ai_generator
from app.utils.s3_storage import get_storage_manager  # ✅ FIXED IMPORT

router = APIRouter()


@router.get("/test-generation")
async def test_generation(db_pool: DatabasePool = Depends(get_db_pool)):
    """
    Simple test to see what's happening with image generation
    Access via: https://backend-production-7aae.up.railway.app/api/v1/debug/test-generation
    """
    logger.info("🧪 Starting debug test...")
    
    try:
        # Step 1: Test AI generation
        logger.info("Step 1: Generating image...")
        generator = get_ai_generator(testing_mode=True)
        
        result = await generator.generate_image(
            prompt="mountain sunset, minimalist style",
            style="minimalist",
            keyword="mountain"
        )
        
        logger.info(f"Result type: {type(result)}")
        logger.info(f"Result: {result}")
        
        # Check if we got an image URL
        image_url = result.get('image_url') if isinstance(result, dict) else None
        
        if not image_url:
            return {
                "success": False,
                "error": "No image_url in result",
                "result_type": str(type(result)),
                "result_keys": list(result.keys()) if isinstance(result, dict) else "NOT A DICT",
                "result_preview": str(result)[:500]
            }
        
        # Step 2: Test S3 upload
        logger.info(f"Step 2: Uploading to S3 from: {image_url[:100]}")
        
        storage = get_storage_manager()  # ✅ FIXED
        s3_key = await storage.download_and_upload_from_url(  # ✅ FIXED
            source_url=image_url,
            folder="debug-test"
        )
        
        if not s3_key:
            return {
                "success": False,
                "error": "S3 upload failed",
                "image_url": image_url[:100]
            }
        
        logger.info(f"S3 key: {s3_key}")
        
        # Step 3: Create product
        logger.info("Step 3: Creating product...")
        
        images_json = json.dumps({'image_url': s3_key, 'style': 'minimalist'})
        
        product = await db_pool.fetchrow("""
            INSERT INTO products (
                title, description, tags, category,
                style, images, status, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
            RETURNING id, images
        """,
            "DEBUG TEST: Mountain",
            "Debug test product",
            json.dumps(['debug', 'test']),
            'debug',
            'minimalist',
            images_json,
            'active'
        )
        
        return {
            "success": True,
            "message": "✅ All steps completed!",
            "steps": {
                "1_ai_generation": "✅ Got image URL",
                "2_s3_upload": f"✅ Uploaded to {s3_key}",
                "3_database": f"✅ Created product ID {product['id']}"
            },
            "product_id": product['id'],
            "images_field": product['images']
        }
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        logger.exception("Full error:")
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


@router.get("/check-products")
async def check_products(db_pool: DatabasePool = Depends(get_db_pool)):
    """
    Check recent products and their images
    Access via: https://backend-production-7aae.up.railway.app/api/v1/debug/check-products
    """
    try:
        products = await db_pool.fetch("""
            SELECT 
                id, title, status, created_at,
                images,
                CASE 
                    WHEN images IS NULL THEN '❌ NULL'
                    WHEN images::text = '{}' THEN '❌ EMPTY'
                    WHEN images::text LIKE '%image_url%' THEN '✅ HAS URL'
                    ELSE '⚠️ UNKNOWN'
                END as status_check
            FROM products
            ORDER BY created_at DESC
            LIMIT 20
        """)
        
        return {
            "total": len(products),
            "products": [
                {
                    "id": p['id'],
                    "title": p['title'],
                    "status_check": p['status_check'],
                    "images": p['images']
                }
                for p in products
            ]
        }
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"error": str(e)}
