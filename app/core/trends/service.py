"""
Enhanced Trend Service with Product Research
Fetches trends from Google, analyzes search volume, and identifies profitable niches
"""
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger
import asyncio

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
        if self.keyword_planner.is_available():
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
        
        # Step 4: Store in database
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
                
                # Insert new trend
                trend_id = await self.db_pool.fetchval(
                    """
                    INSERT INTO trends (
                        keyword, search_volume, trend_score, 
                        geography, category, data
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id
                    """,
                    topic['keyword'],
                    topic.get('search_volume', 10000),  # Default if no data
                    topic['pod_score'],  # Our calculated score
                    topic.get('geography', region),
                    topic.get('category', 'general'),
                    {
                        'is_rising': topic.get('is_rising', False),
                        'competition': topic.get('competition', 'medium'),
                        'cpc': topic.get('cpc', 0),
                        'fetched_at': datetime.utcnow().isoformat(),
                        'source': 'google_trends',
                        'pod_suitable': True
                    }
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
    
    async def analyze_etsy_demand(self, keyword: str) -> Dict:
        """
        Analyze demand on Etsy (when API is available)
        For now, returns estimated data
        """
        # TODO: Implement when Etsy API is approved
        # This is a placeholder that estimates based on keyword
        
        keyword_lower = keyword.lower()
        
        # Estimate based on keyword characteristics
        base_listings = 5000
        
        # Popular categories get more listings
        if any(word in keyword_lower for word in ['vintage', 'boho', 'minimalist', 'wall art']):
            base_listings *= 2
        
        if any(word in keyword_lower for word in ['quote', 'motivational', 'inspirational']):
            base_listings *= 1.5
        
        return {
            'estimated_listings': int(base_listings),
            'competition_level': 'medium' if base_listings < 10000 else 'high',
            'recommended_price': 29.99 if 'premium' in keyword_lower else 19.99,
            'best_sellers_avg_price': 24.99
        }
    
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
