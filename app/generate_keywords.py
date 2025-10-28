#!/usr/bin/env python3
"""
Generate 1000+ proven POD keywords for trending products
Run this locally, then use import_keywords.py to push to your database
"""

import json
from pathlib import Path

# High-volume POD niches with proven search demand
POD_KEYWORDS = {
    "Animals & Pets": [
        "cat lover", "dog mom", "golden retriever", "french bulldog", "corgi",
        "husky", "pug life", "dachshund", "beagle", "german shepherd",
        "labrador", "pitbull", "chihuahua", "pomeranian", "rottweiler",
        "bulldog", "shih tzu", "yorkshire terrier", "boston terrier",
        "cat dad", "crazy cat lady", "meow", "purr", "kitty",
        "horse lover", "horse girl", "equestrian", "horse riding",
        "wildlife", "bear", "wolf", "lion", "tiger", "elephant",
        "giraffe", "panda", "koala", "sloth", "otter", "fox",
        "raccoon", "hedgehog", "bunny", "rabbit", "hamster"
    ],
    
    "Occupations & Professions": [
        "nurse", "teacher", "firefighter", "police officer", "paramedic",
        "doctor", "veterinarian", "dentist", "pharmacist", "therapist",
        "social worker", "counselor", "psychologist", "psychiatrist",
        "engineer", "software engineer", "developer", "programmer",
        "accountant", "lawyer", "attorney", "paralegal", "judge",
        "chef", "baker", "barista", "bartender", "waitress", "server",
        "mechanic", "electrician", "plumber", "carpenter", "contractor",
        "real estate agent", "realtor", "entrepreneur", "business owner",
        "hairstylist", "barber", "makeup artist", "nail tech",
        "photographer", "graphic designer", "artist", "musician",
        "writer", "author", "journalist", "blogger", "influencer"
    ],
    
    "Family & Relationships": [
        "mom life", "dad life", "mama bear", "papa bear", "boy mom",
        "girl mom", "dog mom", "cat mom", "bonus mom", "stepmom",
        "grandma", "nana", "mimi", "grammy", "meemaw", "oma",
        "grandpa", "papa", "gramps", "pops", "peepaw", "opa",
        "aunt life", "auntie", "uncle", "godmother", "godfather",
        "best friend", "sister", "brother", "twins", "triplets",
        "wife", "husband", "spouse", "partner", "soulmate",
        "engaged", "bride", "groom", "newlywed", "married",
        "anniversary", "love", "family", "blessed", "grateful"
    ],
    
    "Hobbies & Interests": [
        "coffee lover", "coffee addict", "caffeine", "espresso", "latte",
        "book lover", "bookworm", "reading", "bibliophile", "book club",
        "gamer", "gaming", "video games", "pc gamer", "console gamer",
        "camping", "hiking", "outdoors", "nature", "adventure",
        "fishing", "hunting", "archery", "shooting", "gun owner",
        "gardening", "plant mom", "plant lady", "green thumb",
        "cooking", "baking", "foodie", "chef life", "home cook",
        "wine", "wine lover", "wine mom", "sommelier", "vineyard",
        "beer", "craft beer", "ipa", "brewery", "beer lover",
        "travel", "wanderlust", "adventure", "explore", "vacation",
        "yoga", "meditation", "mindfulness", "zen", "namaste",
        "running", "runner", "marathon", "5k", "jogging",
        "gym", "fitness", "workout", "bodybuilding", "crossfit",
        "photography", "photographer", "camera", "canon", "nikon",
        "music", "band", "concert", "festival", "musician"
    ],
    
    "Sports & Teams": [
        "football", "nfl", "college football", "fantasy football",
        "basketball", "nba", "college basketball", "march madness",
        "baseball", "mlb", "little league", "softball",
        "soccer", "football", "mls", "premier league", "fifa",
        "hockey", "nhl", "ice hockey", "field hockey",
        "volleyball", "beach volleyball", "setter", "hitter",
        "tennis", "pickleball", "badminton", "table tennis",
        "golf", "golfer", "pga", "golf course", "country club",
        "swimming", "swimmer", "dive team", "water polo",
        "track", "cross country", "relay", "sprinter", "distance runner",
        "wrestling", "wrestler", "ufc", "mma", "boxing",
        "cheerleading", "cheer", "cheerleader", "pom squad",
        "dance", "dancer", "ballet", "hip hop", "jazz dance"
    ],
    
    "Seasons & Holidays": [
        "christmas", "xmas", "santa", "reindeer", "snowman",
        "halloween", "spooky", "witch", "pumpkin", "ghost",
        "thanksgiving", "turkey", "grateful", "blessed", "feast",
        "valentine", "love", "hearts", "cupid", "romance",
        "easter", "bunny", "eggs", "spring", "resurrection",
        "fourth of july", "independence day", "america", "patriotic",
        "new year", "nye", "2025", "2026", "celebration",
        "summer", "beach", "sun", "vacation", "pool",
        "fall", "autumn", "leaves", "pumpkin spice", "cozy",
        "winter", "snow", "cold", "cozy", "hygge",
        "spring", "flowers", "bloom", "fresh", "renewal",
        "birthday", "bday", "celebration", "party", "cake"
    ],
    
    "Zodiac & Astrology": [
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
        "zodiac", "astrology", "horoscope", "star sign", "birth chart",
        "moon sign", "rising sign", "mercury retrograde", "crystal",
        "tarot", "spiritual", "mystic", "witch", "magic"
    ],
    
    "Personality & Humor": [
        "sarcasm", "sarcastic", "funny", "humor", "witty",
        "introvert", "extrovert", "ambivert", "antisocial", "homebody",
        "lazy", "sleepy", "tired", "nap", "sleep",
        "coffee", "wine", "caffeine", "alcohol", "drinking",
        "savage", "queen", "boss", "badass", "fierce",
        "hot mess", "chaos", "disaster", "messy", "clumsy",
        "awkward", "weird", "odd", "strange", "quirky",
        "crazy", "wild", "fun", "party", "adventure",
        "chill", "relaxed", "calm", "zen", "peaceful"
    ],
    
    "Political & Patriotic": [
        "america", "usa", "american flag", "patriotic", "freedom",
        "military", "army", "navy", "air force", "marines", "coast guard",
        "veteran", "vet", "service", "hero", "soldier",
        "conservative", "liberal", "independent", "libertarian",
        "republican", "democrat", "vote", "election", "politics",
        "trump", "biden", "maga", "resist", "impeach",
        "constitution", "second amendment", "free speech", "liberty"
    ],
    
    "States & Cities": [
        "texas", "california", "florida", "new york", "pennsylvania",
        "ohio", "illinois", "michigan", "georgia", "north carolina",
        "virginia", "washington", "arizona", "massachusetts", "tennessee",
        "indiana", "missouri", "maryland", "wisconsin", "colorado",
        "minnesota", "south carolina", "alabama", "louisiana", "kentucky",
        "oregon", "oklahoma", "connecticut", "utah", "iowa",
        "nevada", "arkansas", "mississippi", "kansas", "new mexico",
        "nebraska", "west virginia", "idaho", "hawaii", "new hampshire",
        "maine", "montana", "rhode island", "delaware", "south dakota",
        "north dakota", "alaska", "vermont", "wyoming",
        "new york city", "los angeles", "chicago", "houston", "phoenix",
        "philadelphia", "san antonio", "san diego", "dallas", "austin"
    ],
    
    "Mental Health & Wellness": [
        "anxiety", "depression", "mental health", "therapy", "self care",
        "mindfulness", "meditation", "healing", "recovery", "strength",
        "survivor", "warrior", "fighter", "brave", "courage",
        "hope", "faith", "believe", "positive", "motivation",
        "inspire", "empower", "support", "awareness", "advocate"
    ],
    
    "Food & Drinks": [
        "pizza", "tacos", "burgers", "fries", "wings",
        "bacon", "cheese", "chocolate", "candy", "dessert",
        "pasta", "sushi", "ramen", "pho", "curry",
        "bbq", "grill", "smoker", "brisket", "ribs",
        "vegan", "vegetarian", "keto", "paleo", "gluten free",
        "organic", "farm", "farmer", "agriculture", "harvest"
    ],
    
    "Technology & Gaming": [
        "tech", "geek", "nerd", "coding", "programming",
        "computer", "pc", "laptop", "tablet", "phone",
        "apple", "android", "windows", "linux", "mac",
        "minecraft", "fortnite", "roblox", "pokemon", "zelda",
        "mario", "sonic", "playstation", "xbox", "nintendo",
        "twitch", "streamer", "youtuber", "content creator"
    ],
    
    "Fashion & Beauty": [
        "fashion", "style", "trendy", "chic", "cute",
        "makeup", "beauty", "skincare", "cosmetics", "lipstick",
        "nails", "manicure", "pedicure", "nail art", "gel nails",
        "hair", "hairstyle", "salon", "extensions", "balayage",
        "shopping", "retail", "boutique", "online shopping"
    ],
    
    "Education & School": [
        "teacher", "student", "school", "education", "learning",
        "kindergarten", "elementary", "middle school", "high school",
        "college", "university", "graduate", "alumni", "class of",
        "principal", "counselor", "librarian", "coach", "tutor",
        "homeschool", "online learning", "study", "exam", "test"
    ],
    
    "Retirement & Age": [
        "retired", "retirement", "senior", "elderly", "golden years",
        "grandparent", "boomer", "millennial", "gen z", "gen x",
        "vintage", "classic", "retro", "old school", "throwback"
    ],
    
    "Religion & Faith": [
        "christian", "catholic", "protestant", "baptist", "methodist",
        "jesus", "god", "faith", "prayer", "blessed",
        "church", "worship", "praise", "amen", "hallelujah",
        "bible", "scripture", "verse", "gospel", "cross",
        "jewish", "judaism", "hebrew", "shalom", "kosher",
        "muslim", "islam", "allah", "mosque", "ramadan",
        "buddhist", "zen", "karma", "dharma", "namaste",
        "spiritual", "meditation", "mindfulness", "peace"
    ],
    
    "LGBTQ+": [
        "pride", "lgbtq", "gay", "lesbian", "bisexual",
        "transgender", "queer", "rainbow", "love is love",
        "ally", "equality", "human rights", "inclusive"
    ],
    
    "Causes & Awareness": [
        "breast cancer", "pink ribbon", "survivor", "awareness",
        "autism", "adhd", "disability", "special needs",
        "environment", "climate", "earth", "recycle", "eco",
        "animal rescue", "adopt dont shop", "foster", "rescue",
        "black lives matter", "blm", "equality", "justice"
    ]
}

def generate_compound_keywords():
    """Generate compound keywords by combining base keywords with modifiers"""
    
    modifiers = {
        "prefix": [
            "proud", "best", "super", "awesome", "amazing", "professional",
            "certified", "licensed", "expert", "future", "retired",
            "world's best", "world's okayest", "official", "professional"
        ],
        "suffix": [
            "life", "vibes", "goals", "mode", "squad", "crew", "team",
            "gang", "club", "nation", "family", "tribe", "community",
            "lover", "fan", "addict", "enthusiast", "obsessed"
        ],
        "year": ["2024", "2025", "2026"]
    }
    
    compounds = []
    
    # Add some compound variations
    for category, keywords in POD_KEYWORDS.items():
        for keyword in keywords[:10]:  # Top 10 from each category
            # Add prefix variations
            compounds.append(f"proud {keyword}")
            compounds.append(f"best {keyword}")
            
            # Add suffix variations
            if not any(suffix in keyword for suffix in ["life", "lover", "mom", "dad"]):
                compounds.append(f"{keyword} life")
                compounds.append(f"{keyword} lover")
    
    return compounds

def generate_keywords_json():
    """Generate the complete keywords JSON file"""
    
    all_keywords = []
    
    # Add all base keywords
    for category, keywords in POD_KEYWORDS.items():
        for keyword in keywords:
            all_keywords.append({
                "keyword": keyword,
                "category": category,
                "estimated_volume": estimate_volume(keyword),
                "source": "curated_pod_trends"
            })
    
    # Add compound keywords
    compounds = generate_compound_keywords()
    for keyword in compounds:
        all_keywords.append({
            "keyword": keyword,
            "category": "Compound",
            "estimated_volume": estimate_volume(keyword),
            "source": "compound_generation"
        })
    
    return all_keywords

def estimate_volume(keyword):
    """Estimate search volume based on keyword characteristics"""
    
    # High-volume indicators
    high_volume_terms = [
        "mom", "dad", "dog", "cat", "teacher", "nurse", "christmas",
        "coffee", "love", "family", "america", "texas", "new york"
    ]
    
    # Medium-volume indicators
    medium_volume_terms = [
        "life", "lover", "girl", "boy", "best", "proud", "blessed"
    ]
    
    keyword_lower = keyword.lower()
    
    # Check for high-volume terms
    if any(term in keyword_lower for term in high_volume_terms):
        return "high"  # 10,000+ searches/month
    
    # Check for medium-volume terms
    elif any(term in keyword_lower for term in medium_volume_terms):
        return "medium"  # 1,000-10,000 searches/month
    
    # Default to low-medium
    else:
        return "low"  # 100-1,000 searches/month

def main():
    print("🎨 Generating POD Keywords...")
    print("=" * 60)
    
    # Generate keywords
    keywords = generate_keywords_json()
    
    # Save to file
    output_file = Path("pod_keywords.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(keywords, f, indent=2, ensure_ascii=False)
    
    # Statistics
    total = len(keywords)
    high_vol = len([k for k in keywords if k['estimated_volume'] == 'high'])
    medium_vol = len([k for k in keywords if k['estimated_volume'] == 'medium'])
    low_vol = len([k for k in keywords if k['estimated_volume'] == 'low'])
    
    categories = {}
    for k in keywords:
        cat = k['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n✅ Generated {total} keywords")
    print(f"\n📊 Volume Distribution:")
    print(f"   High Volume (10k+):     {high_vol:4d} keywords")
    print(f"   Medium Volume (1k-10k): {medium_vol:4d} keywords")
    print(f"   Low Volume (100-1k):    {low_vol:4d} keywords")
    
    print(f"\n📁 Categories:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"   {cat:30s} {count:4d} keywords")
    
    print(f"\n💾 Saved to: {output_file}")
    print("\n🎯 Next Step:")
    print("   Run: python import_keywords.py")

if __name__ == "__main__":
    main()
