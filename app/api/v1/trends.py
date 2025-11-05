from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from app.core.trends.service import TrendService
from app.database import DatabasePool
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


# ============================================
# COPY THIS ENTIRE BLOCK INTO YOUR trends.py
# Add at the BOTTOM of the file
# Make sure these imports are at the TOP:
#   from app.database import DatabasePool
#   from app.dependencies import get_db_pool
# ============================================

@router.post("/load-initial-keywords")
async def load_initial_keywords(db_pool: DatabasePool = Depends(get_db_pool)):
    """
    Load 1,250+ curated keywords across 74 categories!
    One-click setup - generates ~10,000 SKUs
    """
    try:
        logger.info("🚀 Loading MEGA keyword database...")
        
        # 1,250+ KEYWORDS ACROSS 74 CATEGORIES!
        mega_keywords = {
            "Mountains & Peaks": ["mountain", "peak", "summit", "alpine", "mountain range", "snow capped", "rocky mountain", "mountain sunset", "mountain sunrise", "mountain lake", "mountain forest", "mountain valley", "mountain meadow", "himalayan", "mountain trail", "mountain reflection", "misty mountain", "dramatic mountain", "mountain silhouette", "mountain vista", "mountain wilderness", "mountain ridge", "mountain pass", "mountain glacier", "mountain stream", "mountain waterfall", "mountain panorama", "mountain scenery"],
            "Oceans & Seas": ["ocean", "sea", "waves", "beach", "coastline", "seascape", "ocean waves", "tropical beach", "sandy beach", "ocean sunset", "sea foam", "tidal wave", "beach scene", "coastal view", "ocean horizon", "beach paradise", "turquoise ocean", "azure sea", "stormy sea", "calm ocean", "ocean breeze", "lighthouse", "pier", "dock", "harbor", "marina", "bay", "cove", "cliff coast", "rocky shore", "beach sunrise", "ocean life", "seaside", "coastal landscape"],
            "Forests & Trees": ["forest", "woodland", "trees", "pine forest", "redwood", "oak tree", "birch", "bamboo", "jungle", "rainforest", "tropical forest", "autumn forest", "winter forest", "spring forest", "summer forest", "forest path", "forest trail", "tree canopy", "forest clearing", "enchanted forest", "misty forest", "dark forest", "sunlit forest", "forest stream", "ancient forest", "evergreen", "deciduous", "tree silhouette"],
            "Flowers & Plants": ["rose", "tulip", "sunflower", "daisy", "lily", "orchid", "peony", "lotus", "cherry blossom", "lavender", "poppy", "iris", "hydrangea", "magnolia", "dahlia", "marigold", "carnation", "chrysanthemum", "daffodil", "violet", "wildflower", "botanical", "pressed flowers", "watercolor flowers", "vintage flowers", "spring flowers", "summer flowers", "tropical flowers", "dried flowers", "flower garden", "flower field", "flower bouquet", "floral arrangement", "flower wreath", "cactus", "succulent", "fern", "palm leaf"],
            "Wildlife Mammals": ["deer", "wolf", "bear", "grizzly", "polar bear", "eagle", "lion", "tiger", "elephant", "giraffe", "zebra", "fox", "red fox", "arctic fox", "owl", "hawk", "falcon", "butterfly", "whale", "dolphin", "penguin", "panda", "koala", "kangaroo", "sloth", "raccoon", "squirrel", "moose", "elk", "bison", "buffalo", "cheetah", "leopard", "jaguar", "lynx", "otter", "seal", "walrus"],
            "Birds": ["eagle", "bald eagle", "hawk", "owl", "barn owl", "snowy owl", "falcon", "hummingbird", "cardinal", "blue jay", "robin", "sparrow", "swan", "flamingo", "peacock", "toucan", "parrot", "macaw", "penguin", "pelican", "heron", "crane", "stork", "woodpecker", "kingfisher", "crow", "raven", "dove", "pigeon"],
            "Marine Life": ["whale", "humpback whale", "blue whale", "orca", "dolphin", "shark", "great white", "octopus", "jellyfish", "sea turtle", "starfish", "seahorse", "clownfish", "tropical fish", "coral reef", "seal", "sea lion", "crab", "lobster", "shrimp", "manta ray", "angelfish", "sailfish", "marlin"],
            "Sky & Weather": ["clouds", "storm", "lightning", "thunder", "aurora", "northern lights", "milky way", "stars", "starry night", "constellation", "nebula", "galaxy", "moon", "full moon", "crescent moon", "sun", "sunrise", "sunset", "golden hour", "blue hour", "rainbow", "dramatic sky", "cloudy", "foggy", "misty", "stormy sky", "clear sky"],
            "Seasons": ["spring", "summer", "autumn", "fall", "winter", "springtime", "summertime", "fall foliage", "autumn leaves", "winter wonderland", "spring blossom", "summer sunset", "fall colors", "winter snow", "seasonal", "spring flowers", "summer vibes", "autumn harvest"],
            "Landscapes": ["landscape", "scenery", "vista", "panorama", "countryside", "rural", "pastoral", "meadow", "field", "prairie", "valley", "canyon", "desert", "dunes", "oasis", "savanna", "tundra", "glacier", "iceberg", "volcano", "hill", "cliff", "cave", "waterfall", "river", "lake", "pond", "wetland"],
            "Abstract Art": ["abstract", "abstract art", "modern abstract", "contemporary", "color field", "gradient", "ombre", "color splash", "paint stroke", "brush stroke", "ink splash", "watercolor abstract", "acrylic abstract", "fluid art", "pour painting", "marbling", "abstract expressionism", "abstract landscape", "abstract floral", "blue abstract", "gold abstract", "pink abstract", "teal abstract", "minimalist abstract", "bold abstract", "colorful abstract", "monochrome abstract"],
            "Geometric": ["geometric", "geometric pattern", "triangle", "hexagon", "circle", "square", "polygon", "tessellation", "mandala", "sacred geometry", "fractal", "kaleidoscope", "symmetry", "chevron", "herringbone", "quatrefoil", "moroccan", "arabesque", "tribal", "aztec", "nordic", "scandinavian", "art deco", "mid century", "modern geometric", "3d geometric", "isometric"],
            "Minimalist": ["minimalist", "minimal", "simple", "clean", "modern", "zen", "line art", "one line", "continuous line", "simple shape", "minimal landscape", "minimal floral", "minimal abstract", "monochrome", "negative space", "whitespace", "simple design", "minimal geometric", "minimal typography"],
            "Textures": ["marble", "gold marble", "granite", "stone", "wood grain", "concrete", "rust", "weathered", "distressed", "vintage texture", "metal", "copper", "brass", "gold foil", "rose gold", "silver", "brushed metal", "aged", "patina", "fabric", "linen", "canvas", "paper texture"],
            "Color Themes": ["blue", "navy", "teal", "turquoise", "green", "sage", "emerald", "pink", "blush", "coral", "red", "burgundy", "orange", "peach", "yellow", "gold", "purple", "lavender", "brown", "beige", "neutral", "black white", "grayscale", "pastel", "bold colors", "earth tones", "jewel tones"],
            "Motivational": ["be kind", "stay positive", "dream big", "never give up", "believe", "you got this", "keep going", "stay strong", "be brave", "choose joy", "make it happen", "live your best life", "follow your dreams", "inspire", "create", "hustle", "grind", "focus", "breathe", "relax", "peace", "love", "hope", "faith", "courage", "strength", "wisdom", "gratitude", "blessed", "thankful", "mindful", "present", "shine bright", "be yourself", "chase dreams", "good vibes", "positive energy"],
            "Funny & Sarcastic": ["coffee first", "but first coffee", "powered by coffee", "coffee lover", "wine time", "wine not", "wine lover", "save water drink wine", "sarcasm loading", "does not compute", "error 404", "out of office", "not today", "nope", "meh", "whatever", "yay monday", "allergic to mornings", "i need my space", "introverted", "peopling is hard", "nope not today", "currently unavailable"],
            "Pet Lovers": ["dog mom", "dog dad", "cat mom", "cat dad", "crazy cat lady", "dog lover", "cat lover", "fur mama", "pet parent", "rescue mom", "adopt dont shop", "dog hair dont care", "cat hair dont care", "paw print", "dog life", "cat life"],
            "Medical": ["nurse", "nurse life", "nursing", "rn", "doctor", "physician", "surgeon", "dentist", "dental hygienist", "veterinarian", "vet tech", "pharmacist", "paramedic", "emt", "therapist", "healthcare worker", "medical professional", "hospital life"],
            "Education": ["teacher", "best teacher", "teacher life", "teach love inspire", "professor", "principal", "librarian", "tutor", "educator", "school counselor", "teaching assistant"],
            "Tech": ["engineer", "software engineer", "web developer", "programmer", "coder", "tech", "it professional", "data scientist", "developer", "software developer"],
            "Business": ["entrepreneur", "boss", "ceo", "manager", "business owner", "hustle", "small business", "girl boss", "boss lady"],
            "Creative": ["artist", "painter", "designer", "graphic designer", "photographer", "writer", "author", "illustrator", "creative", "maker"],
            "Service": ["chef", "cook", "baker", "barista", "server", "bartender", "hairdresser", "stylist", "makeup artist", "nail tech"],
            "Other Jobs": ["lawyer", "attorney", "accountant", "realtor", "real estate", "mechanic", "plumber", "electrician", "contractor", "architect"],
            "Parents": ["mom", "mama", "mother", "mommy", "mom life", "boy mom", "girl mom", "twin mom", "mama bear", "dad", "father", "daddy", "papa", "dad life", "girl dad", "boy dad"],
            "Grandparents": ["grandma", "grandmother", "nana", "granny", "mimi", "gigi", "grandpa", "grandfather", "papa", "pops", "grandparent"],
            "Family": ["aunt", "auntie", "funcle", "uncle", "sister", "brother", "family", "tribe", "blessed family"],
            "Relationships": ["wife", "husband", "spouse", "partner", "soulmate", "best friend", "bff", "friendship", "squad", "bride", "groom", "engaged", "mrs", "mr"],
            "Popular Dogs": ["dog", "puppy", "golden retriever", "labrador", "lab", "french bulldog", "frenchie", "corgi", "pug", "beagle", "husky", "siberian husky", "german shepherd", "shepherd", "poodle", "doodle", "goldendoodle", "labradoodle", "shih tzu", "yorkie"],
            "Working Dogs": ["rottweiler", "doberman", "boxer", "great dane", "mastiff", "st bernard", "bernese mountain dog", "australian shepherd", "aussie", "border collie", "cattle dog"],
            "Small Dogs": ["chihuahua", "dachshund", "wiener dog", "maltese", "pomeranian", "papillon", "toy poodle", "mini poodle"],
            "Cats": ["cat", "kitten", "tabby", "orange cat", "ginger cat", "black cat", "white cat", "persian", "siamese", "maine coon", "ragdoll", "british shorthair", "bengal", "sphynx", "calico", "tortoiseshell", "tuxedo cat"],
            "Farm Animals": ["horse", "pony", "cow", "pig", "sheep", "lamb", "goat", "chicken", "rooster", "duck", "goose", "turkey", "donkey", "llama", "alpaca"],
            "Exotic Pets": ["rabbit", "bunny", "hamster", "guinea pig", "ferret", "hedgehog", "chinchilla", "sugar glider", "parrot", "bird", "fish", "turtle", "lizard", "snake", "iguana"],
            "US Cities": ["new york", "nyc", "manhattan", "brooklyn", "los angeles", "chicago", "houston", "phoenix", "philadelphia", "san antonio", "san diego", "dallas", "san francisco", "austin", "seattle", "boston", "miami", "atlanta", "denver", "portland", "las vegas"],
            "World Cities": ["london", "paris", "tokyo", "rome", "barcelona", "amsterdam", "venice", "prague", "budapest", "vienna", "berlin", "dubai", "sydney", "melbourne", "toronto", "vancouver", "hong kong", "singapore", "bangkok", "istanbul"],
            "Landmarks": ["eiffel tower", "big ben", "tower bridge", "colosseum", "taj mahal", "great wall", "statue of liberty", "golden gate bridge", "sydney opera house", "burj khalifa", "empire state"],
            "Travel": ["travel", "wanderlust", "adventure", "explore", "journey", "vacation", "passport", "world map", "compass", "airplane", "luggage", "suitcase", "road trip", "camping", "hiking"],
            "Architecture": ["modern architecture", "gothic", "victorian", "art deco", "brutalist", "minimalist architecture", "japanese architecture", "mediterranean", "colonial", "craftsman", "cottage", "mid century"],
            "Christmas": ["christmas", "merry christmas", "xmas", "christmas tree", "santa", "santa claus", "reindeer", "rudolph", "snowman", "frosty", "ornament", "christmas lights", "wreath", "holly", "mistletoe", "candy cane", "gingerbread", "stocking", "presents", "festive", "winter wonderland", "sleigh", "elf", "north pole", "jingle bells"],
            "Halloween": ["halloween", "happy halloween", "spooky", "pumpkin", "jack o lantern", "ghost", "boo", "witch", "black cat", "spider", "spider web", "haunted", "creepy", "skeleton", "skull", "bones", "candy corn", "trick or treat", "october", "zombie", "vampire", "mummy", "monster", "bat"],
            "Valentines": ["valentines day", "valentine", "love", "heart", "hearts", "red heart", "pink heart", "cupid", "romance", "romantic", "kiss", "xoxo", "love you", "i love you", "forever", "always", "soulmate", "be mine", "sweetheart"],
            "Easter": ["easter", "happy easter", "easter egg", "easter bunny", "bunny", "rabbit", "easter basket", "spring", "pastel", "egg hunt", "chick", "easter sunday"],
            "Thanksgiving": ["thanksgiving", "happy thanksgiving", "thankful", "grateful", "gratitude", "turkey", "pumpkin pie", "autumn", "fall", "harvest", "november", "feast"],
            "Mothers Day": ["mothers day", "happy mothers day", "mom", "mama", "best mom", "mom life", "super mom", "mom squad", "motherhood", "mom to be"],
            "Fathers Day": ["fathers day", "happy fathers day", "dad", "father", "best dad", "dad life", "super dad", "fatherhood", "dad to be"],
            "Other Holidays": ["graduation", "graduate", "class of 2024", "class of 2025", "birthday", "happy birthday", "birthday girl", "birthday boy", "wedding", "just married", "mr and mrs", "bride", "groom", "anniversary", "new year", "happy new year", "2025", "fourth of july", "independence day", "july 4th", "patriotic", "usa", "america", "st patricks day", "irish", "lucky", "shamrock", "cinco de mayo"],
            "Fitness": ["fitness", "gym", "workout", "exercise", "lift", "weights", "dumbbell", "barbell", "crossfit", "strong", "muscle", "gains", "fit life", "train", "cardio", "running", "marathon", "5k", "runner"],
            "Yoga": ["yoga", "namaste", "yogi", "meditation", "zen", "om", "chakra", "mindfulness", "yoga life", "downward dog", "warrior pose"],
            "Team Sports": ["football", "soccer", "basketball", "baseball", "hockey", "volleyball", "softball", "lacrosse", "rugby"],
            "Individual Sports": ["tennis", "golf", "swimming", "cycling", "running", "skiing", "snowboarding", "surfing", "skateboarding", "climbing", "boxing", "martial arts"],
            "Outdoor": ["hiking", "camping", "fishing", "hunting", "kayaking", "canoeing", "backpacking", "trail", "outdoor", "nature lover", "mountain life", "adventure"],
            "Gaming": ["gamer", "gaming", "video games", "game on", "level up", "player", "controller", "console", "pc gaming", "esports"],
            "Music": ["music", "musician", "guitar", "piano", "drums", "singing", "band", "concert", "rock", "jazz", "classical", "country", "hip hop", "pop music"],
            "Reading": ["book lover", "bookworm", "reading", "library", "books", "reader", "bibliophile", "book club"],
            "Coffee": ["coffee", "espresso", "latte", "cappuccino", "americano", "cold brew", "iced coffee", "coffee shop", "cafe", "barista", "coffee time", "coffee addict", "coffee break"],
            "Tea": ["tea", "tea time", "tea lover", "green tea", "black tea", "chai", "matcha", "herbal tea", "afternoon tea", "tea party"],
            "Wine": ["wine", "red wine", "white wine", "rose", "wine lover", "wine time", "vineyard", "winery", "wine tasting", "sommelier", "wine glass"],
            "Beer": ["beer", "craft beer", "ipa", "ale", "lager", "brewery", "beer lover", "hops", "beer time"],
            "Cocktails": ["cocktail", "martini", "margarita", "mojito", "cosmopolitan", "old fashioned", "manhattan", "whiskey", "bourbon", "gin", "vodka"],
            "Food": ["pizza", "burger", "sushi", "tacos", "pasta", "bread", "cake", "cupcake", "donut", "ice cream", "chocolate", "cheese", "bacon", "avocado", "food lover", "foodie"],
            "Spiritual": ["spiritual", "spirituality", "mindfulness", "meditation", "zen", "peace", "harmony", "balance", "enlightenment", "awakening", "consciousness"],
            "Mystical": ["mystical", "magic", "magical", "witch", "witchcraft", "wicca", "pagan", "spell", "crystal", "healing", "energy", "aura", "chakra"],
            "Zodiac": ["zodiac", "astrology", "horoscope", "aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces", "star sign"],
            "Symbols": ["mandala", "om", "lotus", "hamsa", "evil eye", "dreamcatcher", "feather", "moon", "sun", "star", "tree of life", "yin yang", "infinity"],
            "Vintage Eras": ["vintage", "retro", "antique", "classic", "nostalgic", "1920s", "1930s", "1940s", "1950s", "1960s", "1970s", "1980s", "1990s", "art nouveau", "art deco", "mid century", "victorian", "baroque"],
            "Vintage Items": ["vintage car", "classic car", "vintage camera", "typewriter", "record player", "vinyl", "cassette", "retro radio", "rotary phone", "vintage map", "compass", "antique clock"],
            "Space": ["space", "galaxy", "nebula", "planet", "solar system", "astronaut", "rocket", "moon landing", "mars", "jupiter", "saturn", "stars", "constellation", "comet", "asteroid", "black hole", "supernova"],
            "Science": ["science", "chemistry", "physics", "biology", "astronomy", "molecule", "atom", "dna", "laboratory", "microscope", "telescope", "experiment"],
            "Baby Animals": ["baby elephant", "baby giraffe", "baby lion", "baby bear", "baby fox", "baby deer", "baby bunny", "baby penguin", "baby seal", "baby panda"],
            "Kids Characters": ["dinosaur", "t rex", "unicorn", "rainbow", "superhero", "princess", "pirate", "mermaid", "fairy", "dragon", "robot", "alien"],
            "Kids Themes": ["abc", "alphabet", "numbers", "123", "shapes", "colors", "nursery", "playroom", "toys", "balloons", "stars", "moon"],
            "Vehicles": ["car", "truck", "train", "airplane", "helicopter", "boat", "ship", "rocket", "fire truck", "police car", "ambulance", "tractor", "excavator"],
        }
        
        total = 0
        for cat, kws in mega_keywords.items():
            for kw in kws:
                try:
                    await db_pool.execute(
                        """
                        INSERT INTO trends (keyword, category, trend_score, search_volume, status, created_at)
                        VALUES ($1, $2, $3, $4, $5, NOW())
                        """,
                        kw, cat, 8.0, 1000, 'ready'
                    )
                    total += 1
                except Exception as e:
                    # Skip duplicates or other errors
                    pass
        
        logger.info(f"✅ Loaded {total} keywords across {len(mega_keywords)} categories!")
        return {
            "success": True,
            "keywords_loaded": total,
            "categories": len(mega_keywords),
            "expected_skus": total * 8,
            "message": f"Loaded {total} keywords! Ready to generate {total * 8} SKUs!"
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
