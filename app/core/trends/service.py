from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger

from app.database import DatabasePool
from app.core.trends.google_trends import get_trends_analyzer


class TrendService:
    """Service for managing trend research and storage"""
    
    def __init__(self, db_pool: DatabasePool):
        self.db_pool = db_pool
        self.trends_analyzer = get_trends_analyzer()
    
    async def fetch_and_store_trends(
        self,
        region: str = 'GB',
        min_score: float = 6.0
    ) -> List[Dict]:
        """
        Fetch trends from Google and store in database
        
        Args:
            region: Country code
            min_score: Minimum trend score to store
            
        Returns:
            List of stored trends
        """
        logger.info(f"Fetching trends for region: {region}")
        
        # Get trending topics
        trending_topics = await self.trends_analyzer.get_trending_topics_for_pod(
            min_score=min_score
        )
        
        if not trending_topics:
            logger.warning("No trends fetched")
            return []
        
        # Store in database
        stored_trends = []
        for topic in trending_topics:
            try:
                # Check if trend already exists (in last 24 hours)
                existing = await self.db_pool.fetchval(
                    """
                    SELECT id FROM trends 
                    WHERE keyword = $1 
                    AND created_at > NOW() - INTERVAL '24 hours'
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
                    topic['search_volume'],
                    topic['trend_score'],
                    topic['geography'],
                    topic['category'],
                    {
                        'is_rising': topic['is_rising'],
                        'current_interest': topic['current_interest'],
                        'fetched_at': topic['fetched_at'].isoformat()
                    }
                )
                
                stored_trends.append({
                    'id': trend_id,
                    **topic
                })
                
                logger.info(f"Stored trend: {topic['keyword']} (score: {topic['trend_score']})")
                
            except Exception as e:
                logger.error(f"Error storing trend '{topic['keyword']}': {e}")
                continue
        
        logger.info(f"Stored {len(stored_trends)} new trends")
        return stored_trends
    
    async def get_top_trends(
        self,
        limit: int = 20,
        min_score: float = 0.0,
        category: Optional[str] = None
    ) -> List[Dict]:
        """
        Get top trends from database
        
        Args:
            limit: Maximum number of trends
            min_score: Minimum trend score
            category: Optional category filter
            
        Returns:
            List of trends
        """
        try:
            if category:
                query = """
                    SELECT id, keyword, search_volume, trend_score, 
                           geography, category, created_at, data
                    FROM trends
                    WHERE trend_score >= $1 
                    AND category = $2
                    ORDER BY trend_score DESC, created_at DESC
                    LIMIT $3
                """
                results = await self.db_pool.fetch(query, min_score, category, limit)
            else:
                query = """
                    SELECT id, keyword, search_volume, trend_score, 
                           geography, category, created_at, data
                    FROM trends
                    WHERE trend_score >= $1
                    ORDER BY trend_score DESC, created_at DESC
                    LIMIT $2
                """
                results = await self.db_pool.fetch(query, min_score, limit)
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error fetching top trends: {e}")
            return []
    
    async def get_trends_without_products(self, limit: int = 10) -> List[Dict]:
        """
        Get trends that don't have products yet
        
        Args:
            limit: Maximum number of trends
            
        Returns:
            List of trends without products
        """
        try:
            query = """
                SELECT t.id, t.keyword, t.search_volume, t.trend_score,
                       t.geography, t.category, t.created_at
                FROM trends t
                LEFT JOIN artwork a ON a.trend_id = t.id
                WHERE a.id IS NULL
                AND t.trend_score >= 6.0
                ORDER BY t.trend_score DESC, t.created_at DESC
                LIMIT $1
            """
            results = await self.db_pool.fetch(query, limit)
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error fetching trends without products: {e}")
            return []
