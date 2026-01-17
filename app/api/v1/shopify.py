from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
from app.database import db_pool
from app.config import settings
from loguru import logger

router = APIRouter()

class ShopifyUpload(BaseModel):
    product_id: int
    shop_url: str
    access_token: str

@router.post("/upload")
async def upload_to_shopify(upload: ShopifyUpload):
    """Upload a product to Shopify"""
    
    # Fetch product from database
    async with db_pool.pool.acquire() as conn:
        product = await conn.fetchrow(
            """
SELECT p.id, p.title, p.description, p.sku, p.base_price, 
                   a.image_url, a.style 
            FROM products p
            LEFT JOIN artwork a ON p.id = a.product_id
            WHERE p.id = $1 AND p.status = 'approved'
            """,
            upload.product_id
        )
    
    if not product:
        raise HTTPException(404, "Product not found or not approved")
    
    # Prepare Shopify product data
    shopify_product = {
        "product": {
            "title": product['title'] or f"Design {product['sku']}",
            "body_html": product['description'] or "Premium quality t-shirt design",
            "vendor": "AI POD Platform",
            "product_type": "T-Shirt",
            "status": "draft",
            "variants": [{
                "price": str(product['base_price'] or 19.99),
                "sku": product['sku'],
                "inventory_management": None
            }]
        }
    }
    
    # Add image if available
    if product['artwork'] and product['artwork'].get('image_url'):
        shopify_product['product']['images'] = [{
            "src": product['artwork']['image_url']
        }]
    
    # Upload to Shopify
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://{upload.shop_url}/admin/api/2024-01/products.json",
                headers={
                    "X-Shopify-Access-Token": upload.access_token,
                    "Content-Type": "application/json"
                },
                json=shopify_product,
                timeout=30.0
            )
            
            if response.status_code == 201:
                shopify_data = response.json()
                logger.info(f"✅ Product {upload.product_id} uploaded to Shopify")
                
                # Mark as uploaded
                async with db_pool.pool.acquire() as conn:
                    await conn.execute(
                        "UPDATE products SET status = 'uploaded' WHERE id = $1",
                        upload.product_id
                    )
                
                return {
                    "success": True,
                    "shopify_product_id": shopify_data['product']['id'],
                    "shopify_url": f"https://{upload.shop_url}/admin/products/{shopify_data['product']['id']}"
                }
            else:
                logger.error(f"Shopify upload failed: {response.text}")
                raise HTTPException(400, f"Shopify API error: {response.text}")
                
    except Exception as e:
        logger.error(f"Error uploading to Shopify: {e}")
        raise HTTPException(500, f"Upload failed: {str(e)}")
