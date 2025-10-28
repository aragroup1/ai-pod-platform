# app/core/products/generator.py - FIXED VERSION
"""
Product Generator - Creates products from trends using asyncpg
"""
from typing import List, Optional, Dict
from loguru import logger
from datetime import datetime

from app.database import DatabasePool
from app.core.ai.generator import get_ai_generator
from app.core.ai.prompt_templates import get_prompt_for_style, STYLE_PRICING
from app.utils.s3_storage import get_storage_manager

class ProductGenerator:
    """Generates products from trending keywords"""
    
    # Art styles to generate per keyword
    STYLES = [
        'minimalist', 'abstract', 'vintage', 'watercolor',
        'line_art', 'photography', 'typography', 'botanical'
    ]
    
    def __init__(self, db_pool: DatabasePool, testing_mode: bool = False, budget_mode: str = "balanced"):
        self.db_pool = db_pool
        self.ai_generator = get_ai_generator(testing_mode=testing_mode, budget_mode=budget_mode)
        self.storage = get_storage_manager()
        self.testing_mode = testing_mode
        self.budget_mode = budget_mode
    
    async def generate_products_from_trend(
        self,
        trend_id: int,
        styles: Optional[List[str]] = None,
        upscale: bool = False
    ) -> List[Dict]:
        """Generate products for a single trend"""
        try:
            # Get trend details
            trend = await self.db_pool.fetchrow(
                "SELECT * FROM trends WHERE id = $1",
                trend_id
            )
            
            if not trend:
                logger.error(f"Trend {trend_id} not found")
                return []
            
            keyword = trend['keyword']
            styles_to_generate = styles or self.STYLES
            
            logger.info(f"🎨 Generating {len(styles_to_generate)} products for: {keyword}")
            
            products = []
            
            for style in styles_to_generate:
                try:
                    # Generate artwork
                    prompt_config = get_prompt_for_style(keyword, style)
                    
                    logger.info(f"  Generating {style} style...")
                    artwork_result = await self.ai_generator.generate_image(
                        prompt=prompt_config['prompt'],
                        style=style,
                        keyword=keyword
                    )
                    
                    if not artwork_result or not artwork_result.get('image_url'):
                        logger.error(f"  Failed to generate {style}")
                        continue
                    
                    # Upload to S3
                    logger.info(f"  Uploading to S3...")
                    s3_key = await self.storage.download_and_upload_from_url(
                        source_url=artwork_result['image_url'],
                        folder=f"products/{keyword.replace(' ', '-')}",
                        metadata={
                            'keyword': keyword,
                            'style': style,
                            'model': artwork_result.get('model_used'),
                            'trend_id': trend_id
                        }
                    )
                    
                    if not s3_key:
                        logger.error(f"  Failed to upload to S3")
                        continue
                    
                    # Store artwork in database
                    artwork_id = await self.db_pool.fetchval(
                        """
                        INSERT INTO artwork (
                            prompt, provider, style, image_url,
                            generation_cost, quality_score, trend_id, metadata
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        RETURNING id
                        """,
                        prompt_config['prompt'],
                        artwork_result.get('model_key', 'unknown'),
                        style,
                        s3_key,  # Store S3 key, not URL
                        artwork_result.get('generation_cost', 0),
                        artwork_result.get('quality_score', 0),
                        trend_id,
                        artwork_result
                    )
                    
                    # Create product
                    pricing = STYLE_PRICING.get(style, {'base_price': 44.99})
                    
                    product_id = await self.db_pool.fetchval(
                        """
                        INSERT INTO products (
                            sku, title, description, base_price,
                            artwork_id, category, tags, status
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8::product_status)
                        RETURNING id
                        """,
                        f"POD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{artwork_id}",
                        f"{keyword.title()} - {style.replace('_', ' ').title()} Canvas Art",
                        f"Premium {style.replace('_', ' ')} artwork featuring {keyword}. High-quality canvas print.",
                        pricing['base_price'],
                        artwork_id,
                        'wall-art',
                        [keyword, style, 'canvas', 'art'],
                        'active'
                    )
                    
                    products.append({
                        'product_id': product_id,
                        'artwork_id': artwork_id,
                        'style': style,
                        'keyword': keyword
                    })
                    
                    logger.info(f"  ✅ Created product: {product_id}")
                    
                except Exception as e:
                    logger.error(f"  ❌ Error generating {style}: {e}")
                    continue
            
            logger.info(f"✅ Generated {len(products)} products for '{keyword}'")
            return products
            
        except Exception as e:
            logger.error(f"Error generating products for trend {trend_id}: {e}")
            return []
    
    async def batch_generate_from_trends(
        self,
        limit: int = 10,
        min_trend_score: float = 6.0,
        upscale: bool = False
    ):
        """Generate products for multiple trends"""
        try:
            # Get trends without products
            trends = await self.db_pool.fetch(
                """
                SELECT t.id, t.keyword, t.trend_score
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
                logger.info("No trends available for generation")
                return
            
            logger.info(f"🚀 Batch generating for {len(trends)} trends")
            
            for trend in trends:
                await self.generate_products_from_trend(
                    trend_id=trend['id'],
                    upscale=upscale
                )
            
            logger.info("✅ Batch generation complete")
            
        except Exception as e:
            logger.error(f"Error in batch generation: {e}")
