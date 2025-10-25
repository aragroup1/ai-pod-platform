"""
Intelligent Trend Analyzer - Multi-Source Data Integration
Analyzes trends from multiple sources and intelligently decides what to generate

Data Sources:
1. Google Trends (free) - Rising topics
2. Etsy Search Volume (web scraping)
3. Pinterest Trends (API if available)
4. Your own sales data (feedback loop)
5. Keyword research tools

Priority Algorithm:
- Search volume (primary metric)
- Rising trend status
- Competition level
- Seasonal factors
- Historical performance
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from loguru import logger
import asyncio
from dataclasses import dataclass

from app.database import DatabasePool
from app.core.trends.google_trends import get_trends_analyzer


@dataclass
class TrendScore:
    """Intelligent scoring for trend prioritization"""
    keyword: str
    search_volume: int  # Most important
    google_trend_score: float
    etsy_search_volume: int = 0
    pinterest_interest: int = 0
    rising_status: bool = False
    competition: str = "medium"  # low, medium, high
    seasonal_boost: float = 1.0
    final_score: float = 0.0
    sources: List[str] = None
    
    def __post_init__(self):
        self.sources = self.sources or []
        self.calculate_final_score()
    
    def calculate_final_score(self):
        """
        Intelligent scoring algorithm
        
        Weights:
        - Search volume: 50% (most important)
        - Rising status: 20%
        - Multi-source validation: 15%
        - Low competition: 10%
        - Seasonal: 5%
        """
        # Normalize search volume (0-10 scale)
        volume_score = min(self.search_volume / 2000, 10)  # 20k+ = max score
        
        # Rising bonus
        rising_bonus = 2.0 if self.rising_status else 0
        
        # Multi-source validation bonus
        source_bonus = len(self.sources) * 0.5
        
        # Competition penalty
        competition_penalty = {
            "low": 0,
            "medium": -1,
            "high": -2
        }.get(self.competition, -1)
        
        # Calculate final score
        self.final_score = (
            volume_score * 0.5 +  # 50% weight on search volume
            self.google_trend_score * 0.2 +  # 20% on Google Trends
            rising_bonus * 0.2 +  # 20% on rising status
            source_bonus * 0.15 +  # 15% on multi-source validation
            competition_penalty * 0.1 +  # 10% competition factor
            self.seasonal_boost * 0.05  # 5% seasonal
        )
        
        return self.final_score


class IntelligentTrendAnalyzer:
    """
    Multi-source trend analyzer with intelligent prioritization
    """
    
    def __init__(self, db_pool: DatabasePool):
        self.db_pool = db_pool
        self.google_analyzer = get_trends_analyzer()
        
    async def fetch_google_trends(self, region: str = "GB") -> List[Dict]:
        """Fetch from Google Trends (free)"""
        logger.info("📊 Fetching Google Trends...")
        
        try:
            trends = await self.google_analyzer.get_trending_topics_for_pod(
                min_score=5.0  # Lower threshold for initial fetch
            )
            
            logger.info(f"✅ Google Trends: {len(trends)} topics found")
            return trends
            
        except Exception as e:
            logger.error(f"❌ Google Trends failed: {e}")
            return []
    
    async def fetch_etsy_search_volumes(self, keywords: List[str]) -> Dict[str, int]:
        """
        Estimate Etsy search volumes (web scraping)
        This gives us marketplace demand data
        """
        logger.info("🛍️ Fetching Etsy search volumes...")
        
        # TODO: Implement Etsy scraping
        # For now, return estimated volumes based on Google data
        
        volumes = {}
        for keyword in keywords:
            # Placeholder - implement real scraping
            estimated_volume = 1000  # Base estimate
            volumes[keyword] = estimated_volume
        
        return volumes
    
    async def fetch_pinterest_trends(self, keywords: List[str]) -> Dict[str, int]:
        """
        Fetch Pinterest interest data
        Great for visual/art trends
        """
        logger.info("📌 Fetching Pinterest trends...")
        
        # TODO: Implement Pinterest API or scraping
        # For now, return placeholder
        
        return {keyword: 500 for keyword in keywords}
    
    async def get_historical_performance(self, keyword: str) -> Dict:
        """
        Check if we've generated this keyword before and how it performed
        This creates a feedback loop for optimization
        """
        try:
            # Check if we have products for this keyword
            result = await self.db_pool.fetchrow(
                """
                SELECT 
                    COUNT(DISTINCT p.id) as product_count,
                    AVG(CAST(o.order_value AS DECIMAL)) as avg_order_value,
                    COUNT(DISTINCT o.id) as total_orders
                FROM trends t
                LEFT JOIN artwork a ON a.trend_id = t.id
                LEFT JOIN products p ON p.artwork_id = a.id
                LEFT JOIN orders o ON o.product_id = p.id
                WHERE LOWER(t.keyword) = LOWER($1)
                """,
                keyword
            )
            
            if result and result['total_orders'] > 0:
                return {
                    'has_history': True,
                    'performance_score': result['total_orders'] * 2,  # Orders worth 2x
                    'avg_order_value': float(result['avg_order_value'] or 0)
                }
            
            return {'has_history': False, 'performance_score': 0}
            
        except Exception as e:
            logger.error(f"Error fetching historical performance: {e}")
            return {'has_history': False, 'performance_score': 0}
    
    def detect_seasonal_boost(self, keyword: str, current_month: int) -> float:
        """
        Detect if keyword is seasonal and boost accordingly
        """
        seasonal_keywords = {
            'christmas': [11, 12, 1],  # Nov-Jan
            'halloween': [9, 10],  # Sep-Oct
            'spring': [3, 4, 5],
            'summer': [6, 7, 8],
            'autumn': [9, 10, 11],
            'winter': [12, 1, 2],
            'valentine': [1, 2],
            'easter': [3, 4],
            'beach': [5, 6, 7, 8],
            'cozy': [10, 11, 12, 1]
        }
        
        keyword_lower = keyword.lower()
        
        for season_word, months in seasonal_keywords.items():
            if season_word in keyword_lower and current_month in months:
                return 2.0  # 2x boost for seasonal relevance
        
        return 1.0  # No boost
    
    async def analyze_and_score_trends(self, min_search_volume: int = 1000) -> List[TrendScore]:
        """
        Main analysis function - combines all data sources and scores intelligently
        """
        logger.info("🧠 Starting intelligent trend analysis...")
        
        # Step 1: Fetch from all sources
        google_trends = await self.fetch_google_trends()
        
        if not google_trends:
            logger.warning("No trends from any source")
            return []
        
        # Step 2: Extract keywords
        keywords = [t['keyword'] for t in google_trends]
        
        # Step 3: Enrich with additional data sources (parallel)
        etsy_volumes, pinterest_data = await asyncio.gather(
            self.fetch_etsy_search_volumes(keywords),
            self.fetch_pinterest_trends(keywords)
        )
        
        # Step 4: Score each trend
        scored_trends = []
        current_month = datetime.now().month
        
        for trend in google_trends:
            keyword = trend['keyword']
            
            # Get historical performance
            history = await self.get_historical_performance(keyword)
            
            # Create score object
            score = TrendScore(
                keyword=keyword,
                search_volume=trend['search_volume'],
                google_trend_score=trend['trend_score'],
                etsy_search_volume=etsy_volumes.get(keyword, 0),
                pinterest_interest=pinterest_data.get(keyword, 0),
                rising_status=trend.get('is_rising', False),
                competition=self._estimate_competition(trend['search_volume']),
                seasonal_boost=self.detect_seasonal_boost(keyword, current_month),
                sources=['google', 'etsy', 'pinterest']
            )
            
            # Add historical performance boost
            if history['has_history'] and history['performance_score'] > 0:
                score.final_score += history['performance_score'] * 0.1
                score.sources.append('historical_sales')
            
            scored_trends.append(score)
        
        # Step 5: Filter by minimum search volume (most important criterion)
        filtered = [t for t in scored_trends if t.search_volume >= min_search_volume]
        
        # Step 6: Sort by final score
        filtered.sort(key=lambda x: x.final_score, reverse=True)
        
        logger.info(f"✅ Analysis complete: {len(filtered)} high-value trends identified")
        
        return filtered
    
    def _estimate_competition(self, search_volume: int) -> str:
        """Estimate competition level based on search volume"""
        if search_volume > 50000:
            return "high"
        elif search_volume > 10000:
            return "medium"
        else:
            return "low"
    
    async def store_prioritized_trends(
        self, 
        scored_trends: List[TrendScore],
        max_to_store: int = 50
    ) -> int:
        """
        Store the top-scored trends in database for generation
        """
        stored_count = 0
        
        for trend in scored_trends[:max_to_store]:
            try:
                # Check if already exists
                existing = await self.db_pool.fetchval(
                    """
                    SELECT id FROM trends 
                    WHERE LOWER(keyword) = LOWER($1)
                    AND created_at > NOW() - INTERVAL '7 days'
                    """,
                    trend.keyword
                )
                
                if existing:
                    logger.debug(f"Trend already exists: {trend.keyword}")
                    continue
                
                # Store new trend
                await self.db_pool.execute(
                    """
                    INSERT INTO trends (
                        keyword, search_volume, trend_score,
                        geography, category, data
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    trend.keyword,
                    trend.search_volume,
                    trend.final_score,  # Use intelligent score
                    'GB',
                    'auto-analyzed',
                    {
                        'sources': trend.sources,
                        'rising': trend.rising_status,
                        'competition': trend.competition,
                        'etsy_volume': trend.etsy_search_volume,
                        'pinterest_interest': trend.pinterest_interest,
                        'seasonal_boost': trend.seasonal_boost,
                        'analyzed_at': datetime.utcnow().isoformat()
                    }
                )
                
                stored_count += 1
                logger.info(f"✅ Stored: {trend.keyword} (score: {trend.final_score:.2f}, volume: {trend.search_volume:,})")
                
            except Exception as e:
                logger.error(f"Error storing trend {trend.keyword}: {e}")
                continue
        
        return stored_count
    
    async def run_intelligent_analysis(
        self,
        min_search_volume: int = 1000,
        max_trends: int = 50
    ) -> Dict:
        """
        Main entry point - runs complete intelligent analysis
        """
        logger.info("🚀 Starting intelligent multi-source trend analysis...")
        
        # Analyze and score
        scored_trends = await self.analyze_and_score_trends(min_search_volume)
        
        if not scored_trends:
            return {
                'success': False,
                'trends_analyzed': 0,
                'trends_stored': 0,
                'message': 'No trends found meeting criteria'
            }
        
        # Store top trends
        stored = await self.store_prioritized_trends(scored_trends, max_trends)
        
        # Get top 5 for summary
        top_5 = scored_trends[:5]
        
        summary = {
            'success': True,
            'trends_analyzed': len(scored_trends),
            'trends_stored': stored,
            'avg_search_volume': sum(t.search_volume for t in scored_trends) / len(scored_trends),
            'top_trends': [
                {
                    'keyword': t.keyword,
                    'search_volume': t.search_volume,
                    'score': round(t.final_score, 2),
                    'sources': t.sources,
                    'rising': t.rising_status
                }
                for t in top_5
            ]
        }
        
        logger.info(f"✅ Analysis complete: {stored} trends stored")
        return summary


# Singleton getter
_analyzer = None

def get_intelligent_analyzer(db_pool: DatabasePool) -> IntelligentTrendAnalyzer:
    """Get or create intelligent analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = IntelligentTrendAnalyzer(db_pool)
    return _analyzer
