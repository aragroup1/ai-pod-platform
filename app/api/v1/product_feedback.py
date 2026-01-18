from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.database import db_pool
from loguru import logger

router = APIRouter()

class ProductFeedback(BaseModel):
    product_id: int
    feedback_type: str  # 'approved' or 'rejected'
    notes: Optional[str] = ""

@router.post("/feedback")
async def record_feedback(feedback: ProductFeedback):
    """Record product approval or rejection"""
    
    logger.info(f"📝 Received {feedback.feedback_type} for product {feedback.product_id}")
    
    if feedback.feedback_type not in ['approved', 'rejected']:
        raise HTTPException(400, "feedback_type must be 'approved' or 'rejected'")
    
    async with db_pool.pool.acquire() as conn:
        # Check product exists
        product = await conn.fetchrow(
            "SELECT id, status FROM products WHERE id = $1",
            feedback.product_id
        )
        
        if not product:
            raise HTTPException(404, f"Product {feedback.product_id} not found")
        
        # Update status
        new_status = 'approved' if feedback.feedback_type == 'approved' else 'rejected'
        
        await conn.execute(
            "UPDATE products SET status = $1 WHERE id = $2",
            new_status,
            feedback.product_id
        )
        
        logger.info(f"✅ Product {feedback.product_id} marked as {new_status}")
        
        return {
            "success": True,
            "product_id": feedback.product_id,
            "status": new_status
        }

@router.post("/batch-generate-seo")
async def batch_generate_seo():
    """Placeholder for batch SEO generation"""
    logger.info("📝 Batch SEO generation endpoint called")
    return {"success": True, "message": "SEO generation not implemented yet"}
