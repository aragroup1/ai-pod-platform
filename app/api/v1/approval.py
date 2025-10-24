from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from loguru import logger

from app.database import DatabasePool
from app.dependencies import get_db_pool

router = APIRouter()


class ApprovalRequest(BaseModel):
    product_id: int
    approved: bool
    notes: str = ""


@router.post("/approve")
async def approve_product(
    request: ApprovalRequest,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    Approve or reject a product for Shopify sync
    
    Workflow:
    1. Product generated (status: 'active')
    2. Manual review & approval
    3. Approved products → status: 'approved' → Sync to Shopify
    4. Rejected products → status: 'rejected' → Don't sync
    """
    try:
        # Get current product
        product = await db_pool.fetchrow(
            "SELECT * FROM products WHERE id = $1",
            request.product_id
        )
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Update status
        new_status = 'approved' if request.approved else 'rejected'
        
        await db_pool.execute(
            """
            UPDATE products 
            SET status = $1::product_status,
                updated_at = NOW()
            WHERE id = $2
            """,
            new_status,
            request.product_id
        )
        
        # Log approval/rejection
        logger.info(f"Product {request.product_id} {new_status} by admin")
        
        # TODO: If approved, trigger Shopify sync
        if request.approved:
            logger.info(f"TODO: Sync product {request.product_id} to Shopify")
            # await sync_to_shopify(request.product_id)
        
        return {
            "message": f"Product {new_status}",
            "product_id": request.product_id,
            "status": new_status,
            "ready_for_shopify": request.approved
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving product: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending")
async def get_pending_approval(
    limit: int = 50,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Get products pending approval"""
    try:
        products = await db_pool.fetch(
            """
            SELECT 
                p.id, p.title, p.sku, p.status, p.base_price,
                a.image_url, a.style, a.quality_score,
                a.metadata->>'model_key' as model_used
            FROM products p
            JOIN artwork a ON p.artwork_id = a.id
            WHERE p.status = 'active'
            ORDER BY p.created_at DESC
            LIMIT $1
            """,
            limit
        )
        
        return {
            "products": [
                {
                    "id": p["id"],
                    "title": p["title"],
                    "sku": p["sku"],
                    "status": p["status"],
                    "base_price": float(p["base_price"]),
                    "image_url": p["image_url"],
                    "style": p["style"],
                    "quality_score": float(p["quality_score"]) if p["quality_score"] else 0,
                    "model_used": p["model_used"]
                }
                for p in products
            ],
            "total": len(products)
        }
        
    except Exception as e:
        logger.error(f"Error fetching pending products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/approved")
async def get_approved_products(
    limit: int = 100,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Get approved products ready for Shopify"""
    try:
        products = await db_pool.fetch(
            """
            SELECT 
                p.id, p.title, p.sku, p.base_price, p.description,
                a.image_url, a.style, a.quality_score,
                p.tags, p.category
            FROM products p
            JOIN artwork a ON p.artwork_id = a.id
            WHERE p.status = 'approved'
            ORDER BY p.updated_at DESC
            LIMIT $1
            """,
            limit
        )
        
        return {
            "products": [
                {
                    "id": p["id"],
                    "title": p["title"],
                    "sku": p["sku"],
                    "base_price": float(p["base_price"]),
                    "description": p["description"],
                    "image_url": p["image_url"],
                    "style": p["style"],
                    "tags": p["tags"],
                    "category": p["category"],
                    "shopify_ready": True
                }
                for p in products
            ],
            "total": len(products),
            "ready_for_sync": len(products)
        }
        
    except Exception as e:
        logger.error(f"Error fetching approved products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-approve")
async def batch_approve_products(
    product_ids: list[int],
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Approve multiple products at once"""
    try:
        await db_pool.execute(
            """
            UPDATE products 
            SET status = 'approved'::product_status,
                updated_at = NOW()
            WHERE id = ANY($1)
            """,
            product_ids
        )
        
        logger.info(f"Batch approved {len(product_ids)} products")
        
        return {
            "message": f"Approved {len(product_ids)} products",
            "product_ids": product_ids,
            "status": "approved"
        }
        
    except Exception as e:
        logger.error(f"Error batch approving: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_approval_stats(
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Get approval workflow statistics"""
    try:
        stats = await db_pool.fetchrow(
            """
            SELECT 
                COUNT(*) FILTER (WHERE status = 'active') as pending,
                COUNT(*) FILTER (WHERE status = 'approved') as approved,
                COUNT(*) FILTER (WHERE status = 'rejected') as rejected,
                COUNT(*) as total
            FROM products
            """
        )
        
        return {
            "pending_approval": stats["pending"],
            "approved": stats["approved"],
            "rejected": stats["rejected"],
            "total_products": stats["total"],
            "approval_rate": round((stats["approved"] / stats["total"] * 100), 2) if stats["total"] > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
