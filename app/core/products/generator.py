# COMPLETE app/core/products/generator.py WITH FIX
# Replace your current generator.py with this

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime

from app.database import DatabasePool
from app.core.ai.generator import AIGenerator
from app.utils.s3_storage import upload_image, download_and_upload_from_url

logger = logging.getLogger(__name__)


class ProductGenerator:
    def __init__(self, db_pool: DatabasePool):
        self.db_pool = db_pool
        self.ai_generator = AIGenerator()
    
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
            'modern'
        ][:num_styles]
        
        products = []
        
        for style in styles:
            try:
                logger.info(f"  Generating {style} style...")
                
                # Generate AI image
                prompt = f"{keyword}, {style} style, high quality, professional"
                image_url = await self.ai_generator.generate_image(
                    prompt=prompt,
                    style=style,
                    keyword=keyword
                )
                
                # Upload to S3
                logger.info(f"  Uploading to S3...")
                s3_url = await download_and_upload_from_url(
                    image_url,
                    f"products/{keyword.replace(' ', '-')}"
                )
                
                # Create product in database
                # FIX: Convert images to JSON string, not dict
                images_data = {
                    'image_url': s3_url,
                    'style': style,
                    'keyword': keyword,
                    'generated_at': datetime.now().isoformat()
                }
                images_json = json.dumps(images_data)  # <-- FIX: Convert to JSON string
                
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
                    images_json,  # <-- FIX: Pass JSON string, not dict
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
            prompt = f"{keyword}, {style} style, high quality"
            image_url = await self.ai_generator.generate_image(
                prompt=prompt,
                style=style,
                keyword=keyword
            )
            
            # Upload to S3
            s3_url = await download_and_upload_from_url(
                image_url,
                f"products/{keyword.replace(' ', '-')}"
            )
            
            # Create product
            images_json = json.dumps({'image_url': s3_url})  # JSON string
            
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
                images_json,  # JSON string
                'active'
            )
            
            return dict(product)
            
        except Exception as e:
            logger.error(f"Error generating product: {e}")
            return None
