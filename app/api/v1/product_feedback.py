# app/api/v1/product_feedback.py
"""
Product Feedback API - Learn from User Preferences
Stores approvals/rejections and learns from patterns
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from loguru import logger
from datetime import datetime

from app.database import DatabasePool
from app.dependencies import get_db_pool

router = APIRouter()


class FeedbackRequest(BaseModel):
    product_id: int
    action: str  # 'approve' or 'reject'
    reason: Optional[str] = None


class BulkFeedbackRequest(BaseModel):
    product_ids: List[int]
    action: str


@router.post("/feedback")
async def record_feedback(
    request: FeedbackRequest,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    Record user feedback on a product
    This helps the AI learn what you like/dislike
    """
    try:
        # Get product details
        product = await db_pool.fetchrow(
            """
            SELECT p.*, a.style, a.metadata, a.provider
            FROM products p
            LEFT JOIN artwork a ON p.artwork_id = a.id
            WHERE p.id = $1
            """,
            request.product_id
        )
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Store feedback
        await db_pool.execute(
            """
            INSERT INTO product_feedback (
                product_id, action, reason, style, 
                provider, keyword, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, NOW())
            """,
            request.product_id,
            request.action,
            request.reason,
            product['style'],
            product['provider'],
            product['title'].split('-')[0].strip() if product['title'] else ''
        )
        
        # Update product status
        new_status = 'approved' if request.action == 'approve' else 'rejected'
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
        
        logger.info(f"Feedback recorded: Product {request.product_id} {request.action}ed")
        
        return {
            "success": True,
            "product_id": request.product_id,
            "action": request.action,
            "status": new_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-feedback")
async def bulk_feedback(
    request: BulkFeedbackRequest,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Approve/reject multiple products at once"""
    try:
        new_status = 'approved' if request.action == 'approve' else 'rejected'
        
        # Update all products
        await db_pool.execute(
            """
            UPDATE products 
            SET status = $1::product_status,
                updated_at = NOW()
            WHERE id = ANY($2)
            """,
            new_status,
            request.product_ids
        )
        
        # Record feedback for each
        for product_id in request.product_ids:
            product = await db_pool.fetchrow(
                """
                SELECT p.*, a.style, a.provider
                FROM products p
                LEFT JOIN artwork a ON p.artwork_id = a.id
                WHERE p.id = $1
                """,
                product_id
            )
            
            if product:
                await db_pool.execute(
                    """
                    INSERT INTO product_feedback (
                        product_id, action, style, provider, created_at
                    ) VALUES ($1, $2, $3, $4, NOW())
                    """,
                    product_id,
                    request.action,
                    product['style'],
                    product['provider']
                )
        
        logger.info(f"Bulk feedback: {len(request.product_ids)} products {request.action}ed")
        
        return {
            "success": True,
            "count": len(request.product_ids),
            "action": request.action
        }
        
    except Exception as e:
        logger.error(f"Error in bulk feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rejected")
async def get_rejected_products(
    limit: int = 100,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Get all rejected products (hidden from gallery)"""
    try:
        products = await db_pool.fetch(
            """
            SELECT p.id, p.title, p.sku, a.style, a.image_url
            FROM products p
            LEFT JOIN artwork a ON p.artwork_id = a.id
            WHERE p.status = 'rejected'
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
                    "style": p["style"],
                    "image_url": p["image_url"]
                }
                for p in products
            ],
            "total": len(products)
        }
        
    except Exception as e:
        logger.error(f"Error fetching rejected products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preferences")
async def get_learned_preferences(
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    Get AI-learned preferences from feedback history
    Shows what styles, keywords, etc. you tend to approve/reject
    """
    try:
        # Style preferences
        style_stats = await db_pool.fetch(
            """
            SELECT 
                style,
                COUNT(*) FILTER (WHERE action = 'approve') as approved,
                COUNT(*) FILTER (WHERE action = 'reject') as rejected,
                COUNT(*) as total,
                ROUND(
                    COUNT(*) FILTER (WHERE action = 'approve')::DECIMAL / 
                    COUNT(*)::DECIMAL * 100, 
                    1
                ) as approval_rate
            FROM product_feedback
            WHERE style IS NOT NULL
            GROUP BY style
            ORDER BY total DESC
            """)
        
        # Provider preferences
        provider_stats = await db_pool.fetch(
            """
            SELECT 
                provider,
                COUNT(*) FILTER (WHERE action = 'approve') as approved,
                COUNT(*) FILTER (WHERE action = 'reject') as rejected,
                ROUND(
                    COUNT(*) FILTER (WHERE action = 'approve')::DECIMAL / 
                    COUNT(*)::DECIMAL * 100, 
                    1
                ) as approval_rate
            FROM product_feedback
            WHERE provider IS NOT NULL
            GROUP BY provider
            ORDER BY approval_rate DESC
            """)
        
        # Overall stats
        overall = await db_pool.fetchrow(
            """
            SELECT 
                COUNT(*) FILTER (WHERE action = 'approve') as total_approved,
                COUNT(*) FILTER (WHERE action = 'reject') as total_rejected,
                COUNT(*) as total_feedback
            FROM product_feedback
            """
        )
        
        return {
            "overall": {
                "total_approved": overall["total_approved"],
                "total_rejected": overall["total_rejected"],
                "total_feedback": overall["total_feedback"],
                "approval_rate": round(
                    (overall["total_approved"] / overall["total_feedback"] * 100) 
                    if overall["total_feedback"] > 0 else 0, 
                    1
                )
            },
            "by_style": [
                {
                    "style": row["style"],
                    "approved": row["approved"],
                    "rejected": row["rejected"],
                    "total": row["total"],
                    "approval_rate": float(row["approval_rate"])
                }
                for row in style_stats
            ],
            "by_provider": [
                {
                    "provider": row["provider"],
                    "approved": row["approved"],
                    "rejected": row["rejected"],
                    "approval_rate": float(row["approval_rate"])
                }
                for row in provider_stats
            ],
            "recommendations": generate_recommendations(style_stats, provider_stats)
        }
        
    except Exception as e:
        logger.error(f"Error getting preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def generate_recommendations(style_stats, provider_stats) -> List[str]:
    """Generate recommendations based on feedback patterns"""
    recommendations = []
    
    # Style recommendations
    if style_stats:
        best_style = max(style_stats, key=lambda x: x["approval_rate"] if x["total"] > 5 else 0)
        worst_style = min(style_stats, key=lambda x: x["approval_rate"] if x["total"] > 5 else 100)
        
        if best_style["total"] > 5 and best_style["approval_rate"] > 70:
            recommendations.append(f"✅ Generate more {best_style['style']} style products (you approve {best_style['approval_rate']}%)")
        
        if worst_style["total"] > 5 and worst_style["approval_rate"] < 30:
            recommendations.append(f"❌ Avoid {worst_style['style']} style (only {worst_style['approval_rate']}% approval)")
    
    # Provider recommendations
    if provider_stats:
        best_provider = max(provider_stats, key=lambda x: x["approval_rate"])
        if best_provider["approval_rate"] > 70:
            recommendations.append(f"🤖 Use {best_provider['provider']} model more often")
    
    if not recommendations:
        recommendations.append("📊 Need more feedback to generate recommendations (approve/reject at least 10 products)")
    
    return recommendations
