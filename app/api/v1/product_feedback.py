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
async def record_feedback(feedback: ProductFeedback):
    """Record product feedback and auto-generate SEO content for approved products"""
    
    logger.info(f"Processing {feedback.feedback_type} feedback for product {feedback.product_id}")
    
    async with db_pool.pool.acquire() as conn:
        # Update product status
        if feedback.feedback_type == 'approved':
            await conn.execute(
                "UPDATE products SET status = 'approved' WHERE id = $1",
                feedback.product_id
            )
            logger.info(f"✅ Product {feedback.product_id} approved for Shopify")
            
            # Fetch product with artwork
            product = await conn.fetchrow(
                "SELECT id, artwork FROM products WHERE id = $1", 
                feedback.product_id
            )
            
            # Auto-generate SEO content
        if product and product['artwork'] and product['artwork'].get('image_url'):
                # This is the corrected section for your product_feedback.py file
# Replace lines 50-110 approximately with this code

                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=settings.OPENAI_API_KEY)
                    
                    logger.info(f"🎨 Analyzing image for SEO content generation...")
                    
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{
                            "role": "user",
                            "content": [
                                {
                                    "type": "text", 
                                    "text": """Analyze this canvas print design in detail and create SEO-optimized listing content.

ANALYZE:
- Main colors (be specific: navy blue, sage green, burnt orange, etc)
- Design style (minimalist, vintage, abstract, geometric, illustrative, etc)
- Visual elements (what objects, shapes, patterns, text, symbols are visible)
- Overall aesthetic and mood (playful, serious, edgy, peaceful, etc)
- Target audience (home decor enthusiasts, art collectors, interior designers, etc)

CREATE JSON:
{
  "title": "50-60 character SEO title including: main visual element + style + color + 'Canvas Print' or 'Wall Art'",
  "description": "150-200 word description that:
    - Opens with the main visual hook describing the artwork
    - Describes colors and design elements in vivid detail
    - Includes keywords: 'canvas print', 'wall art', 'home decor', 'framed art', 'gallery wrap', 'museum quality'
    - Mentions quality: 'premium canvas', 'vibrant colors', 'fade-resistant', 'ready to hang'
    - Appeals to target audience with home/office decor context
    - SEO keywords naturally integrated throughout
    - Ends with a call-to-action"
}

IMPORTANT: Be extremely specific about what you actually see in the image. This is a canvas wall art print, not clothing.

Example title: "Abstract Geometric Canvas Print - Navy Blue & Gold Modern Wall Art"
Example description start: "Transform your space with this stunning abstract geometric canvas print. Featuring bold navy blue shapes contrasted against luxurious gold accents, this modern wall art brings sophisticated style to any room. The clean lines and minimalist composition create a sense of balance and harmony, perfect for contemporary homes and offices..."

Return ONLY valid JSON, no markdown formatting."""
                                },
                                {"type": "image_url", "image_url": {"url": product['artwork']['image_url']}}
                            ]
                        }],
                        max_tokens=600
                    )
                    
                    # Parse response
                    content_text = response.choices[0].message.content.strip()
                    
                    # Remove markdown code blocks if present
                    if content_text.startswith('```'):
                        content_text = content_text.split('```')[1]
                        if content_text.startswith('json'):
                            content_text = content_text[4:]
                        content_text = content_text.strip()
                    
                    content = json.loads(content_text)
                    
                    # Update product with SEO content
                    await conn.execute(
                        "UPDATE products SET title = $1, description = $2 WHERE id = $3",
                        content['title'], 
                        content['description'], 
                        feedback.product_id
                    )
                    
                    logger.info(f"✅ SEO content generated for product {feedback.product_id}")
                    logger.info(f"   Title: {content['title']}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to generate SEO content: {e}")
                    # Don't fail the approval if SEO generation fails
                    
        elif feedback.feedback_type == 'rejected':
            await conn.execute(
                "UPDATE products SET status = 'rejected' WHERE id = $1",
                feedback.product_id
            )
            logger.info(f"❌ Product {feedback.product_id} rejected")
        
        # Record feedback in feedback table (optional)
        if feedback.notes:
            await conn.execute(
                """
                INSERT INTO product_feedback (product_id, feedback_type, notes, created_at)
                VALUES ($1, $2, $3, NOW())
                """,
                feedback.product_id,
                feedback.feedback_type,
                feedback.notes
            )
    
    return {
        "success": True, 
        "message": f"Product {feedback.feedback_type}",
        "product_id": feedback.product_id
    }


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

@router.post("/batch-generate-seo")
async def batch_generate_seo():
    products = await db.fetch_all(
        "SELECT id, artwork FROM products WHERE status = 'approved' AND (title IS NULL OR title = '')"
    )
    
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    for product in products:
        if product['artwork']['image_url']:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Create SEO t-shirt listing JSON: {\"title\": \"50-60 char keyword-rich title\", \"description\": \"150 word persuasive description\"}"},
                        {"type": "image_url", "image_url": {"url": product['artwork']['image_url']}}
                    ]
                }]
            )
            
            content = json.loads(response.choices[0].message.content)
            await db.execute(
                "UPDATE products SET title = $1, description = $2 WHERE id = $3",
                content['title'], content['description'], product['id']
            )
    
    return {"updated": len(products)}
    
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
