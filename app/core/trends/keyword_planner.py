"""
Google Keyword Planner Integration
Provides actual search volume data from Google Ads API
"""
from typing import List, Dict, Optional
from loguru import logger
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    from google.ads.googleads.client import GoogleAdsClient
    from google.ads.googleads.errors import GoogleAdsException
    GOOGLE_ADS_AVAILABLE = True
except ImportError:
    GOOGLE_ADS_AVAILABLE = False
    logger.warning("google-ads library not installed. Keyword Planner features disabled.")

from app.core.trends.google_ads_config import get_google_ads_config, validate_customer_id


class KeywordPlannerAnalyzer:
    """
    Google Keyword Planner integration for search volume data
    
    Requires:
    1. Google Ads account (can have $0 spend)
    2. Google Ads API credentials
    3. Developer token
    """
    
    def __init__(self, customer_id: Optional[str] = None):
        """
        Initialize the analyzer
        
        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
        """
        if not GOOGLE_ADS_AVAILABLE:
            logger.error("Google Ads library not available. Install with: pip install google-ads")
            self.client = None
            return
        
        config = get_google_ads_config()
        if not config:
            logger.error("Google Ads API not configured")
            self.client = None
            return
        
        # Add customer ID if provided
        if customer_id:
            customer_id = validate_customer_id(customer_id)
            if customer_id:
                config['login_customer_id'] = customer_id
        
        try:
            self.client = GoogleAdsClient.load_from_dict(config)
            self.customer_id = customer_id or config.get('login_customer_id')
            
            if self.customer_id:
                self.customer_id = validate_customer_id(self.customer_id)
            
            logger.info(f"✅ Google Keyword Planner initialized (Customer ID: {self.customer_id})")
        except Exception as e:
            logger.error(f"Failed to initialize Google Ads client: {e}")
            self.client = None
    
    def _get_keyword_ideas_sync(
        self,
        keywords: List[str],
        country_code: str = "GB",
        language_code: str = "en"
    ) -> List[Dict]:
        """
        Synchronous method to get keyword ideas
        Runs in thread pool executor for async compatibility
        """
        if not self.client or not self.customer_id:
            logger.error("Google Ads client not initialized")
            return []
        
        try:
            keyword_plan_idea_service = self.client.get_service("KeywordPlanIdeaService")
            
            # Map country codes to geo target constants
            geo_target_constants = {
                "GB": "geoTargetConstants/2826",  # United Kingdom
                "US": "geoTargetConstants/2840",  # United States
                "CA": "geoTargetConstants/2124",  # Canada
                "AU": "geoTargetConstants/2036",  # Australia
            }
            
            geo_target = geo_target_constants.get(country_code, "geoTargetConstants/2826")
            
            # Build request
            request = self.client.get_type("GenerateKeywordIdeasRequest")
            request.customer_id = self.customer_id
            
            # Set language (English)
            request.language = self.client.get_service("GoogleAdsService").language_constant_path("1000")
            
            # Set geo target
            request.geo_target_constants.append(geo_target)
            
            # Set keywords
            request.keyword_seed.keywords.extend(keywords)
            
            # Include adult keywords (for comprehensive data)
            request.include_adult_keywords = False
            
            # Get keyword ideas
            response = keyword_plan_idea_service.generate_keyword_ideas(request=request)
            
            results = []
            for idea in response.results:
                # Extract metrics
                metrics = idea.keyword_idea_metrics
                
                # Competition level mapping
                competition_map = {
                    0: "UNSPECIFIED",
                    1: "UNKNOWN", 
                    2: "LOW",
                    3: "MEDIUM",
                    4: "HIGH"
                }
                
                competition = competition_map.get(
                    metrics.competition.value if hasattr(metrics.competition, 'value') else metrics.competition,
                    "UNKNOWN"
                )
                
                results.append({
                    'keyword': idea.text,
                    'avg_monthly_searches': metrics.avg_monthly_searches or 0,
                    'competition': competition,
                    'competition_index': metrics.competition_index or 0,  # 0-100 scale
                    'low_top_of_page_bid_micros': metrics.low_top_of_page_bid_micros or 0,
                    'high_top_of_page_bid_micros': metrics.high_top_of_page_bid_micros or 0,
                })
            
            logger.info(f"✅ Retrieved {len(results)} keyword ideas from Google Keyword Planner")
            return results
            
        except GoogleAdsException as ex:
            logger.error(f"Google Ads API error: {ex}")
            for error in ex.failure.errors:
                logger.error(f"  Error: {error.message}")
            return []
        except Exception as e:
            logger.error(f"Error getting keyword ideas: {e}")
            logger.exception("Full traceback:")
            return []
    
    async def get_keyword_volume(
        self,
        keywords: List[str],
        country_code: str = "GB",
        language_code: str = "en"
    ) -> List[Dict]:
        """
        Get search volume data for keywords (async wrapper)
        
        Args:
            keywords: List of keywords to analyze
            country_code: Country code (GB, US, CA, AU)
            language_code: Language code (en)
            
        Returns:
            List of dicts with keyword data:
            {
                'keyword': str,
                'avg_monthly_searches': int,
                'competition': str,  # LOW, MEDIUM, HIGH
                'competition_index': int,  # 0-100
                'low_top_of_page_bid_micros': int,
                'high_top_of_page_bid_micros': int
            }
        """
        if not self.client:
            logger.warning("Google Keyword Planner not available")
            return []
        
        # Run sync method in thread pool
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            results = await loop.run_in_executor(
                executor,
                self._get_keyword_ideas_sync,
                keywords,
                country_code,
                language_code
            )
        
        return results
    
    async def analyze_trend_keywords(
        self,
        keywords: List[str],
        country_code: str = "GB"
    ) -> Dict:
        """
        Analyze multiple keywords and provide summary
        
        Returns:
            {
                'keywords': [...],  # Full data
                'total_volume': int,
                'avg_competition': str,
                'high_volume_keywords': [...],  # >10k monthly searches
                'low_competition_keywords': [...]  # LOW competition
            }
        """
        results = await self.get_keyword_volume(keywords, country_code)
        
        if not results:
            return {
                'keywords': [],
                'total_volume': 0,
                'avg_competition': 'UNKNOWN',
                'high_volume_keywords': [],
                'low_competition_keywords': []
            }
        
        total_volume = sum(k['avg_monthly_searches'] for k in results)
        
        # High volume keywords (>10k monthly searches)
        high_volume = [
            k for k in results 
            if k['avg_monthly_searches'] >= 10000
        ]
        
        # Low competition keywords
        low_competition = [
            k for k in results
            if k['competition'] == 'LOW'
        ]
        
        # Average competition
        competition_counts = {}
        for k in results:
            comp = k['competition']
            competition_counts[comp] = competition_counts.get(comp, 0) + 1
        
        avg_competition = max(competition_counts, key=competition_counts.get) if competition_counts else 'UNKNOWN'
        
        return {
            'keywords': results,
            'total_volume': total_volume,
            'avg_volume_per_keyword': total_volume // len(results) if results else 0,
            'avg_competition': avg_competition,
            'high_volume_keywords': high_volume,
            'low_competition_keywords': low_competition,
            'total_keywords_analyzed': len(results)
        }
    
    def is_available(self) -> bool:
        """Check if the service is available and configured"""
        return self.client is not None and self.customer_id is not None


# Singleton instance
_analyzer = None

def get_keyword_planner(customer_id: Optional[str] = None) -> KeywordPlannerAnalyzer:
    """Get or create keyword planner instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = KeywordPlannerAnalyzer(customer_id=customer_id)
    return _analyzer
