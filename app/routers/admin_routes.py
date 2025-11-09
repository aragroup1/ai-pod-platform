# app/routers/admin_routes.py
# Uses async session instead of engine to avoid SQLAlchemy compatibility issues

from fastapi import APIRouter, HTTPException, Depends
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/link-artwork-to-products")  # Changed to GET so browser works
async def link_artwork_to_products():
    """
    Links existing artwork to products by matching:
    1. Created date
    2. Style keywords in product title/tags
    """
    try:
        # Use your existing async session dependency
        from app.database import get_async_session
        
        async for session in get_async_session():
            # Update products with matching artwork
            from sqlalchemy import text
            
            query = text("""
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
            
            result = await session.execute(query)
            await session.commit()
            
            matched_count = result.rowcount
            
            # Get remaining unmatched
            check_query = text("""
                SELECT COUNT(*) as unmatched
                FROM products
                WHERE artwork_id IS NULL
            """)
            
            unmatched_result = await session.execute(check_query)
            unmatched = unmatched_result.scalar()
            
            return {
                "success": True,
                "matched_products": matched_count,
                "remaining_unmatched": unmatched,
                "message": f"Linked {matched_count} products to artwork"
            }
            
    except Exception as e:
        logger.error(f"Error linking artwork: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check-linkage-status")
async def check_linkage_status():
    """Check how many products are linked vs unlinked"""
    try:
        from app.database import get_async_session
        from sqlalchemy import text
        
        async for session in get_async_session():
            query = text("""
                SELECT 
                    COUNT(*) FILTER (WHERE artwork_id IS NOT NULL) as linked,
                    COUNT(*) FILTER (WHERE artwork_id IS NULL) as unlinked,
                    COUNT(*) as total
                FROM products
            """)
            
            result = await session.execute(query)
            row = result.fetchone()
            
            return {
                "total_products": row.total,
                "linked": row.linked,
                "unlinked": row.unlinked
            }
            
    except Exception as e:
        logger.error(f"Error checking status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
