import logging
import json
from typing import Dict, List, Optional
from datetime import datetime

from app.database import DatabasePool

logger = logging.getLogger(__name__)


class ProductGenerator:
    def __init__(self, db_pool: DatabasePool):
        self.db_pool = db_pool
        self._ai_generator = None
    
    @property
    def ai_generator(self):
        """Lazy load to avoid circular import"""
        if self._ai_generator is None:
            from app.core.ai.generator import get_ai_generator
            self._ai_generator = get_ai_generator()
        return self._ai_generator
    
    async def batch_generate_from_trends(self, trend_ids: List[int], styles_per_trend: int = 8):
        """Generate products for multiple trends"""
        logger.info(f"🚀 Batch generating for {len(trend_ids)} trends")
        
        results = []
        for trend_id in trend_ids:
            trend = await self.db_pool.fetchrow("SELECT * FROM trends WHERE id = $1", trend_id)
            if trend:
                products = await self.generate_products_from_trend(trend, styles_per_trend)
                results.extend(products)
        
        return results
    
    async def generate_products_from_trend(self, trend: Dict, num_styles: int = 8) -> List[Dict]:
        """Generate multiple product variations from a single trend"""
        keyword = trend['keyword']
        logger.info(f"🎨 Generating {num_styles} products for: {keyword}")
        
        styles = [
            'minimalist',
            'abstract',
            'vintage',
            'watercolor',
            'line_art',
            'photography',
            'typography',
            'botanical'
        ][:num_styles]
        
        products = []
        
        for style in styles:
            try:
                logger.info(f"  Generating {style} style...")
                
                # Generate AI image - returns a dict with 'image_url' key
                result = await self.ai_generator.generate_image(
                    prompt=f"{keyword}, {style} style, high quality, professional",
                    style=style,
                    keyword=keyword
                )
                
                # ✅ CRITICAL FIX: Validate result first
                if not isinstance(result, dict):
                    logger.error(f"  ❌ AI result is not a dict! Type: {type(result)}")
                    continue

                # Extract the URL string from the result dict
                image_url = result.get('image_url')

                if not image_url or not isinstance(image_url, str):
                    logger.error(f"  ❌ Invalid image_url! Type: {type(image_url)}, Value: {image_url}")
                    continue

                logger.info(f"  ✅ Got image URL: {image_url[:100]}...")

                # Upload to S3
                logger.info(f"  📤 Uploading to S3...")
                from app.utils.s3_storage import get_storage_manager
                storage = get_storage_manager()
                s3_key = await storage.download_and_upload_from_url(
                    source_url=image_url,
                    folder='products/generated'
                )

                if not s3_key:
                    logger.error(f"  ❌ S3 upload failed!")
                    continue

                logger.info(f"  ✅ S3 uploaded: {s3_key}")
                
                # ✅ CRITICAL FIX: Create artwork record FIRST
                artwork = await self.db_pool.fetchrow("""
                    INSERT INTO artwork (
                        prompt,
                        provider,
                        style,
                        image_url,
                        generation_cost,
                        quality_score,
                        trend_id,
                        created_at,
                        metadata
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), $8)
                    RETURNING *
                """,
                    result.get('prompt', f"{keyword} {style} style"),
                    result.get('provider', result.get('model_used', 'replicate')),
                    style,
                    s3_key,  # ✅ Store S3 key in artwork table
                    result.get('generation_cost', 0.003),
                    result.get('quality_score', 8.0),
                    trend['id'],
                    json.dumps({
                        'model_key': result.get('model_key'),
                        'model_used': result.get('model_used'),
                        'keyword': keyword,
                        'generated_at': datetime.now().isoformat()
                    })
                )
                
                logger.info(f"  ✅ Created artwork record ID: {artwork['id']}")
                
                # ✅ Now create product linked to artwork
                product = await self.db_pool.fetchrow("""
                    INSERT INTO products (
                        title,
                        description,
                        tags,
                        category,
                        trend_id,
                        style,
                        artwork_id,
                        base_price,
                        status,
                        created_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
                    RETURNING *
                """,
                    f"{keyword.title()} - {style.title()} Art",
                    f"Beautiful {style} style artwork featuring {keyword}. Perfect for home decor.",
                    json.dumps([keyword, style, 'wall art', 'home decor']),
                    trend.get('category', 'art'),
                    trend['id'],
                    style,
                    artwork['id'],  # ✅ Link to artwork record
                    19.99,  # Default base price
                    'active'
                )
                
                products.append(dict(product))
                logger.info(f"  ✓ Created product: {product['id']} with artwork: {artwork['id']}")
                
            except Exception as e:
                logger.error(f"  ❌ Error generating {style}: {e}")
                logger.exception("Full traceback:")
                continue
        
        logger.info(f"✅ Generated {len(products)} products for {keyword}")
        return products
    
    async def generate_single_product(
        self,
        keyword: str,
        style: str,
        category: str = "art"
    ) -> Optional[Dict]:
        """Generate a single product"""
        try:
            # Generate image - returns dict with 'image_url' key
            result = await self.ai_generator.generate_image(
                prompt=f"{keyword}, {style} style, high quality",
                style=style,
                keyword=keyword
            )
            
            # Extract URL string
            image_url = result['image_url']
            
            # Upload to S3
            from app.utils.s3_storage import get_storage_manager
            storage = get_storage_manager()
            s3_key = await storage.download_and_upload_from_url(
                source_url=image_url,
                folder=f"products/{keyword.replace(' ', '-')}"
            )
            
            # ✅ Create artwork record first
            artwork = await self.db_pool.fetchrow("""
                INSERT INTO artwork (
                    prompt, provider, style, image_url,
                    generation_cost, quality_score, created_at, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, NOW(), $7)
                RETURNING *
            """,
                f"{keyword} {style} style",
                result.get('provider', 'replicate'),
                style,
                s3_key,
                result.get('generation_cost', 0.003),
                result.get('quality_score', 8.0),
                json.dumps({'keyword': keyword})
            )
            
            # ✅ Create product linked to artwork
            product = await self.db_pool.fetchrow("""
                INSERT INTO products (
                    title, description, tags, category,
                    style, artwork_id, base_price, status, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
                RETURNING *
            """,
                f"{keyword.title()} - {style.title()}",
                f"{style.title()} style {keyword} artwork",
                json.dumps([keyword, style]),
                category,
                style,
                artwork['id'],  # ✅ Link to artwork
                19.99,
                'active'
            )
            
            return dict(product)
            
        except Exception as e:
            logger.error(f"Error generating product: {e}")
            logger.exception("Full traceback:")
            return None
