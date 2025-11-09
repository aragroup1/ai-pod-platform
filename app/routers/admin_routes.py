# app/routers/admin_routes.py
# Uses asyncpg pool that matches your database setup

from fastapi import APIRouter, HTTPException, Depends
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/link-artwork-to-products")
async def link_artwork_to_products():
    """
    Links existing artwork to products by matching:
    1. Created date
    2. Style keywords in product title/tags
    """
    try:
        from app.database import get_db_pool
        
        pool = await get_db_pool()
        
        # Update products with matching artwork
        query = """
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
        """
        
        result = await pool.execute(query)
        
        # Extract row count from result string like "UPDATE 42"
        matched_count = int(result.split()[-1]) if result.startswith('UPDATE') else 0
        
        # Get remaining unmatched
        unmatched = await pool.fetchval("""
            SELECT COUNT(*) 
            FROM products
            WHERE artwork_id IS NULL
        """)
        
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
        from app.database import get_db_pool
        
        pool = await get_db_pool()
        
        row = await pool.fetchrow("""
            SELECT 
                COUNT(*) FILTER (WHERE artwork_id IS NOT NULL) as linked,
                COUNT(*) FILTER (WHERE artwork_id IS NULL) as unlinked,
                COUNT(*) as total
            FROM products
        """)
        
        return {
            "total_products": row['total'],
            "linked": row['linked'],
            "unlinked": row['unlinked']
        }
        
    except Exception as e:
        logger.error(f"Error checking status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
