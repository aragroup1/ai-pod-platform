from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Optional
from loguru import logger

from app.database import DatabasePool
from app.dependencies import get_db_pool
from app.core.products.generator import ProductGenerator

router = APIRouter()


class GenerateRequest(BaseModel):
    trend_id: int
    styles: Optional[List[str]] = None
    upscale: bool = False
    budget_mode: str = "balanced"  # "cheap" | "balanced" | "quality"


class BatchGenerateRequest(BaseModel):
    limit: int = 10
    min_trend_score: float = 6.0
    upscale: bool = False
    testing_mode: bool = True  # Start with testing mode
    budget_mode: str = "balanced"  # "cheap" | "balanced" | "quality"


@router.post("/generate")
async def generate_products_from_trend(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    Generate products from a single trend
    Intelligently selects best AI model for each style
    Runs in background
    
    Budget modes:
    - "cheap": Always use FLUX Schnell ($0.003/image)
    - "balanced": Mix of models based on style ($0.003-$0.04/image)
    - "quality": Prioritize quality over cost ($0.025-$0.04/image)
    """
    try:
        generator = ProductGenerator(
            db_pool, 
            testing_mode=False,
            budget_mode=request.budget_mode
        )
        
        background_tasks.add_task(
            generator.generate_products_from_trend,
            trend_id=request.trend_id,
            styles=request.styles,
            upscale=request.upscale
        )
        
        return {
            "message": "Product generation started",
            "trend_id": request.trend_id,
            "budget_mode": request.budget_mode,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error starting generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-generate")
async def batch_generate_products(
    request: BatchGenerateRequest,
    background_tasks: BackgroundTasks,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    Generate products for multiple trends with intelligent model selection
    This will create LIMIT × 8 products (8 styles per trend)
    
    Each style automatically gets the best AI model:
    - Typography → Ideogram Turbo (best text rendering)
    - Photography → FLUX Pro (best photorealism)
    - Watercolor/Botanical → FLUX Dev (best artistic quality)
    - Minimalist → FLUX Schnell (fast and cheap)
    
    Budget modes:
    - "cheap": ~$0.024 for 8 products (all FLUX Schnell)
    - "balanced": ~$0.20 for 8 products (smart mix)
    - "quality": ~$0.32 for 8 products (premium models)
    
    Testing mode: Always uses FLUX Schnell regardless of budget_mode
    """
    try:
        generator = ProductGenerator(
            db_pool,
            testing_mode=request.testing_mode,
            budget_mode=request.budget_mode
        )
        
        background_tasks.add_task(
            generator.batch_generate_from_trends,
            limit=request.limit,
            min_trend_score=request.min_trend_score,
            upscale=request.upscale
        )
        
        expected_products = request.limit * 8  # 8 styles per trend
        
        # Cost estimates
        if request.testing_mode:
            estimated_cost = expected_products * 0.003
            cost_note = "Testing mode: All FLUX Schnell"
        elif request.budget_mode == "cheap":
            estimated_cost = expected_products * 0.003
            cost_note = "Cheap mode: All FLUX Schnell"
        elif request.budget_mode == "balanced":
            estimated_cost = expected_products * 0.025  # Average mix
            cost_note = "Balanced mode: Smart model selection"
        else:  # quality
            estimated_cost = expected_products * 0.035  # Average premium
            cost_note = "Quality mode: Premium models"
        
        return {
            "message": "Batch generation started",
            "expected_products": expected_products,
            "trends_to_process": request.limit,
            "testing_mode": request.testing_mode,
            "budget_mode": request.budget_mode,
            "estimated_cost": f"${estimated_cost:.2f}",
            "cost_note": cost_note,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error starting batch generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_generation_status(db_pool: DatabasePool = Depends(get_db_pool)):
    """Get statistics about generated products"""
    try:
        stats = await db_pool.fetchrow(
            """
            SELECT 
                COUNT(DISTINCT p.id) as total_products,
                COUNT(DISTINCT a.trend_id) as trends_with_products,
                COUNT(DISTINCT a.id) as total_artwork
            FROM products p
            LEFT JOIN artwork a ON p.artwork_id = a.id
            """
        )
        
        trends_without = await db_pool.fetchval(
            """
            SELECT COUNT(*)
            FROM trends t
            LEFT JOIN artwork a ON a.trend_id = t.id
            WHERE a.id IS NULL
            AND t.trend_score >= 6.0
            """
        )
        
        return {
            "total_products": stats['total_products'],
            "trends_with_products": stats['trends_with_products'],
            "total_artwork": stats['total_artwork'],
            "trends_awaiting_generation": trends_without
        }
        
    except Exception as e:
        logger.error(f"Error getting generation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-info")
async def get_model_info():
    """
    Get information about available AI models and intelligent selection
    """
    return {
        "intelligent_selection": True,
        "description": "System automatically selects the best AI model for each art style",
        "models": {
            "flux-schnell": {
                "cost": 0.003,
                "quality": "7/10",
                "speed": "Very Fast (5s)",
                "best_for": ["minimalist", "abstract", "testing"],
                "text_rendering": "5/10",
                "photorealism": "6/10"
            },
            "flux-dev": {
                "cost": 0.025,
                "quality": "8/10",
                "speed": "Fast (8s)",
                "best_for": ["watercolor", "line_art", "botanical"],
                "text_rendering": "7/10",
                "photorealism": "8/10"
            },
            "flux-pro": {
                "cost": 0.04,
                "quality": "9/10",
                "speed": "Medium (10s)",
                "best_for": ["photography", "vintage", "high-quality"],
                "text_rendering": "7/10",
                "photorealism": "9/10"
            },
            "ideogram-turbo": {
                "cost": 0.025,
                "quality": "8/10",
                "speed": "Fast (6s)",
                "best_for": ["typography", "quotes", "text-heavy"],
                "text_rendering": "10/10 ⭐",
                "photorealism": "7/10"
            }
        },
        "budget_modes": {
            "cheap": {
                "description": "Always use FLUX Schnell",
                "avg_cost_per_product": "$0.003",
                "avg_cost_8_styles": "$0.024"
            },
            "balanced": {
                "description": "Smart mix based on style (Recommended)",
                "avg_cost_per_product": "$0.025",
                "avg_cost_8_styles": "$0.20"
            },
            "quality": {
                "description": "Prioritize quality over cost",
                "avg_cost_per_product": "$0.035",
                "avg_cost_8_styles": "$0.28"
            }
        },
        "selection_rules": {
            "typography": "Uses Ideogram Turbo (best text rendering)",
            "photography": "Uses FLUX Pro (best photorealism)",
            "watercolor_botanical_line_art": "Uses FLUX Dev (best artistic quality)",
            "minimalist": "Uses FLUX Schnell (fast and clean)",
            "vintage_abstract": "Uses FLUX Pro/Dev based on budget mode"
        }
    }


@router.post("/estimate-cost")
async def estimate_generation_cost(
    request: BatchGenerateRequest,
    db_pool: DatabasePool = Depends(get_db_pool)
):
    """
    Estimate the cost of batch generation before running it
    Useful for budget planning
    """
    try:
        # Get trends that would be generated
        trends = await db_pool.fetch(
            """
            SELECT t.keyword
            FROM trends t
            LEFT JOIN artwork a ON a.trend_id = t.id
            WHERE a.id IS NULL
            AND t.trend_score >= $1
            ORDER BY t.trend_score DESC
            LIMIT $2
            """,
            request.min_trend_score,
            request.limit
        )
        
        if not trends:
            return {
                "message": "No trends available for generation",
                "estimated_cost": "$0.00",
                "products": 0
            }
        
        # Estimate based on budget mode
        styles = ['minimalist', 'abstract', 'vintage', 'watercolor', 
                  'line_art', 'photography', 'typography', 'botanical']
        
        total_products = len(trends) * len(styles)
        
        if request.testing_mode:
            cost_per_image = 0.003
            mode_description = "Testing mode (all FLUX Schnell)"
        elif request.budget_mode == "cheap":
            cost_per_image = 0.003
            mode_description = "Cheap mode (all FLUX Schnell)"
        elif request.budget_mode == "balanced":
            # Estimate mix: 2 ideogram, 2 flux-pro, 3 flux-dev, 1 flux-schnell
            cost_per_image = (2*0.025 + 2*0.04 + 3*0.025 + 1*0.003) / 8
            mode_description = "Balanced mode (intelligent mix)"
        else:  # quality
            # Estimate: 2 ideogram, 4 flux-pro, 2 flux-dev
            cost_per_image = (2*0.025 + 4*0.04 + 2*0.025) / 8
            mode_description = "Quality mode (premium models)"
        
        total_cost = total_products * cost_per_image
        
        return {
            "trends_to_process": len(trends),
            "products_per_trend": len(styles),
            "total_products": total_products,
            "mode": mode_description,
            "cost_per_image": f"${cost_per_image:.4f}",
            "estimated_total_cost": f"${total_cost:.2f}",
            "keywords": [t['keyword'] for t in trends[:5]],  # Show first 5
            "note": "This is an estimate. Actual cost may vary slightly."
        }
        
    except Exception as e:
        logger.error(f"Error estimating cost: {e}")
        raise HTTPException(status_code=500, detail=str(e))
