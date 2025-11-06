import logging
import json
from typing import Dict, List, Optional
from datetime import datetime

from app.database import DatabasePool
from app.utils.s3_storage import upload_image, download_and_upload_from_url

logger = logging.getLogger(__name__)


class ProductGenerator:
    def __init__(self, db_pool: DatabasePool):
        self.db_pool = db_pool
        # ✅ FIXED: Lazy import to avoid circular import
        self._ai_generator = None
    
    @property
    def ai_generator(self):
        """Lazy load AI generator to avoid circular import"""
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
                
                # Generate AI image
                result = await self.ai_generator.generate_image(
                    prompt=f"{keyword}, {style} style, high quality, professional",
                    style=style,
                    keyword=keyword
                )
                
                # Extract URL from result
                image_url = result['image_url']  # This is already a string
                
                # Upload to S3
                logger.info(f"  Uploading to S3...")
                s3_url = await download_and_upload_from_url(
                    image_url,
                    f"products/{keyword.replace(' ', '-')}"
                )
                
                # ✅ FIX: Convert images to JSON string before INSERT
                images_json = json.dumps({
                    'image_url': s3_url,
                    'style': style,
                    'keyword': keyword,
                    'generated_at': datetime.now().isoformat()
                })
                
                # Create product in database
                product = await self.db_pool.fetchrow("""
                    INSERT INTO products (
                        title,
                        description,
                        tags,
                        category,
                        trend_id,
                        style,
                        images,
                        status,
                        created_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
                    RETURNING *
                """,
                    f"{keyword.title()} - {style.title()} Art",
                    f"Beautiful {style} style artwork featuring {keyword}. Perfect for home decor.",
                    json.dumps([keyword, style, 'wall art', 'home decor']),
                    trend.get('category', 'art'),
                    trend['id'],
                    style,
                    images_json,  # ✅ FIXED: Pass JSON string, not dict
                    'active'
                )
                
                products.append(dict(product))
                logger.info(f"  ✓ Created product: {product['id']}")
                
            except Exception as e:
                logger.error(f"  ❌ Error generating {style}: {e}")
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
            # Generate image
            result = await self.ai_generator.generate_image(
                prompt=f"{keyword}, {style} style, high quality",
                style=style,
                keyword=keyword
            )
            
            image_url = result['image_url']
            
            # Upload to S3
            s3_url = await download_and_upload_from_url(
                image_url,
                f"products/{keyword.replace(' ', '-')}"
            )
            
            # ✅ FIX: Convert to JSON string
            images_json = json.dumps({'image_url': s3_url})
            
            # Create product
            product = await self.db_pool.fetchrow("""
                INSERT INTO products (
                    title, description, tags, category,
                    style, images, status, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
                RETURNING *
            """,
                f"{keyword.title()} - {style.title()}",
                f"{style.title()} style {keyword} artwork",
                json.dumps([keyword, style]),
                category,
                style,
                images_json,  # ✅ FIXED: JSON string
                'active'
            )
            
            return dict(product)
            
        except Exception as e:
            logger.error(f"Error generating product: {e}")
            return None
