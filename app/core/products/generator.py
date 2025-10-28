"""
Product Generator - Creates canvas wall art products from trending keywords
Generates multiple designs per keyword based on search volume
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.product import Product
from app.models.trend import Trend
from app.core.artwork.generator import ArtworkGenerator
from app.utils.s3_storage import S3StorageManager

logger = logging.getLogger(__name__)

class ProductGenerator:
    """Generates products from trending keywords with volume-based design counts"""
    
    # Design counts based on search volume
    DESIGNS_PER_VOLUME = {
        "high": 100,      # 10k+ searches/month → 100 designs
        "medium": 50,     # 1k-10k searches/month → 50 designs
        "low": 25,        # 100-1k searches/month → 25 designs
        "unknown": 10     # No data → 10 designs (conservative)
    }
    
    # Canvas formats and their pricing multipliers
    CANVAS_FORMATS = {
        "single": {
            "name": "Single Canvas",
            "panels": 1,
            "dimensions": ["12x16", "16x20", "18x24", "24x36"],
            "price_multiplier": 1.0
        },
        "diptych": {
            "name": "2-Panel Diptych",
            "panels": 2,
            "dimensions": ["12x16", "16x20", "20x30"],
            "price_multiplier": 1.8
        },
        "triptych": {
            "name": "3-Panel Triptych",
            "panels": 3,
            "dimensions": ["12x16", "16x20", "20x30"],
            "price_multiplier": 2.5
        }
    }
    
    # Art styles for variety
    ART_STYLES = [
        "minimalist",
        "abstract",
        "geometric",
        "watercolor",
        "vintage",
        "modern",
        "bohemian",
        "rustic"
    ]
    
    def __init__(self, db: Session):
        self.db = db
        self.artwork_generator = ArtworkGenerator()
        self.s3_storage = S3StorageManager()
    
    def get_designs_needed(self, search_volume: Optional[str]) -> int:
        """
        Determine how many designs to create based on search volume
        
        Args:
            search_volume: "high", "medium", "low", or None
            
        Returns:
            Number of designs to create
        """
        if not search_volume:
            return self.DESIGNS_PER_VOLUME["unknown"]
        
        volume = search_volume.lower()
        return self.DESIGNS_PER_VOLUME.get(volume, self.DESIGNS_PER_VOLUME["unknown"])
    
    async def generate_products_for_trend(
        self, 
        trend: Trend,
        max_designs: Optional[int] = None
    ) -> List[Product]:
        """
        Generate multiple product designs for a single trend
        
        Args:
            trend: The trend to generate products for
            max_designs: Optional limit on number of designs (for testing)
            
        Returns:
            List of created products
        """
        logger.info(f"🎨 Generating products for keyword: {trend.keyword}")
        logger.info(f"   Search volume: {trend.search_volume or 'unknown'}")
        
        # Determine how many designs to create
        designs_needed = self.get_designs_needed(trend.search_volume)
        if max_designs:
            designs_needed = min(designs_needed, max_designs)
        
        logger.info(f"   Creating {designs_needed} designs")
        
        products = []
        
        for design_num in range(1, designs_needed + 1):
            logger.info(f"   Design {design_num}/{designs_needed}")
            
            # Rotate through art styles for variety
            style = self.ART_STYLES[(design_num - 1) % len(self.ART_STYLES)]
            
            # Create products for each canvas format
            for format_key, format_config in self.CANVAS_FORMATS.items():
                try:
                    product = await self._create_product_variant(
                        trend=trend,
                        format_key=format_key,
                        format_config=format_config,
                        style=style,
                        design_number=design_num
                    )
                    
                    if product:
                        products.append(product)
                        logger.info(f"      ✅ Created {format_config['name']} ({style})")
                
                except Exception as e:
                    logger.error(f"      ❌ Failed to create {format_key}: {e}")
                    continue
        
        logger.info(f"✅ Generated {len(products)} products for '{trend.keyword}'")
        return products
    
    async def _create_product_variant(
        self,
        trend: Trend,
        format_key: str,
        format_config: Dict,
        style: str,
        design_number: int
    ) -> Optional[Product]:
        """Create a single product variant"""
        
        # Generate artwork
        prompt = self._create_prompt(
            keyword=trend.keyword,
            style=style,
            format_type=format_key,
            panels=format_config["panels"]
        )
        
        logger.info(f"         Generating {style} artwork...")
        artwork_url = await self.artwork_generator.generate_artwork(prompt)
        
        if not artwork_url:
            logger.error(f"         Failed to generate artwork")
            return None
        
        # Upload to S3
        logger.info(f"         Uploading to S3...")
        s3_key = await self.s3_storage.upload_from_url(
            url=artwork_url,
            folder=f"products/{trend.keyword.replace(' ', '-')}"
        )
        
        if not s3_key:
            logger.error(f"         Failed to upload to S3")
            return None
        
        # Create product in database for each dimension
        products_created = []
        for dimension in format_config["dimensions"]:
            base_price = self._calculate_price(dimension, format_config["panels"])
            
            product = Product(
                title=f"{trend.keyword.title()} - {format_config['name']} - {style.title()} #{design_number}",
                description=self._generate_description(
                    keyword=trend.keyword,
                    style=style,
                    format_name=format_config['name'],
                    dimension=dimension
                ),
                keyword=trend.keyword,
                category=trend.category or "Canvas Wall Art",
                style=style,
                canvas_format=format_key,
                panels=format_config["panels"],
                dimensions=dimension,
                price=base_price,
                image_s3_key=s3_key,
                design_number=design_number,
                status="pending",
                created_at=datetime.now(timezone.utc)
            )
            
            self.db.add(product)
            products_created.append(product)
        
        self.db.commit()
        
        # Return the first product as representative
        return products_created[0] if products_created else None
    
    def _create_prompt(
        self, 
        keyword: str, 
        style: str, 
        format_type: str,
        panels: int
    ) -> str:
        """Create AI prompt for artwork generation"""
        
        base_prompt = f"Create a beautiful {style} style canvas wall art"
        
        if panels == 1:
            prompt = f"{base_prompt} with the theme '{keyword}'"
        elif panels == 2:
            prompt = f"{base_prompt} split into 2 panels (diptych) with the theme '{keyword}', ensuring visual continuity across both panels"
        else:  # 3 panels
            prompt = f"{base_prompt} split into 3 panels (triptych) with the theme '{keyword}', with a cohesive flow from left to right"
        
        # Add style-specific guidance
        style_guidance = {
            "minimalist": "simple lines, clean composition, lots of white space",
            "abstract": "bold colors, expressive shapes, dynamic composition",
            "geometric": "precise shapes, symmetrical patterns, modern aesthetic",
            "watercolor": "soft blended colors, organic flowing forms",
            "vintage": "aged texture, muted tones, nostalgic feel",
            "modern": "contemporary design, sleek lines, trendy colors",
            "bohemian": "eclectic patterns, warm earthy tones, free-spirited",
            "rustic": "natural textures, wood tones, cozy farmhouse aesthetic"
        }
        
        if style in style_guidance:
            prompt += f", {style_guidance[style]}"
        
        prompt += ". High quality, suitable for home decor, artistic, visually striking."
        
        return prompt
    
    def _calculate_price(self, dimension: str, panels: int) -> float:
        """Calculate base price based on dimension and panel count"""
        
        # Base prices for single canvas
        size_prices = {
            "12x16": 29.99,
            "16x20": 39.99,
            "18x24": 49.99,
            "20x30": 59.99,
            "24x36": 79.99
        }
        
        base = size_prices.get(dimension, 49.99)
        
        # Multiply by panel count (with slight discount)
        if panels == 2:
            return round(base * 1.8, 2)  # Diptych
        elif panels == 3:
            return round(base * 2.5, 2)  # Triptych
        else:
            return base
    
    def _generate_description(
        self,
        keyword: str,
        style: str,
        format_name: str,
        dimension: str
    ) -> str:
        """Generate product description"""
        
        return f"""Beautiful {style} style {format_name.lower()} featuring '{keyword}'. 

Perfect for living room, bedroom, office, or any space that needs a stylish focal point. 

Features:
- High-quality canvas print
- {dimension} inches
- Ready to hang
- Fade-resistant inks
- {format_name} configuration

Add a touch of artistic elegance to your home decor with this stunning piece."""
    
    async def generate_batch(
        self,
        limit: int = 10,
        max_designs_per_keyword: Optional[int] = None
    ) -> Dict:
        """
        Generate products for multiple trends
        
        Args:
            limit: Maximum number of trends to process
            max_designs_per_keyword: Optional limit on designs per keyword (for testing)
            
        Returns:
            Summary statistics
        """
        logger.info(f"🚀 Starting batch generation for {limit} trends")
        
        # Get trends that need products
        stmt = (
            select(Trend)
            .where(Trend.status == "active")
            .order_by(Trend.search_volume.desc(), Trend.created_at.desc())
            .limit(limit)
        )
        
        trends = self.db.execute(stmt).scalars().all()
        
        if not trends:
            logger.info("No active trends found")
            return {
                "trends_processed": 0,
                "products_created": 0,
                "message": "No active trends to process"
            }
        
        logger.info(f"Found {len(trends)} trends to process")
        
        total_products = 0
        
        for i, trend in enumerate(trends, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Trend {i}/{len(trends)}: {trend.keyword}")
            logger.info(f"{'='*60}")
            
            try:
                products = await self.generate_products_for_trend(
                    trend=trend,
                    max_designs=max_designs_per_keyword
                )
                total_products += len(products)
                
                # Update trend status
                trend.product_count = len(products)
                trend.last_generated_at = datetime.now(timezone.utc)
                self.db.commit()
                
            except Exception as e:
                logger.error(f"❌ Failed to generate products for '{trend.keyword}': {e}")
                continue
        
        summary = {
            "trends_processed": len(trends),
            "products_created": total_products,
            "average_per_trend": round(total_products / len(trends), 1) if trends else 0
        }
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ BATCH COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Trends processed: {summary['trends_processed']}")
        logger.info(f"Products created: {summary['products_created']}")
        logger.info(f"Average per trend: {summary['average_per_trend']}")
        
        return summary
