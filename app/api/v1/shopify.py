from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import re
import boto3
import base64
from app.database import db_pool
from app.config import settings
from loguru import logger

router = APIRouter()

class ShopifyUploadRequest(BaseModel):
    product_id: int

def extract_s3_key_from_url(url: str) -> str:
    """Extract S3 key from pre-signed URL"""
    match = re.search(r'amazonaws\.com/(.+?)\?', url)
    if match:
        return match.group(1)
    return None

async def download_s3_image_as_base64(image_url: str) -> str:
    """Download image from S3 using boto3 and convert to base64"""
    s3_key = extract_s3_key_from_url(image_url)
    if not s3_key:
        raise ValueError("Could not extract S3 key from URL")
    
    logger.info(f"📸 Downloading S3 key: {s3_key}")
    
    s3_client = boto3.client('s3',
        region_name='eu-north-1',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )
    
    response = s3_client.get_object(
        Bucket='ai-pod-platform-images',
        Key=s3_key
    )
    
    image_data = response['Body'].read()
    base64_image = base64.b64encode(image_data).decode('utf-8')
    content_type = response['ContentType']
    
    return f"data:{content_type};base64,{base64_image}"

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
    
    # Download image from S3 as base64
    base64_image = None
    if product['image_url']:
        try:
            base64_image = await download_s3_image_as_base64(product['image_url'])
            logger.info(f"✅ Image downloaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to download image: {e}")
    else:
        logger.warning(f"⚠️ No image URL for product {request.product_id}")
    
    shopify_product = {
        "product": {
            "title": product['title'] or f"Design {product['sku']}",
            "body_html": product['description'] or "Premium quality canvas print",
            "vendor": "",
            "product_type": "",
            "published_scope": "web",
            "status": "draft",
            "variants": [{
                "price": str(product['base_price'] or 29.99),
                "sku": product['sku'],
                "inventory_management": None
            }]
        }
    }
    
    if base64_image:
        shopify_product['product']['images'] = [{"attachment": base64_image}]
    else:
        logger.warning(f"⚠️ No image will be uploaded for product {request.product_id}")
    
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
                logger.info(f"   Shopify Product ID: {shopify_data['product']['id']}")
                logger.info(f"   Has images: {len(shopify_data['product'].get('images', [])) > 0}")
                
                async with db_pool.pool.acquire() as conn:
                    await conn.execute(
                        "UPDATE products SET status = 'uploaded' WHERE id = $1",
                        request.product_id
                    )
                
                return {
                    "success": True,
                    "shopify_product_id": shopify_data['product']['id'],
                    "shopify_url": f"https://{shop_url}/admin/products/{shopify_data['product']['id']}",
                    "has_images": len(shopify_data['product'].get('images', [])) > 0
                }
            else:
                logger.error(f"❌ Shopify upload failed: {response.text}")
                raise HTTPException(400, f"Shopify API error: {response.text}")
                
    except Exception as e:
        logger.error(f"❌ Error uploading to Shopify: {e}")
        raise HTTPException(500, f"Upload failed: {str(e)}")
