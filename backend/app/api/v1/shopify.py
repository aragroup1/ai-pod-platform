from fastapi import APIRouter, HTTPException
import httpx

router = APIRouter()

@router.post("/upload")
async def upload_to_shopify(product_id: int, shop_url: str, access_token: str):
    # Fetch product from DB
    product = await get_product(product_id)
    
    # Upload to Shopify
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://{shop_url}/admin/api/2024-01/products.json",
            headers={"X-Shopify-Access-Token": access_token},
            json={
                "product": {
                    "title": product.title,
                    "body_html": product.description,
                    "images": [{"src": product.artwork.image_url}]
                }
            }
        )
    
    if response.status_code == 201:
        return {"success": True}
    raise HTTPException(400, "Upload failed")
