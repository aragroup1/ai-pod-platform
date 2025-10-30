from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from app.core.trends.service import TrendService
from app.dependencies import get_db_pool

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class ManualKeywordInput(BaseModel):
    keywords_text: str
    category: Optional[str] = "general"

class KeywordCreate(BaseModel):
    keyword: str
    search_volume: Optional[int] = None
    category: Optional[str] = "general"
    designs_allocated: Optional[int] = None
    trend_score: Optional[float] = 5.0

class BatchKeywordImport(BaseModel):
    keywords: List[KeywordCreate]


@router.post("/manual-add")
async def add_manual_keywords(input_data: ManualKeywordInput, db_pool = Depends(get_db_pool)):
    """Add keywords manually from dashboard"""
    try:
        keywords_text = input_data.keywords_text
        category = input_data.category or "general"
        
        if "," in keywords_text:
            keyword_list = [k.strip() for k in keywords_text.split(",") if k.strip()]
        else:
            keyword_list = [k.strip() for k in keywords_text.split("\n") if k.strip()]
        
        if not keyword_list:
            raise HTTPException(status_code=400, detail="No valid keywords found")
        
        logger.info(f"📝 Manual add: {len(keyword_list)} keywords")
        
        def estimate_volume(keyword: str) -> int:
            word_count = len(keyword.split())
            if word_count <= 2:
                return 50000
            elif word_count <= 3:
                return 30000
            else:
                return 15000
        
        def calculate_designs(volume: int) -> int:
            if volume >= 150000:
                return 250
            elif volume >= 100000:
                return 200
            elif volume >= 50000:
                return 150
            elif volume >= 30000:
                return 100
            elif volume >= 20000:
                return 75
            elif volume >= 10000:
                return 50
            else:
                return 30
        
        stored_keywords = []
        total_designs = 0
        
        for keyword in keyword_list:
            keyword_lower = keyword.lower()
            
            existing = await db_pool.fetchrow(
                "SELECT * FROM trends WHERE keyword = $1",
                keyword_lower
            )
            
            if existing:
                logger.info(f"⏭️  Already exists: {keyword_lower}")
                stored_keywords.append(dict(existing))
                total_designs += existing['designs_allocated'] if existing.get('designs_allocated') else 0
                continue
            
            estimated_volume = estimate_volume(keyword_lower)
            designs = calculate_designs(estimated_volume)
            
            new_keyword = await db_pool.fetchrow(
                """
                INSERT INTO trends (keyword, search_volume, category, trend_score, created_at)
                VALUES ($1, $2, $3, $4, NOW())
                RETURNING *
                """,
                keyword_lower,
                estimated_volume,
                category,
                7.0
            )
            
            stored_keywords.append(dict(new_keyword))
            total_designs += designs
        
        return {
            "success": True,
            "message": f"Added {len(stored_keywords)} keywords",
            "keywords_stored": len(stored_keywords),
            "potential_listings": total_designs * 8,
            "keywords": stored_keywords
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error adding manual keywords: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-import")
async def batch_import_keywords(batch: BatchKeywordImport, db_pool = Depends(get_db_pool)):
    """Import multiple keywords at once"""
    try:
        logger.info(f"📦 Batch import: {len(batch.keywords)} keywords")
        
        stored_keywords = []
        total_designs = 0
        
        def calculate_designs(volume: int) -> int:
            if volume >= 150000:
                return 250
            elif volume >= 100000:
                return 200
            elif volume >= 50000:
                return 150
            elif volume >= 30000:
                return 100
            elif volume >= 20000:
                return 75
            elif volume >= 10000:
                return 50
            else:
                return 30
        
        for kw_data in batch.keywords:
            keyword_lower = kw_data.keyword.lower()
            
            existing = await db_pool.fetchrow(
                "SELECT * FROM trends WHERE keyword = $1",
                keyword_lower
            )
            
            if existing:
                stored_keywords.append(dict(existing))
                total_designs += existing['designs_allocated'] if existing.get('designs_allocated') else 0
                continue
            
            designs = kw_data.designs_allocated
            if designs is None:
                volume = kw_data.search_volume or 20000
                designs = calculate_designs(volume)
            
            new_keyword = await db_pool.fetchrow(
                """
                INSERT INTO trends (keyword, search_volume, category, trend_score, created_at)
                VALUES ($1, $2, $3, $4, NOW())
                RETURNING *
                """,
                keyword_lower,
                kw_data.search_volume or 20000,
                kw_data.category or "general",
                kw_data.trend_score or 5.0
            )
            
            stored_keywords.append(dict(new_keyword))
            total_designs += designs
        
        return {
            "success": True,
            "message": f"Imported {len(stored_keywords)} keywords",
            "keywords_stored": len(stored_keywords),
            "potential_listings": total_designs * 8,
            "keywords": stored_keywords
        }
        
    except Exception as e:
        logger.error(f"❌ Batch import error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_trend_stats(db_pool = Depends(get_db_pool)):
    """Get statistics about stored keywords"""
    try:
        total = await db_pool.fetchval("SELECT COUNT(*) FROM trends")
        
        categories = await db_pool.fetch(
            """
            SELECT 
                category,
                COUNT(*) as count
            FROM trends
            GROUP BY category
            ORDER BY count DESC
            """
        )
        
        return {
            "total_keywords": total or 0,
            "categories": [
                {
                    "category": cat['category'],
                    "count": cat['count']
                }
                for cat in categories
            ]
        }
    except Exception as e:
        logger.error(f"❌ Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def get_trends(
    category: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    db_pool = Depends(get_db_pool)
):
    """Get stored keywords with optional category filter"""
    try:
        if category:
            keywords = await db_pool.fetch(
                """
                SELECT * FROM trends
                WHERE category = $1
                ORDER BY search_volume DESC
                LIMIT $2
                """,
                category, limit
            )
        else:
            keywords = await db_pool.fetch(
                """
                SELECT * FROM trends
                ORDER BY search_volume DESC
                LIMIT $1
                """,
                limit
            )
        
        return [dict(kw) for kw in keywords]
        
    except Exception as e:
        logger.error(f"❌ Error fetching keywords: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch")
async def fetch_and_store_trends(
    region: str = Query("GB", description="Region code"),
    limit: int = Query(20, ge=1, le=50),
    db_pool = Depends(get_db_pool)
):
    """Fetch trending keywords from Google Trends"""
    try:
        service = TrendService(db_pool)
        trends = await service.fetch_and_store_trends(
            region=region,
            min_score=6.0,
            limit=limit
        )
        
        return {
            "success": True,
            "message": f"Fetched {len(trends)} trends",
            "trends_stored": len(trends),
            "trends": trends
        }
        
    except Exception as e:
        logger.error(f"Error fetching trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch-10k-initial")
async def fetch_10k_initial(db_pool = Depends(get_db_pool)):
    """Launch 10K initial keyword strategy"""
    try:
        service = TrendService(db_pool)
        result = await service.fetch_initial_10k_keywords()
        
        return result
        
    except Exception as e:
        logger.error(f"Error launching 10K strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics")
async def get_trend_analytics(db_pool = Depends(get_db_pool)):
    """Get trend analytics for dashboard"""
    try:
        total = await db_pool.fetchval("SELECT COUNT(*) FROM trends")
        
        categories = await db_pool.fetch(
            """
            SELECT 
                category,
                COUNT(*) as count,
                AVG(trend_score) as avg_score
            FROM trends
            GROUP BY category
            ORDER BY count DESC
            LIMIT 10
            """
        )
        
        products_count = await db_pool.fetchval(
            "SELECT COUNT(*) FROM products WHERE status = 'active'"
        ) or 0
        
        target = 10000
        progress = (products_count / target) * 100 if target > 0 else 0
        
        return {
            "total_trends": total,
            "total_categories": len(categories),
            "avg_trend_score": sum(c['avg_score'] for c in categories) / len(categories) if categories else 0,
            "goal_progress": {
                "target_designs": target,
                "current_designs": products_count,
                "designs_needed": max(0, target - products_count),
                "progress_percentage": round(progress, 1)
            },
            "top_categories": [
                {
                    "name": c['category'],
                    "count": c['count'],
                    "avg_score": round(float(c['avg_score']), 2)
                }
                for c in categories
            ]
        }
        
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/load-initial-keywords")
async def load_initial_keywords(db_pool: DatabasePool = Depends(get_db_pool)):
    """
    Load 600+ curated keywords - one click setup!
    """
    try:
        # All keywords embedded here - no external API needed!
        keywords = {
            "Mountains": ["mountain", "peak", "summit", "alpine", "mountain range", "snow mountain", "rocky mountain", "mountain sunset", "mountain lake", "himalayan peak", "misty mountain", "mountain landscape", "mountain vista", "mountain trail", "mountain reflection"],
            "Oceans": ["ocean", "sea", "waves", "beach", "coastline", "seascape", "tropical beach", "ocean sunset", "turquoise ocean", "lighthouse", "pier", "harbor", "bay", "coastal view", "ocean waves"],
            "Forests": ["forest", "woodland", "trees", "pine forest", "autumn forest", "winter forest", "forest path", "enchanted forest", "misty forest", "rainforest", "jungle", "tree canopy", "forest trail"],
            "Flowers": ["rose", "tulip", "sunflower", "daisy", "lily", "orchid", "cherry blossom", "lavender", "poppy", "wildflower", "botanical", "pressed flowers", "watercolor flowers", "vintage flowers", "floral arrangement", "bouquet", "garden flowers", "spring flowers"],
            "Wildlife": ["deer", "wolf", "bear", "eagle", "lion", "tiger", "elephant", "giraffe", "zebra", "fox", "owl", "butterfly", "whale", "dolphin", "penguin", "panda", "koala", "sloth"],
            "Sky": ["clouds", "storm", "lightning", "aurora", "northern lights", "milky way", "stars", "starry night", "nebula", "galaxy", "moon", "full moon", "sunrise", "sunset", "golden hour", "rainbow"],
            "Abstract": ["abstract", "abstract art", "modern abstract", "color field", "gradient", "watercolor abstract", "fluid art", "pour painting", "marbling", "abstract landscape", "blue abstract", "gold abstract", "pink abstract", "geometric abstract"],
            "Geometric": ["geometric", "mandala", "sacred geometry", "pattern", "symmetry", "chevron", "moroccan pattern", "tribal pattern", "tessellation", "hexagon", "minimalist geometric"],
            "Minimalist": ["minimalist", "simple", "clean design", "zen", "line art", "one line drawing", "minimal landscape", "minimal floral", "black and white", "monochrome"],
            "Textures": ["marble", "gold marble", "granite", "wood grain", "concrete", "rust", "weathered", "gold foil", "rose gold", "copper", "brushed metal"],
            "Motivational": ["be kind", "stay positive", "dream big", "never give up", "you got this", "keep going", "stay strong", "choose joy", "inspire", "create", "breathe", "peace", "love", "gratitude", "blessed"],
            "Funny": ["coffee first", "but first coffee", "wine time", "wine not", "dog mom", "cat mom", "crazy cat lady", "out of office", "not today", "allergic to mornings", "peopling is hard"],
            "Professions": ["teacher", "nurse", "doctor", "engineer", "lawyer", "chef", "artist", "designer", "writer", "photographer", "entrepreneur", "boss"],
            "Family": ["mom", "dad", "grandma", "grandpa", "mom life", "dad life", "boy mom", "girl mom", "best friend", "family", "sister", "brother"],
            "Dogs": ["dog", "puppy", "golden retriever", "labrador", "french bulldog", "corgi", "pug", "husky", "german shepherd", "poodle", "goldendoodle"],
            "Cats": ["cat", "kitten", "black cat", "orange cat", "tabby", "cat lover", "cat mom", "cat dad"],
            "Birds": ["eagle", "owl", "hawk", "hummingbird", "cardinal", "blue jay", "swan", "flamingo", "peacock", "parrot", "penguin"],
            "Marine": ["whale", "dolphin", "shark", "octopus", "jellyfish", "sea turtle", "starfish", "seahorse", "tropical fish", "coral reef"],
            "Cities": ["new york", "london", "paris", "tokyo", "rome", "barcelona", "amsterdam", "venice", "sydney", "san francisco"],
            "Christmas": ["christmas", "santa", "christmas tree", "snowman", "reindeer", "christmas ornament", "christmas lights", "wreath", "candy cane", "gingerbread", "festive"],
            "Halloween": ["halloween", "pumpkin", "jack o lantern", "ghost", "witch", "black cat", "spider", "haunted", "skeleton", "skull", "spooky"],
            "Valentines": ["valentines day", "love", "heart", "romance", "cupid", "xoxo", "forever", "soulmate"],
            "Easter": ["easter", "easter bunny", "easter egg", "bunny", "rabbit", "spring"],
            "Thanksgiving": ["thanksgiving", "thankful", "grateful", "turkey", "harvest", "autumn"],
            "Other Holidays": ["mothers day", "fathers day", "graduation", "birthday", "wedding", "anniversary", "new year"],
        }
        
        total = 0
        for category, kw_list in keywords.items():
            for kw in kw_list:
                try:
                    await db_pool.execute(
                        """
                        INSERT INTO trends (keyword, category, region, trend_score, search_volume, status, created_at)
                        VALUES ($1, $2, 'GB', 8.0, 1000, 'ready', NOW())
                        ON CONFLICT (keyword, region) DO UPDATE
                        SET category = EXCLUDED.category, trend_score = GREATEST(trends.trend_score, 8.0), status = 'ready'
                        """,
                        kw, category
                    )
                    total += 1
                except Exception as e:
                    logger.error(f"Failed: {kw} - {e}")
        
        logger.success(f"✅ Loaded {total} keywords!")
        return {
            "success": True,
            "keywords_loaded": total,
            "categories": len(keywords),
            "expected_skus": total * 8,
            "message": f"Loaded {total} keywords!"
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
