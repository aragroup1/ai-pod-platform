from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import base64
from io import BytesIO
from app.database import db_pool
from app.config import settings
from loguru import logger

router = APIRouter()

class ShopifyUploadRequest(BaseModel):
    product_id: int

async def download_image_as_base64(image_url: str) -> str:
    """Download image from S3 and convert to base64"""
    async with httpx.AsyncClient() as client:
        response = await client.get(image_url)
        response.raise_for_status()
        image_data = response.content
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Detect content type
        content_type = response.headers.get('content-type', 'image/png')
        return f"data:{content_type};base64,{base64_image}"

@router.post("/upload")
async def upload_to_shopify(request: ShopifyUploadRequest):
    """Upload a product to Shopify"""
    
    shop_url = settings.SHOPIFY_SHOP_URL
    access_token = settings.SHOPIFY_ACCESS_TOKEN
    
    if not shop_url or not access_token:
        raise HTTPException(400, "Shopify credentials not configured")
    
    # Fetch product and process image inside the same block
    async with db_pool.pool.acquire() as conn:
        product = await conn.fetchrow(
            """
            SELECT p.id, p.title, p.description, p.sku, p.base_price, 
                   a.image_url, a.style
            FROM products p
            LEFT JOIN artwork a ON p.artwork_id = a.id
            WHERE p.id = $1 AND p.status = 'approved'
            """,
            request.product_id
        )
        
        if not product:
            raise HTTPException(404, "Product not found or not approved")
        
        # Extract values while still in context
        product_id = product['id']
        title = product['title']
        description = product['description']
        sku = product['sku']
        base_price = product['base_price']
        image_url = product['image_url']
    
    # Now continue outside the block with extracted values
    base64_image = None
    if image_url:
        try:
            base64_image = await download_image_as_base64(image_url)
        except Exception as e:
            logger.error(f"Failed to download image: {e}")
    
    shopify_product = {
        "product": {
            "title": title or f"Design {sku}",
            "body_html": description or "Premium quality canvas print",
            # ... rest of code
            "vendor": "AI POD Platform",
            "product_type": "Canvas Print",
            "status": "draft",
            "variants": [{
                "price": str(product['base_price'] or 29.99),
                "sku": product['sku'],
                "inventory_management": None
            }]
        }
    }
    
    # Add base64 image - Shopify will host it
    if base64_image:
        shopify_product['product']['images'] = [{
            "attachment": base64_image
        }]
        
@router.post("/upload")
async def upload_to_shopify(request: ShopifyUploadRequest):
    """Upload a product to Shopify"""
    
    shop_url = settings.SHOPIFY_SHOP_URL
    access_token = settings.SHOPIFY_ACCESS_TOKEN
    
    if not shop_url or not access_token:
        raise HTTPException(400, "Shopify credentials not configured")
    
    async with db_pool.pool.acquire() as conn:
        product = await conn.fetchrow(
            """
            SELECT p.id, p.title, p.description, p.sku, p.base_price, 
                   a.image_url, a.style
            FROM products p
            LEFT JOIN artwork a ON p.artwork_id = a.id
            WHERE p.id = $1 AND p.status = 'approved'
            """,
            request.product_id
        )
    
    if not product:
        raise HTTPException(404, "Product not found or not approved")
    
    image_url = product['image_url']
    
    shopify_product = {
        "product": {
            "title": product['title'] or f"Design {product['sku']}",
            "body_html": product['description'] or "Premium quality canvas print",
            "vendor": "AI POD Platform",
            "product_type": "Canvas Print",
            "status": "draft",
            "variants": [{
                "price": str(product['base_price'] or 29.99),
                "sku": product['sku'],
                "inventory_management": None
            }]
        }
    }
    
    if image_url:
        shopify_product['product']['images'] = [{"src": image_url}]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://{shop_url}/admin/api/2024-01/products.json",
                headers={
                    "X-Shopify-Access-Token": access_token,
                    "Content-Type": "application/json"
                },
                json=shopify_product,
                timeout=30.0
            )
            
            if response.status_code == 201:
                shopify_data = response.json()
                logger.info(f"✅ Product {request.product_id} uploaded to Shopify")
                
                async with db_pool.pool.acquire() as conn:
                    await conn.execute(
                        "UPDATE products SET status = 'uploaded' WHERE id = $1",
                        request.product_id
                    )
                
                return {
                    "success": True,
                    "shopify_product_id": shopify_data['product']['id'],
                    "shopify_url": f"https://{shop_url}/admin/products/{shopify_data['product']['id']}"
                }
            else:
                logger.error(f"Shopify upload failed: {response.text}")
                raise HTTPException(400, f"Shopify API error: {response.text}")
                
    except Exception as e:
        logger.error(f"Error uploading to Shopify: {e}")
        raise HTTPException(500, f"Upload failed: {str(e)}")
