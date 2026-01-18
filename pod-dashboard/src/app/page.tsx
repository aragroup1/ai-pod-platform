from fastapi import APIRouter, HTTPException, Request
from app.database import db_pool
from loguru import logger

router = APIRouter()

@router.post("/feedback")
async def record_feedback(request: Request):
    """Record product approval or rejection - accepts raw JSON"""
    
    try:
        # Get raw JSON body
        body = await request.json()
        logger.info(f"📝 Raw request received: {body}")
        
        # Extract fields - accept BOTH formats for backwards compatibility
        product_id = body.get('product_id')
        feedback_type = body.get('feedback_type') or body.get('action')  # Accept both!
        
        if not product_id:
            raise HTTPException(400, "product_id is required")
        
        # Normalize values: approve/reject -> approved/rejected
        if feedback_type == 'approve':
            feedback_type = 'approved'
        elif feedback_type == 'reject':
            feedback_type = 'rejected'
        
        if feedback_type not in ['approved', 'rejected']:
            raise HTTPException(400, f"feedback_type must be 'approved' or 'rejected', got: {feedback_type}")
        
        # Update product status
        new_status = feedback_type  # Already normalized
        
        async with db_pool.pool.acquire() as conn:
            # Check if product exists
            product = await conn.fetchrow(
                "SELECT id, status FROM products WHERE id = $1",
                product_id
            )
            
            if not product:
                raise HTTPException(404, f"Product {product_id} not found")
            
            # Update status
            await conn.execute(
                "UPDATE products SET status = $1 WHERE id = $2",
                new_status,
                product_id
            )
        
        logger.info(f"✅ Product {product_id} status updated to {new_status}")
        
        return {
            "success": True,
            "product_id": product_id,
            "status": new_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in feedback endpoint: {e}")
        raise HTTPException(500, f"Error: {str(e)}")

@router.post("/batch-generate-seo")
async def batch_generate_seo():
    """Placeholder for batch SEO generation"""
    return {"success": True, "message": "Not implemented"}
