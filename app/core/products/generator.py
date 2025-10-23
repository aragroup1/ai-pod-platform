from typing import List, Dict, Optional
from loguru import logger
from datetime import datetime

from app.database import DatabasePool
from app.core.ai.generator import get_ai_generator
from app.core.ai.prompt_templates import get_pricing_for_style
from app.utils.helpers import generate_sku


class ProductGenerator:
    """Generate POD products from trends"""
    
    ALL_STYLES = [
        'minimalist', 'abstract', 'vintage', 'watercolor',
        'line_art', 'photography', 'typography', 'botanical'
    ]
    
    def __init__(self, db_pool: DatabasePool, testing_mode: bool = False):
        self.db_pool = db_pool
        self.ai_generator = get_ai_generator(testing_mode=testing_mode)
        self.testing_mode = testing_mode
    
    async def generate_products_from_trend(
        self,
        trend_id: int,
        styles: Optional[List[str]] = None,
        upscale: bool = False
    ) -> List[Dict]:
        """
        Generate products from a single trend in multiple styles
        
        Args:
            trend_id: ID of the trend
            styles: List of styles (or None for all)
            upscale: Whether to upscale for print
            
        Returns:
            List of created products
        """
        # Get trend data
        trend = await self.db_pool.fetchrow(
            "SELECT * FROM trends WHERE id = $1",
            trend_id
        )
        
        if not trend:
            logger.error(f"Trend {trend_id} not found")
            return []
        
        keyword = trend['keyword']
        styles_to_generate = styles or self.ALL_STYLES
        
        logger.info(f"🎨 Generating {len(styles_to_generate)} products for trend: {keyword}")
        
        products = []
        
        for style in styles_to_generate:
            try:
                logger.info(f"  → Creating {style} version...")
                
                # Generate artwork
                artwork_data = await self.ai_generator.generate_product_artwork(
                    keyword=keyword,
                    style=style,
                    upscale_for_print=upscale
                )
                
                # Save artwork to database
                artwork_id = await self._save_artwork(
                    trend_id=trend_id,
                    artwork_data=artwork_data
                )
                
                # Create product
                product_id = await self._create_product(
                    artwork_id=artwork_id,
                    keyword=keyword,
                    style=style,
                    trend_category=trend['category']
                )
                
                products.append({
                    'product_id': product_id,
                    'artwork_id': artwork_id,
                    'keyword': keyword,
                    'style': style
                })
                
                logger.info(f"  ✅ Product created: ID {product_id}")
                
            except Exception as e:
                logger.error(f"  ❌ Failed to create {style} product: {e}")
                continue
        
        logger.info(f"✅ Generated {len(products)} products for '{keyword}'")
        return products
    
    async def _save_artwork(
    self,
    trend_id: int,
    artwork_data: Dict
) -> int:
    """Save generated artwork to database WITH permanent storage"""
    
    from app.utils.storage import storage_manager
    
    # Generate unique filename
    artwork_filename = f"artwork/{trend_id}_{datetime.now().timestamp()}.png"
    
    # Download from Replicate and upload to R2
    permanent_url = await storage_manager.download_and_upload(
        source_url=artwork_data['image_url'],
        destination_path=artwork_filename
    )
    
    # Use permanent URL if available, otherwise fall back to temp URL
    final_url = permanent_url or artwork_data['image_url']
    
    artwork_id = await self.db_pool.fetchval(
        """
        INSERT INTO artwork (
            prompt, provider, style, image_url,
            generation_cost, quality_score, trend_id, metadata
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id
        """,
        artwork_data['prompt'],
        artwork_data['model_used'],
        artwork_data['style'],
        final_url,  # Use permanent URL
        0.04 if not self.testing_mode else 0.003,
        9.0,
        trend_id,
        {
            'original_url': artwork_data['image_url'],  # Keep temp URL for reference
            'permanent_url': permanent_url,
            'print_ready': artwork_data.get('print_ready', False),
            'generated_at': artwork_data['generated_at'],
            'dimensions': artwork_data['dimensions']
        }
    )
    
    return artwork_id
    
    async def _create_product(
        self,
        artwork_id: int,
        keyword: str,
        style: str,
        trend_category: str
    ) -> int:
        """Create product entry in database"""
        
        sku = generate_sku(prefix="POD")
        pricing = get_pricing_for_style(style)
        
        # Create product title
        title = f"{keyword.title()} - {style.replace('_', ' ').title()} Wall Art"
        
        # Create description
        description = f"Premium {style.replace('_', ' ')} artwork featuring {keyword}. " \
                      f"High-quality print perfect for home or office decor. " \
                      f"Available in multiple sizes."
        
        product_id = await self.db_pool.fetchval(
            """
            INSERT INTO products (
                sku, title, description, base_price,
                artwork_id, category, tags, status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
            """,
            sku,
            title,
            description,
            pricing['base_price'],
            artwork_id,
            trend_category or 'wall-art',
            [keyword, style, trend_category, 'premium', 'print'],
            'active'  # Ready to sell!
        )
        
        return product_id
    
    async def batch_generate_from_trends(
        self,
        limit: int = 10,
        min_trend_score: float = 6.0,
        upscale: bool = False
    ) -> Dict:
        """
        Generate products for multiple top trends
        
        Args:
            limit: Number of trends to process
            min_trend_score: Minimum trend score
            upscale: Whether to upscale images
            
        Returns:
            Summary dict with statistics
        """
        # Get top trends without products
        trends = await self.db_pool.fetch(
            """
            SELECT t.id, t.keyword, t.trend_score, t.category
            FROM trends t
            LEFT JOIN artwork a ON a.trend_id = t.id
            WHERE a.id IS NULL
            AND t.trend_score >= $1
            ORDER BY t.trend_score DESC
            LIMIT $2
            """,
            min_trend_score,
            limit
        )
        
        if not trends:
            logger.warning("No trends found without products")
            return {'trends_processed': 0, 'products_created': 0}
        
        logger.info(f"🚀 Batch generating products for {len(trends)} trends")
        
        total_products = 0
        
        for trend in trends:
            products = await self.generate_products_from_trend(
                trend_id=trend['id'],
                upscale=upscale
            )
            total_products += len(products)
            
            # Small delay between trends
            await asyncio.sleep(2)
        
        logger.info(f"✅ Batch complete: {total_products} products from {len(trends)} trends")
        
        return {
            'trends_processed': len(trends),
            'products_created': total_products,
            'styles_per_trend': len(self.ALL_STYLES)
        }
