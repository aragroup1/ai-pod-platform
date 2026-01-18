from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.database import db_pool
from loguru import logger

router = APIRouter()

class ProductFeedback(BaseModel):
    product_id: int
    feedback_type: str
    notes: Optional[str] = None

@router.post("/feedback")
async def record_feedback(feedback: ProductFeedback):
    """Record product approval or rejection"""
    
    try:
        logger.info(f"✅ Feedback received: product={feedback.product_id}, type={feedback.feedback_type}")
        
        if feedback.feedback_type not in ['approved', 'rejected']:
            raise HTTPException(400, "feedback_type must be 'approved' or 'rejected'")
        
        # Update product status
        new_status = 'approved' if feedback.feedback_type == 'approved' else 'rejected'
        
        async with db_pool.pool.acquire() as conn:
            # Check if product exists
            product = await conn.fetchrow(
                "SELECT id, status FROM products WHERE id = $1",
                feedback.product_id
            )
            
            if not product:
                raise HTTPException(404, f"Product {feedback.product_id} not found")
            
            # Update status
            await conn.execute(
                "UPDATE products SET status = $1 WHERE id = $2",
                new_status,
                feedback.product_id
            )
        
        logger.info(f"✅ Product {feedback.product_id} status updated to {new_status}")
        
        return {
            "success": True,
            "product_id": feedback.product_id,
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
