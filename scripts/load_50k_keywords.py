# 50K SKU Strategy - Comprehensive Keyword & Category Expansion
# Target: 50,000 unique SKUs across all art product categories

"""
MATH:
- 50,000 SKUs ÷ 8 styles per keyword = 6,250 keywords needed
- Organized into ~100 categories (62-63 keywords per category)
- OR ~50 mega-categories (125 keywords each)

STRATEGY:
1. Broad categories with depth (100+ keywords each)
2. Niche categories with specificity (20-50 keywords each)
3. Trending/seasonal keywords (rotating)
4. Long-tail combinations (auto-generated)
"""

MEGA_CATEGORY_STRUCTURE = {
    # ========== NATURE & LANDSCAPES (750 keywords) ==========
    "Nature - Mountains": {
        "base_keywords": [
            "mountain", "peak", "summit", "alpine", "himalayan", "rocky mountains",
            "mountain range", "mountain peak", "snow peak", "mountain vista",
            "mountain landscape", "mountain sunrise", "mountain sunset", "mountain lake",
            "mountain forest", "mountain meadow", "mountain valley", "mountain trail"
        ],
        "modifiers": ["sunset", "sunrise", "winter", "summer", "autumn", "spring", 
                     "dramatic", "majestic", "misty", "foggy", "snowy", "rugged"],
        "styles": ["watercolor", "oil painting", "photography", "minimalist", "abstract"],
        "estimated_combinations": 100
    },
    
    "Nature - Oceans & Seas": {
        "base_keywords": [
            "ocean", "sea", "waves", "beach", "coastline", "seascape", "ocean waves",
            "tropical beach", "sandy beach", "ocean sunset", "sea foam", "tidal wave",
            "coral reef", "underwater", "deep sea", "ocean floor", "marine life",
            "lighthouse", "pier", "dock", "harbor", "bay", "cove", "cliff coast"
        ],
        "modifiers": ["turquoise", "azure", "stormy", "calm", "tropical", "arctic"],
        "estimated_combinations": 120
    },
    
    "Nature - Forests & Trees": {
        "base_keywords": [
            "forest", "woodland", "trees", "pine forest", "redwood", "oak tree",
            "birch forest", "bamboo grove", "jungle", "rainforest", "autumn forest",
            "winter forest", "forest path", "tree canopy", "grove", "copse"
        ],
        "estimated_combinations": 80
    },
    
    "Nature - Flowers & Botanicals": {
        "base_keywords": [
            "rose", "tulip", "sunflower", "daisy", "lily", "orchid", "peony", "lotus",
            "cherry blossom", "lavender", "poppy", "iris", "hydrangea", "magnolia",
            "dahlia", "marigold", "carnation", "chrysanthemum", "daffodil", "violet",
            "wildflower", "garden flowers", "floral arrangement", "bouquet", "wreath"
        ],
        "modifiers": ["watercolor", "vintage", "botanical illustration", "pressed"],
        "estimated_combinations": 150
    },
    
    "Nature - Wildlife": {
        "base_keywords": [
            "deer", "wolf", "bear", "eagle", "lion", "tiger", "elephant", "giraffe",
            "zebra", "fox", "owl", "hawk", "butterfly", "hummingbird", "whale",
            "dolphin", "penguin", "polar bear", "panda", "koala", "kangaroo"
        ],
        "estimated_combinations": 100
    },
    
    "Nature - Sky & Weather": {
        "base_keywords": [
            "clouds", "storm", "lightning", "aurora", "northern lights", "milky way",
            "stars", "constellation", "nebula", "galaxy", "moon", "sun", "rainbow",
            "sunset sky", "sunrise sky", "dramatic sky", "cloudy sky"
        ],
        "estimated_combinations": 80
    },
    
    "Nature - Seasons": {
        "base_keywords": [
            "autumn leaves", "fall foliage", "spring flowers", "summer meadow",
            "winter snow", "spring blossom", "harvest", "seasonal", "equinox"
        ],
        "estimated_combinations": 50
    },

    # ========== ABSTRACT & GEOMETRIC (600 keywords) ==========
    "Abstract - Color Fields": {
        "base_keywords": [
            "abstract", "color field", "gradient", "ombre", "color splash",
            "paint stroke", "brush stroke", "ink splash", "watercolor abstract",
            "fluid art", "pour painting", "acrylic pour", "resin art"
        ],
        "color_combinations": ["blue gold", "pink purple", "teal coral", "sage blush"],
        "estimated_combinations": 100
    },
    
    "Geometric - Patterns": {
        "base_keywords": [
            "geometric", "triangle", "hexagon", "circle", "square", "polygon",
            "tessellation", "mandala", "sacred geometry", "fractal", "kaleidoscope",
            "chevron", "herringbone", "quatrefoil", "moroccan pattern", "tribal"
        ],
        "estimated_combinations": 120
    },
    
    "Abstract - Minimalist": {
        "base_keywords": [
            "minimalist", "simple", "clean", "modern", "scandinavian", "zen",
            "line art", "one line", "continuous line", "simple shape", "minimal"
        ],
        "estimated_combinations": 80
    },
    
    "Abstract - Textures": {
        "base_keywords": [
            "marble", "granite", "stone", "wood grain", "concrete", "rust",
            "metal", "copper", "gold foil", "rose gold", "brushed metal",
            "aged", "distressed", "weathered", "vintage texture"
        ],
        "estimated_combinations": 100
    },

    # ========== TYPOGRAPHY & QUOTES (800 keywords) ==========
    "Typography - Motivational": {
        "base_keywords": [
            "be kind", "stay positive", "dream big", "never give up", "believe",
            "inspire", "create", "hustle", "grind", "focus", "breathe", "namaste",
            "live laugh love", "good vibes", "positive energy", "blessed"
        ],
        "estimated_combinations": 150
    },
    
    "Typography - Funny": {
        "base_keywords": [
            "sarcastic quote", "funny saying", "witty", "humorous", "coffee lover",
            "wine lover", "cat lover", "dog lover", "introvert", "extrovert"
        ],
        "estimated_combinations": 100
    },
    
    "Typography - Profession": {
        "base_keywords": [
            "teacher", "nurse", "doctor", "engineer", "lawyer", "accountant",
            "realtor", "chef", "artist", "writer", "photographer", "designer",
            "developer", "entrepreneur", "mom", "dad", "grandma", "grandpa"
        ],
        "estimated_combinations": 150
    },
    
    "Typography - Sports & Hobbies": {
        "base_keywords": [
            "yoga", "fitness", "running", "cycling", "swimming", "hiking",
            "camping", "fishing", "hunting", "golf", "tennis", "basketball",
            "football", "soccer", "baseball", "gaming", "reading", "music"
        ],
        "estimated_combinations": 150
    },

    # ========== ANIMALS (500 keywords) ==========
    "Animals - Pets": {
        "base_keywords": [
            "dog", "cat", "puppy", "kitten", "golden retriever", "labrador",
            "french bulldog", "corgi", "pug", "beagle", "husky", "german shepherd",
            "persian cat", "siamese cat", "maine coon", "tabby cat", "rabbit",
            "hamster", "guinea pig", "bird", "parrot", "fish", "aquarium"
        ],
        "estimated_combinations": 150
    },
    
    "Animals - Wild": {
        "base_keywords": [
            "lion", "tiger", "bear", "wolf", "fox", "deer", "moose", "elk",
            "bison", "buffalo", "elephant", "giraffe", "zebra", "rhino",
            "hippo", "monkey", "gorilla", "chimpanzee", "orangutan"
        ],
        "estimated_combinations": 100
    },
    
    "Animals - Birds": {
        "base_keywords": [
            "eagle", "hawk", "owl", "falcon", "hummingbird", "cardinal",
            "blue jay", "robin", "sparrow", "swan", "flamingo", "peacock",
            "toucan", "parrot", "penguin", "pelican", "heron", "crane"
        ],
        "estimated_combinations": 100
    },
    
    "Animals - Marine": {
        "base_keywords": [
            "whale", "dolphin", "shark", "octopus", "jellyfish", "sea turtle",
            "starfish", "seahorse", "clownfish", "tropical fish", "coral"
        ],
        "estimated_combinations": 80
    },

    # ========== URBAN & ARCHITECTURE (400 keywords) ==========
    "Urban - Cities": {
        "base_keywords": [
            "new york", "london", "paris", "tokyo", "rome", "barcelona",
            "amsterdam", "venice", "prague", "budapest", "vienna", "berlin",
            "skyline", "cityscape", "urban", "metropolitan", "downtown"
        ],
        "estimated_combinations": 120
    },
    
    "Architecture - Landmarks": {
        "base_keywords": [
            "eiffel tower", "statue of liberty", "big ben", "colosseum",
            "taj mahal", "great wall", "sydney opera house", "burj khalifa",
            "golden gate bridge", "brooklyn bridge", "tower bridge"
        ],
        "estimated_combinations": 80
    },
    
    "Architecture - Styles": {
        "base_keywords": [
            "modern architecture", "gothic", "victorian", "art deco",
            "brutalist", "minimalist architecture", "japanese architecture",
            "mediterranean", "colonial", "craftsman", "cottage"
        ],
        "estimated_combinations": 100
    },

    # ========== VINTAGE & RETRO (350 keywords) ==========
    "Vintage - Era Specific": {
        "base_keywords": [
            "vintage", "retro", "1920s", "1930s", "1940s", "1950s", "1960s",
            "1970s", "1980s", "1990s", "art nouveau", "art deco", "mid century",
            "victorian", "edwardian", "baroque", "rococo", "renaissance"
        ],
        "estimated_combinations": 120
    },
    
    "Vintage - Objects": {
        "base_keywords": [
            "vintage car", "classic car", "vintage camera", "typewriter",
            "record player", "vintage radio", "rotary phone", "vintage bike",
            "vintage map", "compass", "antique", "nostalgic"
        ],
        "estimated_combinations": 100
    },

    # ========== HOLIDAYS & CELEBRATIONS (500 keywords) ==========
    "Holidays - Christmas": {
        "base_keywords": [
            "christmas", "santa", "reindeer", "snowman", "christmas tree",
            "ornament", "wreath", "candy cane", "gingerbread", "holly",
            "mistletoe", "winter wonderland", "festive", "merry christmas"
        ],
        "estimated_combinations": 120
    },
    
    "Holidays - Halloween": {
        "base_keywords": [
            "halloween", "pumpkin", "jack o lantern", "ghost", "witch",
            "black cat", "spider", "web", "haunted", "spooky", "skeleton",
            "candy corn", "trick or treat", "autumn halloween"
        ],
        "estimated_combinations": 100
    },
    
    "Holidays - Other": {
        "base_keywords": [
            "easter", "thanksgiving", "valentines day", "mothers day",
            "fathers day", "graduation", "birthday", "wedding", "anniversary",
            "new year", "fourth of july", "st patricks day", "cinco de mayo"
        ],
        "estimated_combinations": 120
    },

    # ========== FOOD & DRINK (300 keywords) ==========
    "Food - Categories": {
        "base_keywords": [
            "coffee", "tea", "wine", "beer", "cocktail", "pizza", "burger",
            "sushi", "pasta", "bread", "cake", "cupcake", "donut", "ice cream",
            "fruit", "vegetable", "herbs", "spices", "kitchen", "cooking"
        ],
        "estimated_combinations": 150
    },

    # ========== SPIRITUALITY & MYSTICAL (300 keywords) ==========
    "Spiritual - Symbols": {
        "base_keywords": [
            "mandala", "chakra", "om", "lotus", "zen", "buddha", "meditation",
            "yoga", "namaste", "peace", "yin yang", "hamsa", "evil eye",
            "dream catcher", "feather", "crystal", "moon phases", "tarot",
            "astrology", "zodiac", "celestial", "mystical", "spiritual"
        ],
        "estimated_combinations": 150
    },

    # ========== SCIENCE & SPACE (300 keywords) ==========
    "Space - Astronomy": {
        "base_keywords": [
            "galaxy", "nebula", "planet", "solar system", "constellation",
            "astronaut", "rocket", "space shuttle", "moon landing", "mars",
            "jupiter", "saturn", "venus", "mercury", "uranus", "neptune",
            "black hole", "supernova", "meteor", "comet", "asteroid"
        ],
        "estimated_combinations": 150
    },

    # ========== SPORTS & ACTIVITIES (350 keywords) ==========
    "Sports - Categories": {
        "base_keywords": [
            "football", "soccer", "basketball", "baseball", "tennis", "golf",
            "hockey", "volleyball", "swimming", "running", "cycling", "hiking",
            "skiing", "snowboarding", "surfing", "skateboarding", "climbing",
            "boxing", "martial arts", "yoga", "fitness", "gym", "crossfit"
        ],
        "estimated_combinations": 150
    },

    # ========== PROFESSIONS & CAREERS (400 keywords) ==========
    "Professions - Medical": {
        "base_keywords": [
            "doctor", "nurse", "surgeon", "dentist", "veterinarian",
            "pharmacist", "paramedic", "therapist", "medical", "healthcare"
        ],
        "estimated_combinations": 80
    },
    
    "Professions - Education": {
        "base_keywords": [
            "teacher", "professor", "principal", "librarian", "tutor",
            "coach", "counselor", "education", "school", "classroom"
        ],
        "estimated_combinations": 80
    },

    # ========== KIDS & NURSERY (400 keywords) ==========
    "Kids - Animals": {
        "base_keywords": [
            "cute animal", "baby animal", "cartoon animal", "woodland animal",
            "safari animal", "farm animal", "zoo animal", "nursery animal"
        ],
        "estimated_combinations": 100
    },
    
    "Kids - Themes": {
        "base_keywords": [
            "dinosaur", "unicorn", "rainbow", "superhero", "princess",
            "pirate", "space", "ocean", "jungle", "farm", "construction",
            "vehicles", "alphabet", "numbers", "shapes", "colors"
        ],
        "estimated_combinations": 120
    },
}

# ========== KEYWORD GENERATION STRATEGIES ==========

GENERATION_STRATEGIES = {
    "Long-Tail Combinations": {
        "description": "Combine base keywords with modifiers for unique variations",
        "examples": [
            "minimalist mountain sunset watercolor",
            "abstract blue gold geometric",
            "vintage 1970s retro typography"
        ],
        "estimated_output": "10,000+ unique combinations"
    },
    
    "Color Variations": {
        "colors": [
            "red", "blue", "green", "yellow", "orange", "purple", "pink",
            "black", "white", "gray", "brown", "teal", "coral", "navy",
            "sage", "blush", "gold", "silver", "rose gold", "copper",
            "turquoise", "lavender", "mint", "peach", "burgundy", "emerald"
        ],
        "patterns": [
            "[keyword] in [color]",
            "[color] [keyword]",
            "[keyword] [color] theme"
        ]
    },
    
    "Style Modifiers": {
        "styles": [
            "watercolor", "oil painting", "sketch", "pencil drawing",
            "digital art", "vector", "line art", "minimalist", "abstract",
            "realistic", "photorealistic", "vintage", "retro", "modern",
            "contemporary", "traditional", "folk art", "street art"
        ]
    },
    
    "Seasonal Variations": {
        "seasons": ["spring", "summer", "autumn", "fall", "winter"],
        "times": ["sunrise", "sunset", "dawn", "dusk", "noon", "night"],
        "weather": ["sunny", "cloudy", "rainy", "stormy", "misty", "foggy"]
    }
}

# ========== IMPLEMENTATION PHASES ==========

IMPLEMENTATION_PLAN = {
    "Phase 1 - Foundation (0-10K SKUs)": {
        "focus": "Top 20 categories, 100 keywords each",
        "categories": 20,
        "keywords_per_category": 100,
        "expected_skus": 16000,
        "timeline": "Week 1-2"
    },
    
    "Phase 2 - Expansion (10K-25K SKUs)": {
        "focus": "Add 30 more categories, expand existing",
        "new_categories": 30,
        "expand_existing": "50 keywords each",
        "expected_skus": 15000,
        "timeline": "Week 3-4"
    },
    
    "Phase 3 - Long-Tail (25K-40K SKUs)": {
        "focus": "Automated combinations, niche categories",
        "strategy": "Combine keywords with modifiers",
        "expected_skus": 15000,
        "timeline": "Week 5-6"
    },
    
    "Phase 4 - Saturation (40K-50K SKUs)": {
        "focus": "Fill gaps, trending keywords, seasonal",
        "strategy": "API trending + manual curation",
        "expected_skus": 10000,
        "timeline": "Week 7-8"
    }
}

# ========== TOTAL BREAKDOWN ==========
"""
CATEGORY DISTRIBUTION (100 categories total):
- Nature & Landscapes: 20 categories × 40 keywords = 800 keywords
- Abstract & Geometric: 15 categories × 40 keywords = 600 keywords
- Typography & Quotes: 20 categories × 40 keywords = 800 keywords
- Animals: 10 categories × 50 keywords = 500 keywords
- Urban & Architecture: 10 categories × 40 keywords = 400 keywords
- Vintage & Retro: 8 categories × 45 keywords = 360 keywords
- Holidays: 12 categories × 42 keywords = 500 keywords
- Food & Drink: 8 categories × 40 keywords = 320 keywords
- Spiritual & Mystical: 8 categories × 40 keywords = 320 keywords
- Science & Space: 8 categories × 40 keywords = 320 keywords
- Sports: 10 categories × 35 keywords = 350 keywords
- Professions: 15 categories × 27 keywords = 400 keywords
- Kids & Nursery: 10 categories × 40 keywords = 400 keywords

TOTAL: ~6,070 base keywords × 8 styles = 48,560 SKUs
+ Long-tail combinations and variations = 50,000+ SKUs
"""

print("50K SKU Strategy loaded!")
print(f"Estimated base keywords: 6,000+")
print(f"With 8 styles each: 48,000+ SKUs")
print(f"With combinations: 50,000+ SKUs")
