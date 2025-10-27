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
    logger.warning("google-ads library not installed. Run: pip install google-ads")

from app.core.trends.google_ads_config import get_google_ads_config, validate_customer_id


class KeywordPlannerAnalyzer:
    """
    Google Keyword Planner integration for search volume data
    
    Setup Instructions:
    1. Go to https://console.cloud.google.com
    2. Enable Google Ads API
    3. Create OAuth 2.0 credentials (Web application)
    4. Use OAuth Playground to get refresh token
    5. Add environment variables to Railway
    
    Required Environment Variables:
    - GOOGLE_ADS_DEVELOPER_TOKEN (you have: tbWEP6dGtUdVRGOBFl2Wzg)
    - GOOGLE_ADS_CLIENT_ID (from OAuth credentials)
    - GOOGLE_ADS_CLIENT_SECRET (from OAuth credentials)
    - GOOGLE_ADS_REFRESH_TOKEN (from OAuth Playground)
    - GOOGLE_ADS_CUSTOMER_ID (your ID: 9735349933)
    """
    
    def __init__(self, customer_id: Optional[str] = None):
        self.client = None
        self.customer_id = None
        self.setup_error = None
        
        if not GOOGLE_ADS_AVAILABLE:
            self.setup_error = "google-ads library not installed"
            logger.warning(self.setup_error)
            return
        
        config = get_google_ads_config()
        if not config:
            self.setup_error = "Google Ads API credentials not configured. See setup instructions."
            logger.warning(self.setup_error)
            return
        
        # Validate and set customer ID
        if customer_id:
            self.customer_id = validate_customer_id(customer_id)
        elif config.get('login_customer_id'):
            self.customer_id = validate_customer_id(config['login_customer_id'])
        
        if not self.customer_id:
            self.setup_error = "Customer ID not provided or invalid"
            logger.warning(self.setup_error)
            return
        
        try:
            self.client = GoogleAdsClient.load_from_dict(config)
            logger.info(f"✅ Google Keyword Planner initialized (Customer: {self.customer_id})")
        except Exception as e:
            self.setup_error = f"Failed to initialize: {str(e)}"
            logger.error(self.setup_error)
    
    def _get_keyword_ideas_sync(
        self,
        keywords: List[str],
        country_code: str = "GB",
        language_code: str = "en"
    ) -> List[Dict]:
        """Synchronous method to get keyword ideas"""
        if not self.client or not self.customer_id:
            logger.error(f"Cannot get keyword ideas: {self.setup_error}")
            return []
        
        try:
            keyword_plan_idea_service = self.client.get_service("KeywordPlanIdeaService")
            
            # Geo target constants
            geo_targets = {
                "GB": "geoTargetConstants/2826",
                "US": "geoTargetConstants/2840",
                "CA": "geoTargetConstants/2124",
                "AU": "geoTargetConstants/2036",
            }
            
            # Build request
            request = self.client.get_type("GenerateKeywordIdeasRequest")
            request.customer_id = self.customer_id
            
            # Language: English
            request.language = self.client.get_service("GoogleAdsService").language_constant_path("1000")
            
            # Geo target
            geo_target = geo_targets.get(country_code, geo_targets["GB"])
            request.geo_target_constants.append(geo_target)
            
            # Keywords
            request.keyword_seed.keywords.extend(keywords)
            request.include_adult_keywords = False
            
            # Get ideas
            response = keyword_plan_idea_service.generate_keyword_ideas(request=request)
            
            results = []
            for idea in response.results:
                metrics = idea.keyword_idea_metrics
                
                # Competition mapping
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
                
                # Convert micros to currency (1 million micros = 1 unit)
                low_bid = (metrics.low_top_of_page_bid_micros or 0) / 1_000_000
                high_bid = (metrics.high_top_of_page_bid_micros or 0) / 1_000_000
                
                results.append({
                    'keyword': idea.text,
                    'avg_monthly_searches': metrics.avg_monthly_searches or 0,
                    'competition': competition,
                    'competition_index': metrics.competition_index or 0,
                    'low_top_of_page_bid': round(low_bid, 2),
                    'high_top_of_page_bid': round(high_bid, 2),
                })
            
            logger.info(f"✅ Retrieved {len(results)} keyword ideas")
            return results
            
        except GoogleAdsException as ex:
            logger.error("Google Ads API error:")
            for error in ex.failure.errors:
                logger.error(f"  - {error.message}")
            return []
        except Exception as e:
            logger.error(f"Error getting keyword ideas: {e}")
            return []
    
    async def get_keyword_volume(
        self,
        keywords: List[str],
        country_code: str = "GB",
        language_code: str = "en"
    ) -> List[Dict]:
        """Get search volume data for keywords (async)"""
        if not self.client:
            logger.warning(f"Keyword Planner unavailable: {self.setup_error}")
            return []
        
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
        """Analyze multiple keywords with summary"""
        results = await self.get_keyword_volume(keywords, country_code)
        
        if not results:
            return {
                'keywords': [],
                'total_volume': 0,
                'avg_competition': 'UNKNOWN',
                'high_volume_keywords': [],
                'low_competition_keywords': [],
                'error': self.setup_error
            }
        
        total_volume = sum(k['avg_monthly_searches'] for k in results)
        
        high_volume = [k for k in results if k['avg_monthly_searches'] >= 10000]
        low_competition = [k for k in results if k['competition'] == 'LOW']
        
        # Most common competition level
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
        """Check if service is ready"""
        return self.client is not None and self.customer_id is not None
    
    def get_setup_status(self) -> Dict:
        """Get detailed setup status for debugging"""
        import os
        
        return {
            'library_installed': GOOGLE_ADS_AVAILABLE,
            'developer_token_set': bool(os.getenv('GOOGLE_ADS_DEVELOPER_TOKEN')),
            'client_id_set': bool(os.getenv('GOOGLE_ADS_CLIENT_ID')),
            'client_secret_set': bool(os.getenv('GOOGLE_ADS_CLIENT_SECRET')),
            'refresh_token_set': bool(os.getenv('GOOGLE_ADS_REFRESH_TOKEN')),
            'customer_id_set': bool(self.customer_id),
            'client_initialized': bool(self.client),
            'ready': self.is_available(),
            'error': self.setup_error,
            'setup_instructions': 'See scripts/setup_google_ads.md for setup guide'
        }


# Singleton
_analyzer = None

def get_keyword_planner(customer_id: Optional[str] = None) -> KeywordPlannerAnalyzer:
    """Get or create keyword planner instance"""
    global _analyzer
    if _analyzer is None:
        # Use customer ID from environment or provided
        import os
        cid = customer_id or os.getenv('GOOGLE_ADS_CUSTOMER_ID')
        _analyzer = KeywordPlannerAnalyzer(customer_id=cid)
    return _analyzer
