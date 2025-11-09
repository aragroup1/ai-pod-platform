# app/routers/admin_routes.py
# Fixed version - imports SQLAlchemy inside functions

from fastapi import APIRouter, HTTPException
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/link-artwork-to-products")
async def link_artwork_to_products():
    """
    Links existing artwork to products by matching:
    1. Created date
    2. Style keywords in product title/tags
    """
    try:
        # Import inside function to avoid module-level SQLAlchemy issues
        from sqlalchemy import text
        from app.utils.database import engine
        
        with engine.connect() as conn:
            # Update products with matching artwork by date and style
            update_query = text("""
                UPDATE products p
                SET 
                    artwork_id = a.id,
                    image_url = a.image_url
                FROM artwork a
                WHERE 
                    p.artwork_id IS NULL
                    AND DATE(p.created_at) = DATE(a.created_at)
                    AND (
                        p.title ILIKE '%' || a.style || '%'
                        OR a.style = ANY(p.tags)
                    )
            """)
            
            result = conn.execute(update_query)
            conn.commit()
            
            matched_count = result.rowcount
            
            # Get remaining unmatched products
            check_query = text("""
                SELECT COUNT(*) as unmatched
                FROM products
                WHERE artwork_id IS NULL
            """)
            
            unmatched = conn.execute(check_query).scalar()
            
            return {
                "success": True,
                "matched_products": matched_count,
                "remaining_unmatched": unmatched,
                "message": f"Linked {matched_count} products to artwork"
            }
            
    except Exception as e:
        logger.error(f"Error linking artwork: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check-linkage-status")
async def check_linkage_status():
    """Check how many products are linked vs unlinked"""
    try:
        # Import inside function
        from sqlalchemy import text
        from app.utils.database import engine
        
        with engine.connect() as conn:
            query = text("""
                SELECT 
                    COUNT(*) FILTER (WHERE artwork_id IS NOT NULL) as linked,
                    COUNT(*) FILTER (WHERE artwork_id IS NULL) as unlinked,
                    COUNT(*) as total
                FROM products
            """)
            
            result = conn.execute(query).fetchone()
            
            return {
                "total_products": result.total,
                "linked": result.linked,
                "unlinked": result.unlinked
            }
            
    except Exception as e:
        logger.error(f"Error checking status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
