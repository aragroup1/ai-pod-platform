# app/api/v1/listing_optimizer.py
"""
Listing Optimization API
Optimizes approved products for Shopify with SEO and mockup images

Workflow:
1. Product gets approved
2. Generate SEO-optimized title, description, tags
3. Generate lifestyle mockup images (optional)
4. Ready for Shopify sync
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from loguru import logger
import os
import json

from app.database import DatabasePool
from app.dependencies import get_db_pool

router = APIRouter()


class OptimizationRequest(BaseModel):
    product_id: int
    generate_mockups: bool = True
    seo_level: str = "standard"  # "basic", "standard", "premium"


class BatchOptimizationRequest(BaseModel):
    product_ids: List[int]
    generate_mockups: bool = True
    seo_level: str = "standard"


@router.post("/optimize")
async def optimize_listing(
    request: OptimizationRequest,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    Optimize a single approved product for Shopify listing
    
    Steps:
    1. Get product details + artwork
    2. Generate SEO-optimized title, description, tags
    3. Generate lifestyle mockup images (if requested)
    4. Update product with optimized data
    5. Mark as ready for Shopify sync
    """
    try:
        # Get product with artwork details
        product = await db_pool.fetchrow("""
            SELECT 
                p.*,
                a.style,
                a.prompt,
                a.image_url,
                t.keyword,
                t.category,
                t.search_volume
            FROM products p
            LEFT JOIN artwork a ON p.artwork_id = a.id
            LEFT JOIN trends t ON a.trend_id = t.id
            WHERE p.id = $1 AND p.status = 'approved'
        """, request.product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found or not approved")
        
        logger.info(f"🎯 Optimizing product {request.product_id}: {product['title']}")
        
        # Step 1: Generate SEO-optimized content
        optimized_content = await generate_seo_content(
            keyword=product['keyword'],
            style=product['style'],
            category=product['category'],
            current_title=product['title'],
            seo_level=request.seo_level
        )
        
        # Step 2: Generate mockup images (optional)
        mockup_urls = []
        if request.generate_mockups and product['image_url']:
            logger.info(f"📸 Generating lifestyle mockups...")
            mockup_urls = await generate_lifestyle_mockups(
                artwork_url=product['image_url'],
                style=product['style']
            )
        
        # Step 3: Update product with optimized data
        updated_metadata = product.get('metadata', {})
        updated_metadata.update({
            'seo_optimized': True,
            'seo_level': request.seo_level,
            'mockups_generated': len(mockup_urls),
            'optimization_date': 'NOW()',
            'original_title': product['title']
        })
        
        # Combine original image + mockups
        all_images = [product['image_url']] + mockup_urls if mockup_urls else [product['image_url']]
        
        await db_pool.execute("""
            UPDATE products
            SET 
                title = $1,
                description = $2,
                tags = $3,
                metadata = $4,
                status = 'optimized'::product_status,
                updated_at = NOW()
            WHERE id = $5
        """,
            optimized_content['title'],
            optimized_content['description'],
            optimized_content['tags'],
            json.dumps(updated_metadata),
            request.product_id
        )
        
        logger.info(f"✅ Product {request.product_id} optimized successfully")
        
        return {
            "success": True,
            "product_id": request.product_id,
            "optimizations": {
                "title": {
                    "original": product['title'],
                    "optimized": optimized_content['title'],
                    "improvement": "SEO keywords added"
                },
                "description": {
                    "length": len(optimized_content['description']),
                    "features": "bullet points, keywords, benefits"
                },
                "tags": {
                    "count": len(optimized_content['tags']),
                    "tags": optimized_content['tags']
                },
                "mockups": {
                    "generated": len(mockup_urls),
                    "urls": mockup_urls
                }
            },
            "ready_for_shopify": True,
            "estimated_seo_score": optimized_content.get('seo_score', 85),
            "cost": optimized_content.get('cost', 0.0004),
            "model": optimized_content.get('model', 'gpt-4o-mini')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Optimization error: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-optimize")
async def batch_optimize_listings(
    request: BatchOptimizationRequest,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Optimize multiple products at once"""
    try:
        results = []
        
        for product_id in request.product_ids:
            try:
                result = await optimize_listing(
                    OptimizationRequest(
                        product_id=product_id,
                        generate_mockups=request.generate_mockups,
                        seo_level=request.seo_level
                    ),
                    db_pool
                )
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to optimize product {product_id}: {e}")
                results.append({
                    "success": False,
                    "product_id": product_id,
                    "error": str(e)
                })
        
        successful = sum(1 for r in results if r.get('success'))
        
        return {
            "success": True,
            "total": len(request.product_ids),
            "successful": successful,
            "failed": len(request.product_ids) - successful,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Batch optimization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending-optimization")
async def get_pending_optimization(
    limit: int = 50,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """Get products that are approved but not yet optimized"""
    try:
        products = await db_pool.fetch("""
            SELECT 
                p.id,
                p.title,
                p.sku,
                p.base_price,
                a.style,
                a.image_url,
                t.keyword,
                t.search_volume
            FROM products p
            LEFT JOIN artwork a ON p.artwork_id = a.id
            LEFT JOIN trends t ON a.trend_id = t.id
            WHERE p.status = 'approved'
            ORDER BY t.search_volume DESC NULLS LAST, p.created_at DESC
            LIMIT $1
        """, limit)
        
        return {
            "products": [dict(p) for p in products],
            "total": len(products),
            "ready_for_optimization": len(products)
        }
        
    except Exception as e:
        logger.error(f"Error fetching pending products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# HELPER FUNCTIONS
# ==========================================

async def generate_seo_content(
    keyword: str,
    style: str,
    category: str,
    current_title: str,
    seo_level: str = "standard"
) -> dict:
    """
    Generate SEO-optimized content using OpenAI GPT-4o-mini
    
    Cost: ~$0.0004 per product (67x cheaper than Claude)
    Quality: Nearly identical for SEO tasks
    
    This uses the OpenAI API to generate:
    - SEO-friendly title
    - Detailed description with keywords
    - Relevant tags
    """
    
    # Check if OpenAI API key is available
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    if not openai_api_key:
        logger.warning("No OpenAI API key - using template-based optimization")
        return generate_template_seo(keyword, style, category, current_title)
    
    try:
        import openai
        
        client = openai.OpenAI(api_key=openai_api_key)
        
        prompt = f"""Generate SEO-optimized Shopify listing content for a print-on-demand product.

Product Details:
- Main Keyword: {keyword}
- Art Style: {style}
- Category: {category}
- Current Title: {current_title}
- SEO Level: {seo_level}

Generate:
1. SEO Title (60-80 chars, include main keyword naturally)
2. Product Description (150-250 words, engaging, keyword-rich)
3. Tags (10-15 relevant tags for Shopify)

Format as JSON:
{{
    "title": "SEO-optimized title here",
    "description": "Full description here with paragraphs",
    "tags": ["tag1", "tag2", ...],
    "seo_score": 85
}}

Make it:
- Customer-focused (benefits, not features)
- Natural keyword usage (not spammy)
- Compelling and conversion-focused
- Professional but approachable
"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # 67x cheaper than Claude
            messages=[
                {"role": "system", "content": "You are an expert e-commerce SEO copywriter specializing in Shopify listings for print-on-demand products."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        logger.info(f"✅ Generated SEO content via OpenAI GPT-4o-mini (cost: ~$0.0004)")
        
        return {
            "title": result.get("title", current_title)[:80],  # Shopify limit
            "description": result.get("description", ""),
            "tags": result.get("tags", [])[:15],  # Max 15 tags
            "seo_score": result.get("seo_score", 85),
            "cost": 0.0004,  # Approximate cost per product
            "model": "gpt-4o-mini"
        }
        
    except Exception as e:
        logger.warning(f"OpenAI API failed, using template: {e}")
        return generate_template_seo(keyword, style, category, current_title)


def generate_template_seo(keyword: str, style: str, category: str, current_title: str) -> dict:
    """Fallback template-based SEO generation (FREE)"""
    
    # Capitalize properly
    keyword_title = keyword.title()
    style_title = style.replace('_', ' ').title()
    
    # Generate title
    title_templates = [
        f"{keyword_title} {style_title} Wall Art Print - Premium Canvas",
        f"{keyword_title} Wall Art - {style_title} Canvas Print",
        f"Premium {keyword_title} {style_title} Art Print - Home Decor",
        f"{style_title} {keyword_title} Canvas - Modern Wall Art"
    ]
    
    title = title_templates[hash(keyword) % len(title_templates)]
    
    # Generate description
    description = f"""Transform your space with this stunning {keyword_title} wall art print.

Our premium {style_title.lower()} style artwork brings {keyword.lower()} to life with vibrant colors and exceptional detail. Perfect for living rooms, bedrooms, offices, or as a thoughtful gift.

✨ Product Features:
• Premium quality canvas print
• {style_title} artistic style
• Gallery-wrapped edges
• Ready to hang
• Fade-resistant inks
• Multiple sizes available

🎨 Why Choose This Art:
This {keyword.lower()} artwork adds a touch of elegance and personality to any room. The {style_title.lower()} design complements modern, contemporary, and traditional decor styles.

📦 Fast shipping and satisfaction guaranteed. Order your {keyword_title} wall art today and elevate your home decor!

Perfect for: Home decor, office art, bedroom wall art, living room decor, gift ideas, housewarming presents."""
    
    # Generate tags
    base_tags = [
        keyword.lower(),
        style.lower().replace('_', ' '),
        "wall art",
        "canvas print",
        "home decor",
        "modern art"
    ]
    
    category_tags = {
        'nature': ['landscape', 'nature art', 'outdoor'],
        'abstract': ['contemporary', 'modern', 'geometric'],
        'animals': ['wildlife', 'pet art', 'animal lover'],
        'typography': ['quote', 'text art', 'motivational'],
    }
    
    additional = category_tags.get(category.lower().split()[0], [])
    
    tags = base_tags + additional + [
        "art print",
        "interior design",
        "wall decor",
        f"{keyword} art"
    ]
    
    return {
        "title": title[:80],  # Shopify limit
        "description": description,
        "tags": list(set(tags))[:15],  # Remove duplicates, max 15
        "seo_score": 75,  # Template score
        "cost": 0.00,
        "model": "template"
    }


async def generate_lifestyle_mockups(artwork_url: str, style: str) -> List[str]:
    """
    Generate lifestyle mockup images showing artwork in room settings
    
    Options:
    1. Use Replicate API (SDXL Inpainting) - $0.01/image
    2. Use template overlays (free but less realistic)
    3. Skip for now and add later
    
    For MVP: Return empty list and implement later
    """
    
    # TODO: Implement mockup generation
    # For now, return empty list
    logger.info("Mockup generation not yet implemented - skipping")
    
    return []
    
    # Future implementation:
    """
    mockup_templates = [
        "living_room_wall",
        "bedroom_above_bed",
        "office_desk",
        "hallway_gallery"
    ]
    
    mockup_urls = []
    
    for template in mockup_templates[:2]:  # Generate 2 mockups
        mockup_url = await generate_single_mockup(
            artwork_url=artwork_url,
            template=template,
            style=style
        )
        if mockup_url:
            mockup_urls.append(mockup_url)
    
    return mockup_urls
    """


@router.get("/optimization-settings")
async def get_optimization_settings():
    """Get current optimization settings and costs"""
    return {
        "seo_levels": {
            "basic": {
                "description": "Template-based SEO (FREE)",
                "cost": 0.00,
                "features": ["Basic title", "Simple description", "Auto tags"],
                "model": "template"
            },
            "standard": {
                "description": "AI-enhanced SEO (OpenAI GPT-4o-mini)",
                "cost": 0.0004,
                "features": ["Optimized title", "Detailed description", "Strategic tags", "Keyword density"],
                "model": "gpt-4o-mini"
            },
            "premium": {
                "description": "AI + Mockups (Coming Soon)",
                "cost": 0.05,
                "features": ["Everything in Standard", "Lifestyle mockups", "A/B title variants", "Competitor analysis"],
                "model": "gpt-4o-mini + mockups"
            }
        },
        "mockup_generation": {
            "enabled": False,  # Not yet implemented
            "cost_per_mockup": 0.01,
            "recommended_count": 2,
            "templates": ["living_room", "bedroom", "office"]
        },
        "recommendations": {
            "for_high_volume_keywords": "standard",  # Was "premium", now just AI SEO
            "for_testing": "standard",
            "for_bulk_upload": "basic"
        },
        "cost_comparison": {
            "10_products": {
                "basic": "$0.00",
                "standard": "$0.004 (GPT-4o-mini)",
                "claude_alternative": "$0.10 (67x more expensive)"
            },
            "10000_products": {
                "basic": "$0.00",
                "standard": "$3.75 (GPT-4o-mini)",
                "claude_alternative": "$100 (67x more expensive)"
            }
        }
    }
