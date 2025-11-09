# app/api/v1/generation.py
# COMPLETE FIXED VERSION - With correct method name

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class BatchGenerateRequest(BaseModel):
    limit: int = 5
    max_designs_per_keyword: Optional[int] = 3  # Limit designs per keyword for cost control

@router.post("/batch-generate")
async def batch_generate_products(
    request: BatchGenerateRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate products for top trends by search volume
    """
    try:
        from app.core.products.generator import ProductGenerator
        from app.database import get_db_pool
        
        pool = await get_db_pool()
        
        # Initialize generator
        generator = ProductGenerator(db_pool=pool)
        
        # Get top trends by search volume (not null, ordered desc)
        trends = await pool.fetch("""
            SELECT id, keyword, search_volume, category
            FROM trends
            WHERE search_volume IS NOT NULL 
              AND search_volume > 0
              AND status = 'active'
            ORDER BY search_volume DESC
            LIMIT $1
        """, request.limit)
        
        if not trends:
            return {
                "success": False,
                "message": "No trends with search volumes found. Run trend analysis first.",
                "trends_processed": 0,
                "products_created": 0
            }
        
        logger.info(f"🚀 Starting batch generation for {len(trends)} trends")
        
        total_products = 0
        results = []
        
        for trend in trends:
            try:
                logger.info(f"📊 Generating for: {trend['keyword']} (volume: {trend['search_volume']:,})")
                
                # Create a trend object that the generator expects
                class TrendObj:
                    def __init__(self, row):
                        self.id = row['id']
                        self.keyword = row['keyword']
                        self.search_volume = row['search_volume']
                        self.category = row['category']
                
                trend_obj = TrendObj(trend)
                
                # ✅ FIXED: Use the correct method name
                products = await generator.generate_products_from_trend(
                    trend=trend_obj,
                    num_styles=request.max_designs_per_keyword
                )
                
                total_products += len(products)
                
                results.append({
                    "keyword": trend['keyword'],
                    "search_volume": trend['search_volume'],
                    "products_created": len(products)
                })
                
                logger.info(f"✅ Created {len(products)} products for '{trend['keyword']}'")
                
            except Exception as e:
                logger.error(f"❌ Failed for '{trend['keyword']}': {str(e)}")
                results.append({
                    "keyword": trend['keyword'],
                    "search_volume": trend['search_volume'],
                    "error": str(e),
                    "products_created": 0
                })
                continue
        
        return {
            "success": True,
            "message": f"Generated {total_products} products across {len(trends)} trends",
            "trends_processed": len(trends),
            "products_created": total_products,
            "details": results
        }
        
    except Exception as e:
        logger.error(f"Batch generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_generation_status():
    """Get current generation statistics"""
    try:
        from app.database import get_db_pool
        
        pool = await get_db_pool()
        
        stats = await pool.fetchrow("""
            SELECT 
                COUNT(*) as total_products,
                COUNT(*) FILTER (WHERE artwork_id IS NOT NULL) as products_with_artwork,
                COUNT(*) FILTER (WHERE status = 'active') as active_products,
                COUNT(DISTINCT artwork_id) as unique_artworks
            FROM products
        """)
        
        trend_stats = await pool.fetchrow("""
            SELECT 
                COUNT(*) as total_trends,
                COUNT(*) FILTER (WHERE search_volume IS NOT NULL) as trends_with_volume,
                COUNT(*) FILTER (WHERE search_volume > 1000) as high_volume_trends,
                COUNT(*) FILTER (WHERE status = 'active') as active_trends
            FROM trends
        """)
        
        return {
            "products": {
                "total": stats['total_products'],
                "with_artwork": stats['products_with_artwork'],
                "active": stats['active_products'],
                "unique_artworks": stats['unique_artworks']
            },
            "trends": {
                "total": trend_stats['total_trends'],
                "with_volume": trend_stats['trends_with_volume'],
                "high_volume": trend_stats['high_volume_trends']
            },
            "trends_awaiting_generation": trend_stats['active_trends'],
            "ready_to_generate": trend_stats['active_trends'] > 0
        }
        
    except Exception as e:
        logger.error(f"Failed to get status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
