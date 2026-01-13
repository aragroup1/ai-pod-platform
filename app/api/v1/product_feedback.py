# app/api/v1/product_feedback.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from loguru import logger
from datetime import datetime

from app.database import DatabasePool
from app.dependencies import get_db_pool
from app.utils.s3_storage import get_storage_manager

router = APIRouter()


class FeedbackRequest(BaseModel):
    product_id: int
    action: str  # 'approve' or 'reject'
    reason: Optional[str] = None


class ProductFeedback(BaseModel):
    product_id: int
    feedback_type: str  # 'approved' or 'rejected'
    notes: str = None
    
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
    
    ✅ FIXED: Now DELETES rejected products (they had invalid enum anyway)
    """
    try:
        # Get product details INCLUDING S3 key
        product = await db_pool.fetchrow(
            """
            SELECT p.*, a.image_url as s3_key, a.style, a.metadata, a.provider
            FROM products p
            LEFT JOIN artwork a ON p.artwork_id = a.id
            WHERE p.id = $1
            """,
            request.product_id
        )
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Store feedback BEFORE any deletions
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
        
        if request.action == 'approve':
            # Update to approved status
            await db_pool.execute(
                """
                UPDATE products 
                SET status = 'approved'::product_status,
                   last_updated = NOW()
                WHERE id = $1
                """,
                request.product_id
            )
            
            logger.info(f"✅ Product {request.product_id} approved for Shopify")
            
            return {
                "success": True,
                "product_id": request.product_id,
                "action": "approve",
                "status": "approved",
                "deleted": False
            }
            
        else:  # reject
            # Delete from S3 first
            s3_deleted = False
            if product.get('s3_key'):
                try:
                    storage = get_storage_manager()
                    s3_deleted = storage.delete_image(product['s3_key'])
                    
                    if s3_deleted:
                        logger.info(f"✅ Deleted S3 image: {product['s3_key']}")
                    else:
                        logger.warning(f"⚠️ Failed to delete S3 image: {product['s3_key']}")
                        
                except Exception as s3_error:
                    logger.error(f"❌ S3 deletion error: {s3_error}")
            
            # DELETE the product entirely (feedback is already stored)
            await db_pool.execute(
                """
                DELETE FROM products WHERE id = $1
                """,
                request.product_id
            )
            
            logger.info(f"🗑️ Product {request.product_id} rejected and DELETED from database")
            
            return {
                "success": True,
                "product_id": request.product_id,
                "action": "reject",
                "status": "deleted",
                "s3_deleted": s3_deleted,
                "deleted": True
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-feedback")
async def bulk_feedback(
    request: BulkFeedbackRequest,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    Approve/reject multiple products at once
    ✅ FIXED: Deletes rejected products instead of invalid status update
    """
    try:
        if request.action == 'approve':
            # Update all to approved
            await db_pool.execute(
                """
                UPDATE products 
                SET status = 'approved'::product_status,
                    updated_at = NOW()
                WHERE id = ANY($1)
                """,
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
                        'approve',
                        product['style'],
                        product['provider']
                    )
            
            logger.info(f"✅ Bulk approved: {len(request.product_ids)} products")
            
            return {
                "success": True,
                "count": len(request.product_ids),
                "action": "approve",
                "deleted": False
            }
            
        else:  # reject
            # Get all products with S3 keys
            products = await db_pool.fetch(
                """
                SELECT p.id, p.title, a.image_url as s3_key, a.style, a.provider
                FROM products p
                LEFT JOIN artwork a ON p.artwork_id = a.id
                WHERE p.id = ANY($1)
                """,
                request.product_ids
            )
            
            # Store feedback BEFORE deletion
            for product in products:
                await db_pool.execute(
                    """
                    INSERT INTO product_feedback (
                        product_id, action, style, provider, created_at
                    ) VALUES ($1, $2, $3, $4, NOW())
                    """,
                    product['id'],
                    'reject',
                    product['style'],
                    product['provider']
                )
            
            # Delete from S3
            storage = get_storage_manager()
            deleted_count = 0
            
            for product in products:
                if product['s3_key']:
                    try:
                        if storage.delete_image(product['s3_key']):
                            deleted_count += 1
                            logger.info(f"✅ Deleted S3 image for product {product['id']}")
                    except Exception as e:
                        logger.error(f"❌ Failed to delete S3 for product {product['id']}: {e}")
            
            # DELETE all products from database
            await db_pool.execute(
                """
                DELETE FROM products WHERE id = ANY($1)
                """,
                request.product_ids
            )
            
            logger.info(f"🗑️ Bulk rejected: {len(request.product_ids)} products DELETED (S3: {deleted_count}/{len(products)})")
            
            return {
                "success": True,
                "count": len(request.product_ids),
                "action": "reject",
                "s3_deleted": deleted_count,
                "deleted": True
            }
        
    except Exception as e:
        logger.error(f"Error in bulk feedback: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rejected")
async def get_rejected_products(
    limit: int = 100,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    Get all rejected products from feedback history
    NOTE: Products are now DELETED, so this queries the feedback table
    """
    try:
        # Query feedback history instead since products are deleted
        rejected = await db_pool.fetch(
            """
            SELECT 
                pf.product_id,
                pf.style,
                pf.provider,
                pf.keyword,
                pf.created_at,
                'DELETED' as note
            FROM product_feedback pf
            WHERE pf.action = 'reject'
            ORDER BY pf.created_at DESC
            LIMIT $1
            """,
            limit
        )
        
        return {
            "products": [
                {
                    "id": r["product_id"],
                    "style": r["style"],
                    "provider": r["provider"],
                    "keyword": r["keyword"],
                    "rejected_at": r["created_at"],
                    "note": "Product and S3 image deleted"
                }
                for r in rejected
            ],
            "total": len(rejected)
        }
        
    except Exception as e:
        logger.error(f"Error fetching rejected products: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@router.post("/feedback")
async def record_feedback(feedback: ProductFeedback):
    # Existing approval logic
    await db.execute(
        "UPDATE products SET status = $1 WHERE id = $2",
        'approved', feedback.product_id
    )
    
    # Auto-generate SEO content
    if feedback.feedback_type == 'approved':
        product = await db.fetch_one(
            "SELECT artwork FROM products WHERE id = $1", 
            feedback.product_id
        )
        
        if product['artwork']['image_url']:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Create SEO-optimized t-shirt listing: 1) Title (50-60 chars, keyword-rich) 2) Description (150 words, persuasive, include fit/material). JSON: {\"title\": \"...\", \"description\": \"...\"}"},
                        {"type": "image_url", "image_url": {"url": product['artwork']['image_url']}}
                    ]
                }]
            )
            
            content = json.loads(response.choices[0].message.content)
            
            await db.execute(
                "UPDATE products SET title = $1, description = $2 WHERE id = $3",
                content['title'], content['description'], feedback.product_id
            )
    
    return {"success": True}

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
