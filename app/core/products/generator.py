import asyncio
from typing import List, Dict, Optional
from loguru import logger
from datetime import datetime

from app.database import DatabasePool
from app.core.ai.generator import get_ai_generator
from app.core.ai.prompt_templates import get_pricing_for_style
from app.utils.helpers import generate_sku


class ProductGenerator:
    """Generate POD products from trends with intelligent AI model selection"""
    
    ALL_STYLES = [
        'minimalist', 'abstract', 'vintage', 'watercolor',
        'line_art', 'photography', 'typography', 'botanical'
    ]
    
    def __init__(self, db_pool: DatabasePool, testing_mode: bool = False, budget_mode: str = "balanced"):
        """
        Initialize product generator
        
        Args:
            db_pool: Database connection pool
            testing_mode: If True, use cheapest models for testing
            budget_mode: "cheap" | "balanced" | "quality" - affects model selection
        """
        self.db_pool = db_pool
        self.ai_generator = get_ai_generator(testing_mode=testing_mode, budget_mode=budget_mode)
        self.testing_mode = testing_mode
        self.budget_mode = budget_mode
        
        logger.info(f"📦 Product Generator initialized - Testing: {testing_mode}, Budget: {budget_mode}")
    
    async def generate_products_from_trend(
        self,
        trend_id: int,
        styles: Optional[List[str]] = None,
        upscale: bool = False
    ) -> List[Dict]:
        """
        Generate products from a single trend in multiple styles
        Each style automatically gets the best AI model
        
        Args:
            trend_id: ID of the trend
            styles: List of styles (or None for all)
            upscale: Whether to upscale for print
            
        Returns:
            List of created products with model selection details
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
        logger.info(f"⚙️ Mode: {'Testing' if self.testing_mode else self.budget_mode.title()}")
        
        products = []
        generation_stats = {
            'total_cost': 0,
            'models_used': {},
            'generation_times': []
        }
        
        for style in styles_to_generate:
            try:
                start_time = datetime.utcnow()
                logger.info(f"  → Creating {style} version...")
                
                # Generate artwork (model is automatically selected)
                artwork_data = await self.ai_generator.generate_product_artwork(
                    keyword=keyword,
                    style=style,
                    upscale_for_print=upscale
                )
                
                generation_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Track statistics
                generation_stats['total_cost'] += artwork_data.get('generation_cost', 0)
                model_used = artwork_data.get('model_key', 'unknown')
                generation_stats['models_used'][model_used] = generation_stats['models_used'].get(model_used, 0) + 1
                generation_stats['generation_times'].append(generation_time)
                
                # Log model selection
                logger.info(f"  🤖 Model: {model_used} (${artwork_data.get('generation_cost', 0)})")
                logger.info(f"  💡 Why: {', '.join(artwork_data.get('selection_reasoning', []))}")
                
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
                    'style': style,
                    'model_used': model_used,
                    'generation_cost': artwork_data.get('generation_cost', 0),
                    'quality_score': artwork_data.get('quality_score', 0),
                    'generation_time': generation_time
                })
                
                logger.info(f"  ✅ Product created: ID {product_id} (took {generation_time:.1f}s)")
                
            except Exception as e:
                logger.error(f"  ❌ Failed to create {style} product: {e}")
                continue
        
        # Log summary statistics
        if products:
            avg_time = sum(generation_stats['generation_times']) / len(generation_stats['generation_times'])
            logger.info(f"\n📊 Generation Summary for '{keyword}':")
            logger.info(f"  ✅ Products created: {len(products)}")
            logger.info(f"  💰 Total cost: ${generation_stats['total_cost']:.4f}")
            logger.info(f"  ⏱️  Average time: {avg_time:.1f}s per image")
            logger.info(f"  🤖 Models used: {dict(generation_stats['models_used'])}")
        
        return products
    
    async def _save_artwork(
        self,
        trend_id: int,
        artwork_data: Dict
    ) -> int:
        """Save generated artwork to database with model selection details"""
        
        # For now, we'll just use the temporary URL
        # You can add Cloudflare R2 storage later
        final_url = artwork_data['image_url']
        
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
            final_url,
            artwork_data.get('generation_cost', 0.04 if not self.testing_mode else 0.003),
            artwork_data.get('quality_score', 9.0),
            trend_id,
            {
                'original_url': artwork_data['image_url'],
                'print_ready': artwork_data.get('print_ready', False),
                'generated_at': artwork_data['generated_at'],
                'dimensions': artwork_data['dimensions'],
                'model_key': artwork_data.get('model_key', 'unknown'),
                'selection_reasoning': artwork_data.get('selection_reasoning', []),
                'keyword': artwork_data.get('keyword', '')
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
        Intelligently selects best AI model for each style
        
        Args:
            limit: Number of trends to process
            min_trend_score: Minimum trend score
            upscale: Whether to upscale images
            
        Returns:
            Summary dict with statistics including model usage and costs
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
        logger.info(f"⚙️ Mode: {'Testing' if self.testing_mode else self.budget_mode.title()}")
        
        total_products = 0
        total_cost = 0
        all_models_used = {}
        
        for trend in trends:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing: {trend['keyword']} (Score: {trend['trend_score']})")
            logger.info(f"{'='*60}")
            
            products = await self.generate_products_from_trend(
                trend_id=trend['id'],
                upscale=upscale
            )
            
            # Aggregate statistics
            for product in products:
                total_products += 1
                total_cost += product.get('generation_cost', 0)
                model = product.get('model_used', 'unknown')
                all_models_used[model] = all_models_used.get(model, 0) + 1
            
            # Small delay between trends
            await asyncio.sleep(2)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ BATCH COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"📦 Products created: {total_products} from {len(trends)} trends")
        logger.info(f"💰 Total cost: ${total_cost:.4f}")
        logger.info(f"📊 Average cost per product: ${total_cost/total_products:.4f}" if total_products > 0 else "")
        logger.info(f"🤖 Models used: {dict(all_models_used)}")
        logger.info(f"{'='*60}\n")
        
        return {
            'trends_processed': len(trends),
            'products_created': total_products,
            'styles_per_trend': len(self.ALL_STYLES),
            'total_cost': round(total_cost, 4),
            'avg_cost_per_product': round(total_cost / total_products, 4) if total_products > 0 else 0,
            'models_used': all_models_used,
            'mode': 'testing' if self.testing_mode else self.budget_mode
        }
