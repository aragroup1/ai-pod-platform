"""
Enhanced Trend Service with Product Research - FIXED JSON HANDLING
Fetches trends from Google, analyzes search volume, and identifies profitable niches
"""
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger
import asyncio
import json

from app.database import DatabasePool
from app.core.trends.google_trends import get_trends_analyzer
from app.core.trends.keyword_planner import get_keyword_planner


class TrendService:
    """Service for comprehensive trend research and product opportunity identification"""
    
    def __init__(self, db_pool: DatabasePool):
        self.db_pool = db_pool
        self.trends_analyzer = get_trends_analyzer()
        self.keyword_planner = get_keyword_planner()
    
    async def fetch_and_store_trends(
        self,
        region: str = 'GB',
        min_score: float = 6.0,
        limit: int = 20
    ) -> List[Dict]:
        """
        Comprehensive trend fetching with multiple data sources
        
        This method:
        1. Fetches trending searches from Google Trends
        2. Enriches with search volume data (if Keyword Planner available)
        3. Filters for POD-suitable keywords
        4. Stores high-potential trends in database
        """
        logger.info(f"🔍 Starting comprehensive trend research for region: {region}")
        
        # Step 1: Get trending topics from Google
        trending_topics = await self.trends_analyzer.get_trending_topics_for_pod(
            min_score=min_score
        )
        
        if not trending_topics:
            logger.warning("No trends fetched from Google")
            # Fallback to proven POD keywords
            trending_topics = await self._get_fallback_trends()
        
        # Step 2: Enrich with Keyword Planner data (if available)
        if self.keyword_planner and self.keyword_planner.is_available():
            logger.info("📊 Enriching with Google Keyword Planner data...")
            keywords = [t['keyword'] for t in trending_topics]
            volume_data = await self.keyword_planner.analyze_trend_keywords(
                keywords=keywords[:20],  # Limit to top 20
                country_code=region
            )
            
            # Merge volume data with trends
            for trend in trending_topics:
                kw_data = next(
                    (k for k in volume_data.get('keywords', []) 
                     if k['keyword'].lower() == trend['keyword'].lower()),
                    None
                )
                if kw_data:
                    trend['search_volume'] = kw_data['avg_monthly_searches']
                    trend['competition'] = kw_data['competition']
                    trend['cpc'] = kw_data.get('high_top_of_page_bid', 0)
        
        # Step 3: Score and filter trends
        scored_trends = self._score_trends_for_pod(trending_topics)
        
        # Step 4: Store in database - FIX JSON SERIALIZATION
        stored_trends = []
        for topic in scored_trends[:limit]:
            try:
                # Check if trend already exists (in last 7 days)
                existing = await self.db_pool.fetchval(
                    """
                    SELECT id FROM trends 
                    WHERE LOWER(keyword) = LOWER($1)
                    AND created_at > NOW() - INTERVAL '7 days'
                    """,
                    topic['keyword']
                )
                
                if existing:
                    logger.debug(f"Trend already exists: {topic['keyword']}")
                    continue
                
                # FIXED: Convert dict to JSON string for database
                data_json = json.dumps({
                    'is_rising': topic.get('is_rising', False),
                    'competition': topic.get('competition', 'medium'),
                    'cpc': topic.get('cpc', 0),
                    'fetched_at': datetime.utcnow().isoformat(),
                    'source': 'google_trends',
                    'pod_suitable': True,
                    'designs_allocated': self._calculate_designs_for_volume(topic.get('search_volume', 10000))
                })
                
                # Insert new trend
                trend_id = await self.db_pool.fetchval(
                    """
                    INSERT INTO trends (
                        keyword, search_volume, trend_score, 
                        geography, category, data
                    ) VALUES ($1, $2, $3, $4, $5, $6::jsonb)
                    RETURNING id
                    """,
                    topic['keyword'],
                    topic.get('search_volume', 10000),  # Default if no data
                    topic['pod_score'],  # Our calculated score
                    topic.get('geography', region),
                    topic.get('category', 'general'),
                    data_json  # Pass as JSON string
                )
                
                stored_trends.append({
                    'id': trend_id,
                    'keyword': topic['keyword'],
                    'search_volume': topic.get('search_volume', 10000),
                    'trend_score': topic['pod_score'],
                    'category': topic.get('category', 'general')
                })
                
                logger.info(f"✅ Stored trend: {topic['keyword']} (score: {topic['pod_score']:.1f}, volume: {topic.get('search_volume', 'N/A')})")
                
            except Exception as e:
                logger.error(f"Error storing trend '{topic['keyword']}': {e}")
                continue
        
        logger.info(f"📦 Stored {len(stored_trends)} new high-potential trends")
        
        # Return summary
        return stored_trends
    
    def _calculate_designs_for_volume(self, volume: int) -> int:
        """Calculate how many designs to allocate based on search volume"""
        if volume >= 50000:
            return 100
        elif volume >= 30000:
            return 75
        elif volume >= 20000:
            return 50
        elif volume >= 10000:
            return 30
        elif volume >= 5000:
            return 20
        elif volume >= 2000:
            return 10
        else:
            return 5
    
    def _score_trends_for_pod(self, trends: List[Dict]) -> List[Dict]:
        """
        Score trends specifically for POD potential
        
        Scoring factors:
        - Search volume (most important)
        - Rising trend status
        - Competition level
        - Visual potential (can it be art?)
        - Commercial intent
        """
        scored = []
        
        for trend in trends:
            keyword = trend['keyword'].lower()
            
            # Base score from Google trend score
            score = trend.get('trend_score', 5.0)
            
            # Boost for high search volume
            volume = trend.get('search_volume', 0)
            if volume > 50000:
                score += 2.0
            elif volume > 20000:
                score += 1.5
            elif volume > 10000:
                score += 1.0
            
            # Boost for rising trends
            if trend.get('is_rising', False):
                score += 1.5
            
            # Boost for low competition
            competition = trend.get('competition', 'medium').lower()
            if competition == 'low':
                score += 1.0
            elif competition == 'high':
                score -= 0.5
            
            # Boost for visual/artistic keywords
            visual_keywords = [
                'art', 'design', 'aesthetic', 'vintage', 'retro', 'modern',
                'minimalist', 'abstract', 'nature', 'landscape', 'floral',
                'geometric', 'pattern', 'illustration', 'photography',
                'sunset', 'ocean', 'mountain', 'forest', 'city', 'skyline'
            ]
            if any(vk in keyword for vk in visual_keywords):
                score += 1.5
            
            # Boost for POD-friendly categories
            pod_categories = [
                'home decor', 'wall art', 'poster', 'print', 'canvas',
                'motivation', 'quote', 'inspirational', 'funny', 'cute',
                'animal', 'pet', 'travel', 'adventure', 'hobby'
            ]
            if any(pc in keyword for pc in pod_categories):
                score += 1.0
            
            # Penalty for problematic keywords
            avoid_keywords = [
                'news', 'covid', 'political', 'election', 'crisis',
                'death', 'disease', 'scandal', 'crypto', 'stock'
            ]
            if any(ak in keyword for ak in avoid_keywords):
                score -= 3.0
            
            # Cap score at 10
            score = min(score, 10.0)
            
            trend['pod_score'] = score
            
            if score >= 6.0:  # Only include high-potential trends
                scored.append(trend)
        
        # Sort by POD score
        scored.sort(key=lambda x: x['pod_score'], reverse=True)
        
        return scored
    
    async def _get_fallback_trends(self) -> List[Dict]:
        """
        Fallback trends when Google Trends is unavailable
        These are proven high-performing POD niches
        """
        fallback_keywords = [
            # Nature & Landscapes
            ('mountain landscape minimalist', 15000, 'nature', 8.5),
            ('sunset ocean waves', 18000, 'nature', 8.7),
            ('forest fog photography', 12000, 'nature', 8.2),
            ('desert minimalist art', 8000, 'nature', 7.8),
            
            # Typography & Quotes
            ('motivational quotes workspace', 25000, 'typography', 9.0),
            ('funny office quotes', 20000, 'typography', 8.5),
            ('inspirational wall art', 30000, 'typography', 9.2),
            ('good vibes only poster', 15000, 'typography', 8.3),
            
            # Abstract & Geometric
            ('abstract geometric shapes', 16000, 'abstract', 8.4),
            ('boho abstract art', 14000, 'abstract', 8.2),
            ('minimalist line art', 18000, 'abstract', 8.6),
            ('modern abstract painting', 12000, 'abstract', 8.0),
            
            # Animals & Pets
            ('cute cat illustration', 22000, 'animals', 8.8),
            ('dog portrait minimalist', 15000, 'animals', 8.3),
            ('wildlife photography prints', 10000, 'animals', 7.9),
            ('bird watercolor art', 8000, 'animals', 7.5),
            
            # Vintage & Retro
            ('vintage travel posters', 20000, 'vintage', 8.7),
            ('retro sunset design', 18000, 'vintage', 8.5),
            ('mid century modern art', 15000, 'vintage', 8.3),
            ('vintage botanical prints', 12000, 'vintage', 8.1),
            
            # Botanical & Floral
            ('botanical line drawing', 14000, 'botanical', 8.2),
            ('watercolor flowers art', 16000, 'botanical', 8.4),
            ('pressed flower prints', 10000, 'botanical', 7.8),
            ('tropical leaves pattern', 12000, 'botanical', 8.0)
        ]
        
        trends = []
        for keyword, volume, category, score in fallback_keywords:
            trends.append({
                'keyword': keyword,
                'search_volume': volume,
                'trend_score': score,
                'category': category,
                'is_rising': True,  # Assume these are evergreen rising trends
                'geography': 'GB',
                'pod_score': score
            })
        
        logger.info(f"📋 Using {len(trends)} proven fallback trends")
        return trends
    
    async def fetch_initial_10k_keywords(self) -> Dict:
        """
        Fetch comprehensive keyword set for initial 10K design launch
        This will gather keywords from multiple categories to ensure diversity
        """
        logger.info("🚀 Fetching keywords for 10K initial design launch...")
        
        all_keywords = []
        
        # Categories with expected design counts
        categories_keywords = {
            'nature': [
                ('mountain landscape', 25000, 50),
                ('sunset photography', 22000, 40),
                ('ocean waves art', 20000, 40),
                ('forest prints', 18000, 35),
                ('desert landscape', 15000, 30),
                ('lake reflection', 12000, 25),
                ('northern lights', 16000, 30),
                ('tropical beach', 24000, 45),
                ('autumn leaves', 14000, 25),
                ('winter scene', 13000, 25),
            ],
            'typography': [
                ('motivational quotes', 35000, 70),
                ('inspirational sayings', 30000, 60),
                ('funny quotes', 28000, 55),
                ('office humor', 22000, 40),
                ('bedroom quotes', 20000, 40),
                ('kitchen sayings', 18000, 35),
                ('bathroom quotes', 15000, 30),
                ('gym motivation', 25000, 50),
                ('love quotes', 32000, 65),
                ('family quotes', 24000, 45),
            ],
            'abstract': [
                ('geometric patterns', 20000, 40),
                ('abstract shapes', 18000, 35),
                ('modern art', 22000, 40),
                ('minimalist design', 25000, 50),
                ('boho patterns', 16000, 30),
                ('scandinavian art', 14000, 25),
                ('color blocks', 12000, 20),
                ('line drawings', 15000, 30),
                ('circle art', 10000, 20),
                ('triangle patterns', 8000, 15),
            ],
            'botanical': [
                ('botanical prints', 24000, 45),
                ('flower art', 22000, 40),
                ('leaf patterns', 18000, 35),
                ('tropical plants', 20000, 40),
                ('cactus art', 15000, 30),
                ('succulent prints', 14000, 25),
                ('herb illustrations', 12000, 20),
                ('garden flowers', 16000, 30),
                ('wildflowers', 13000, 25),
                ('monstera leaf', 11000, 20),
            ],
            'animals': [
                ('cat art', 28000, 55),
                ('dog prints', 26000, 50),
                ('bird illustrations', 18000, 35),
                ('elephant art', 16000, 30),
                ('lion prints', 14000, 25),
                ('butterfly art', 15000, 30),
                ('horse photography', 13000, 25),
                ('owl illustrations', 12000, 20),
                ('bear art', 11000, 20),
                ('fox prints', 10000, 20),
            ],
            'city': [
                ('new york skyline', 30000, 60),
                ('london prints', 25000, 50),
                ('paris art', 28000, 55),
                ('tokyo cityscape', 18000, 35),
                ('city maps', 20000, 40),
                ('street photography', 16000, 30),
                ('urban art', 14000, 25),
                ('architecture prints', 15000, 30),
                ('bridges art', 12000, 20),
                ('skyscrapers', 10000, 20),
            ],
            'vintage': [
                ('retro posters', 22000, 40),
                ('vintage travel', 20000, 40),
                ('mid century art', 18000, 35),
                ('vintage flowers', 16000, 30),
                ('classic cars', 14000, 25),
                ('retro patterns', 15000, 30),
                ('vintage maps', 13000, 25),
                ('old advertisements', 11000, 20),
                ('vintage photography', 12000, 20),
                ('antique prints', 10000, 20),
            ],
            'seasonal': [
                ('christmas art', 35000, 70),
                ('halloween prints', 25000, 50),
                ('easter decorations', 18000, 35),
                ('summer vibes', 20000, 40),
                ('spring flowers', 16000, 30),
                ('autumn decor', 14000, 25),
                ('winter wonderland', 15000, 30),
                ('valentines art', 22000, 40),
                ('thanksgiving prints', 12000, 20),
                ('new year art', 13000, 25),
            ],
            'space': [
                ('galaxy art', 18000, 35),
                ('moon phases', 16000, 30),
                ('constellation map', 14000, 25),
                ('solar system', 12000, 20),
                ('astronaut art', 10000, 20),
                ('nebula prints', 11000, 20),
                ('planets poster', 13000, 25),
                ('stars pattern', 9000, 15),
                ('rocket ship', 8000, 15),
                ('space exploration', 7000, 10),
            ],
            'sports': [
                ('gym motivation', 20000, 40),
                ('yoga poses', 18000, 35),
                ('running quotes', 15000, 30),
                ('basketball art', 14000, 25),
                ('football prints', 16000, 30),
                ('golf art', 12000, 20),
                ('tennis posters', 10000, 20),
                ('cycling art', 9000, 15),
                ('swimming quotes', 8000, 15),
                ('fitness motivation', 22000, 40),
            ]
        }
        
        total_designs = 0
        for category, keywords in categories_keywords.items():
            for keyword, volume, designs in keywords:
                all_keywords.append({
                    'keyword': keyword,
                    'search_volume': volume,
                    'category': category,
                    'designs_allocated': designs,
                    'trend_score': 8.0  # Good baseline score
                })
                total_designs += designs
        
        # Store all keywords
        stored_count = 0
        for kw in all_keywords:
            try:
                # Check if exists
                existing = await self.db_pool.fetchval(
                    """
                    SELECT id FROM trends 
                    WHERE LOWER(keyword) = LOWER($1)
                    """,
                    kw['keyword']
                )
                
                if not existing:
                    data_json = json.dumps({
                        'designs_allocated': kw['designs_allocated'],
                        'initial_10k_batch': True,
                        'created_at': datetime.utcnow().isoformat()
                    })
                    
                    await self.db_pool.execute(
                        """
                        INSERT INTO trends (
                            keyword, search_volume, trend_score,
                            geography, category, data
                        ) VALUES ($1, $2, $3, $4, $5, $6::jsonb)
                        """,
                        kw['keyword'],
                        kw['search_volume'],
                        kw['trend_score'],
                        'GB',
                        kw['category'],
                        data_json
                    )
                    stored_count += 1
                    
            except Exception as e:
                logger.error(f"Error storing keyword {kw['keyword']}: {e}")
        
        return {
            'total_keywords': len(all_keywords),
            'keywords_stored': stored_count,
            'total_designs_planned': total_designs,
            'categories': len(categories_keywords),
            'estimated_cost_test': f"£{total_designs * 0.003:.2f}",
            'estimated_cost_production': f"£{total_designs * 0.04:.2f}",
            'message': f"Ready to generate {total_designs} designs across {len(categories_keywords)} categories"
        }
    
    async def get_trends_without_products(self, limit: int = 10) -> List[Dict]:
        """
        Get trends that don't have products yet
        Prioritized by POD score
        """
        try:
            query = """
                SELECT t.id, t.keyword, t.search_volume, t.trend_score,
                       t.geography, t.category, t.created_at, t.data
                FROM trends t
                LEFT JOIN artwork a ON a.trend_id = t.id
                WHERE a.id IS NULL
                AND t.trend_score >= 6.0
                ORDER BY t.trend_score DESC, t.search_volume DESC
                LIMIT $1
            """
            results = await self.db_pool.fetch(query, limit)
            
            trends = []
            for row in results:
                trends.append({
                    'id': row['id'],
                    'keyword': row['keyword'],
                    'search_volume': row['search_volume'],
                    'trend_score': float(row['trend_score']),
                    'geography': row['geography'],
                    'category': row['category'],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                    'data': row['data']
                })
            
            return trends
            
        except Exception as e:
            logger.error(f"Error fetching trends without products: {e}")
            return []
    
    async def get_top_trends(
        self,
        limit: int = 20,
        min_score: float = 6.0,
        category: Optional[str] = None
    ) -> List[Dict]:
        """Get top trends from database"""
        try:
            if category:
                query = """
                    SELECT id, keyword, search_volume, trend_score, 
                           geography, category, created_at, data
                    FROM trends
                    WHERE trend_score >= $1 
                    AND category = $2
                    ORDER BY trend_score DESC, search_volume DESC, created_at DESC
                    LIMIT $3
                """
                results = await self.db_pool.fetch(query, min_score, category, limit)
            else:
                query = """
                    SELECT id, keyword, search_volume, trend_score, 
                           geography, category, created_at, data
                    FROM trends
                    WHERE trend_score >= $1
                    ORDER BY trend_score DESC, search_volume DESC, created_at DESC
                    LIMIT $2
                """
                results = await self.db_pool.fetch(query, min_score, limit)
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error fetching top trends: {e}")
            return []
