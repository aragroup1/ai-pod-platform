"""
Google Ads API Configuration
"""
import os
from loguru import logger

def get_google_ads_config():
    """
    Get Google Ads API configuration from environment variables
    
    Required environment variables:
    - GOOGLE_ADS_DEVELOPER_TOKEN
    - GOOGLE_ADS_CLIENT_ID
    - GOOGLE_ADS_CLIENT_SECRET
    - GOOGLE_ADS_REFRESH_TOKEN
    - GOOGLE_ADS_CUSTOMER_ID (optional, can be set per request)
    - GOOGLE_ADS_LOGIN_CUSTOMER_ID (optional)
    """
    config = {
        'developer_token': os.getenv('GOOGLE_ADS_DEVELOPER_TOKEN'),
        'client_id': os.getenv('GOOGLE_ADS_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_ADS_CLIENT_SECRET'),
        'refresh_token': os.getenv('GOOGLE_ADS_REFRESH_TOKEN'),
        'use_proto_plus': True,
        'login_customer_id': os.getenv('GOOGLE_ADS_LOGIN_CUSTOMER_ID'),
    }
    
    # Validate required fields
    required = ['developer_token', 'client_id', 'client_secret', 'refresh_token']
    missing = [key for key in required if not config.get(key)]
    
    if missing:
        logger.warning(f"Missing Google Ads config: {', '.join(missing)}")
        return None
    
    return config


def validate_customer_id(customer_id: str) -> str:
    """
    Validate and format customer ID
    Google Ads customer IDs should be 10 digits without hyphens
    """
    if not customer_id:
        return None
    
    # Remove hyphens
    customer_id = customer_id.replace('-', '')
    
    # Validate format
    if not customer_id.isdigit() or len(customer_id) != 10:
        logger.error(f"Invalid customer ID format: {customer_id}")
        return None
    
    return customer_id
