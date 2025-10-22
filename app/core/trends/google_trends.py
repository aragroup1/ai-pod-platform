from pytrends.request import TrendReq
from typing import List, Dict, Optional
import asyncio
from datetime import datetime, timedelta
from loguru import logger
import time

class GoogleTrendsAnalyzer:
    """
    Free Google Trends integration - no API key needed!
    Uses pytrends library to fetch trending topics and search volumes.
    """
    
    def __init__(self, region: str = 'GB', language: str = 'en-GB'):
        """
        Initialize Google Trends analyzer
        
        Args:
            region: Country code (GB, US, CA, AU, etc.)
            language: Language code (en-GB, en-US, etc.)
        """
        self.region = region
        self.language = language
        self.pytrends = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize or reinitialize the pytrends client"""
        try:
            self.pytrends = TrendReq(hl=self.language, tz=0, timeout=(10, 25))
            logger.info(f"Google Trends client initialized for region: {self.region}")
        except Exception as e:
            logger.error(f"Failed to initialize Google Trends client: {e}")
            self.pytrends = None
    
    async def get_trending_searches(self, limit: int = 20) -> List[str]:
        """
        Get daily trending searches (FREE)
        
        Args:
            limit: Maximum number of trends to return
            
        Returns:
            List of trending search terms
        """
        try:
            if not self.pytrends:
                self._initialize_client()
            
            # Run in thread pool since pytrends is synchronous
            loop = asyncio.get_event_loop()
            trending_df = await loop.run_in_executor(
                None, 
                self.pytrends.trending_searches, 
                self.region
            )
            
            trends = trending_df[0].tolist()[:limit]
            logger.info(f"Fetched {len(trends)} trending searches from Google Trends")
            return trends
            
        except Exception as e:
            logger.error(f"Error fetching trending searches: {e}")
            return []
    
    async def get_interest_over_time(
        self, 
        keywords: List[str], 
        timeframe: str = 'today 3-m'
    ) -> Dict[str, Dict]:
        """
        Get search volume trends for keywords (FREE)
        
        Args:
            keywords: List of keywords to analyze (max 5 at a time)
            timeframe: Time period ('today 3-m', 'today 12-m', etc.)
            
        Returns:
            Dictionary with keyword stats
        """
        if not keywords:
            return {}
        
        # Google Trends API limits to 5 keywords at a time
        keywords = keywords[:5]
        
        try:
            if not self.pytrends:
                self._initialize_client()
            
            loop = asyncio.get_event_loop()
            
            # Build payload
            await loop.run_in_executor(
                None,
                self.pytrends.build_payload,
                keywords,
                None,  # cat
                timeframe,
                self.region,
                None   # gprop
            )
            
            # Get interest over time
            interest_df = await loop.run_in_executor(
                None,
                self.pytrends.interest_over_time
            )
            
            if interest_df.empty:
                logger.warning(f"No interest data for keywords: {keywords}")
                return {}
            
            # Process results
            results = {}
            for keyword in keywords:
                if keyword in interest_df.columns:
                    series = interest_df[keyword]
                    results[keyword] = {
                        'avg_interest': int(series.mean()),
                        'max_interest': int(series.max()),
                        'current_interest': int(series.iloc[-1]),
                        'trend_score': self._calculate_trend_score(series),
                        'is_rising': series.iloc[-1] > series.mean()
                    }
            
            logger.info(f"Analyzed interest for {len(results)} keywords")
            return results
            
        except Exception as e:
            logger.error(f"Error getting interest over time: {e}")
            return {}
    
    def _calculate_trend_score(self, series) -> float:
        """
        Calculate if trend is rising (0-10 scale)
        
        Args:
            series: Pandas series of interest values
            
        Returns:
            Score from 0-10 (10 = strongly rising)
        """
        if len(series) < 2:
            return 5.0
        
        try:
            # Compare recent 30 days vs older data
            recent_avg = series[-30:].mean()
            older_avg = series[:-30].mean() if len(series) > 30 else series.mean()
            
            if older_avg == 0:
                return 7.0 if recent_avg > 0 else 5.0
            
            # Calculate growth percentage
            growth = ((recent_avg - older_avg) / older_avg) * 100
            
            # Scale to 0-10
            # 0% growth = 5, +100% growth = 10, -50% growth = 0
            score = 5 + (growth / 20)
            
            return max(0, min(10, score))
            
        except Exception as e:
            logger.error(f"Error calculating trend score: {e}")
            return 5.0
    
    async def get_related_queries(
        self, 
        keyword: str, 
        limit: int = 10
    ) -> List[str]:
        """
        Get related search queries (FREE)
        
        Args:
            keyword: Main keyword to find related queries for
            limit: Maximum number of related queries
            
        Returns:
            List of related search terms
        """
        try:
            if not self.pytrends:
                self._initialize_client()
            
            loop = asyncio.get_event_loop()
            
            # Build payload
            await loop.run_in_executor(
                None,
                self.pytrends.build_payload,
                [keyword],
                None,
                'today 3-m',
                self.region,
                None
            )
            
            # Get related queries
            related = await loop.run_in_executor(
                None,
                self.pytrends.related_queries
            )
            
            if keyword in related and related[keyword]['top'] is not None:
                queries = related[keyword]['top']['query'].tolist()[:limit]
                logger.info(f"Found {len(queries)} related queries for '{keyword}'")
                return queries
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting related queries for '{keyword}': {e}")
            return []
    
    async def analyze_keywords_batch(
        self, 
        keywords: List[str],
        batch_size: int = 5
    ) -> Dict[str, Dict]:
        """
        Analyze multiple keywords in batches (respects API limits)
        
        Args:
            keywords: List of keywords to analyze
            batch_size: Number of keywords per batch (max 5)
            
        Returns:
            Dictionary with all keyword analyses
        """
        results = {}
        
        for i in range(0, len(keywords), batch_size):
            batch = keywords[i:i + batch_size]
            batch_results = await self.get_interest_over_time(batch)
            results.update(batch_results)
            
            # Rate limiting - wait between batches
            if i + batch_size < len(keywords):
                await asyncio.sleep(2)  # 2 second delay between batches
        
        return results
    
    async def get_trending_topics_for_pod(
        self,
        categories: Optional[List[str]] = None,
        min_score: float = 6.0
    ) -> List[Dict]:
        """
        Get trending topics suitable for Print-on-Demand
        
        Args:
            categories: Optional list of categories to focus on
            min_score: Minimum trend score to include (0-10)
            
        Returns:
            List of trending topics with metadata
        """
        # Get daily trending searches
        trending = await self.get_trending_searches(limit=20)
        
        if not trending:
            logger.warning("No trending searches found")
            return []
        
        # Filter for POD-suitable keywords
        pod_suitable_keywords = []
        excluded_terms = [
            'news', 'death', 'died', 'killed', 'murder', 'scandal',
            'covid', 'virus', 'disease', 'election', 'politics',
            'stocks', 'crypto', 'bitcoin', 'nft'
        ]
        
        for keyword in trending:
            keyword_lower = keyword.lower()
            # Exclude controversial/unsuitable topics
            if not any(term in keyword_lower for term in excluded_terms):
                pod_suitable_keywords.append(keyword)
        
        if not pod_suitable_keywords:
            logger.info("No POD-suitable trending topics found")
            return []
        
        # Analyze interest for suitable keywords
        keyword_data = await self.analyze_keywords_batch(
            pod_suitable_keywords[:15],  # Limit to 15 keywords
            batch_size=5
        )
        
        # Format results
        trending_topics = []
        for keyword, data in keyword_data.items():
            if data['trend_score'] >= min_score:
                trending_topics.append({
                    'keyword': keyword,
                    'search_volume': data['avg_interest'],
                    'trend_score': data['trend_score'],
                    'is_rising': data['is_rising'],
                    'current_interest': data['current_interest'],
                    'geography': self.region,
                    'category': self._categorize_keyword(keyword),
                    'fetched_at': datetime.utcnow()
                })
        
        # Sort by trend score
        trending_topics.sort(key=lambda x: x['trend_score'], reverse=True)
        
        logger.info(f"Found {len(trending_topics)} POD-suitable trending topics")
        return trending_topics
    
    def _categorize_keyword(self, keyword: str) -> str:
        """
        Categorize keyword for POD purposes
        
        Args:
            keyword: Search keyword
            
        Returns:
            Category name
        """
        keyword_lower = keyword.lower()
        
        categories = {
            'nature': ['nature', 'landscape', 'mountain', 'ocean', 'forest', 'sunset', 'beach'],
            'animals': ['cat', 'dog', 'bird', 'animal', 'pet', 'wildlife'],
            'abstract': ['abstract', 'geometric', 'pattern', 'modern art'],
            'typography': ['quote', 'saying', 'text', 'words', 'motivation'],
            'vintage': ['vintage', 'retro', 'classic', 'antique', 'old'],
            'minimalist': ['minimalist', 'simple', 'clean', 'minimal'],
            'floral': ['flower', 'floral', 'botanical', 'plant', 'garden'],
            'urban': ['city', 'urban', 'street', 'architecture', 'building']
        }
        
        for category, keywords_list in categories.items():
            if any(term in keyword_lower for term in keywords_list):
                return category
        
        return 'general'


# Singleton instance
_trends_analyzer = None

def get_trends_analyzer(region: str = 'GB') -> GoogleTrendsAnalyzer:
    """Get or create Google Trends analyzer instance"""
    global _trends_analyzer
    if _trends_analyzer is None:
        _trends_analyzer = GoogleTrendsAnalyzer(region=region)
    return _trends_analyzer
