import hashlib
import uuid
from datetime import datetime
from typing import Optional
import re

def generate_sku(prefix: str = "POD") -> str:
    """Generate unique SKU"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"{prefix}-{timestamp}-{unique_id}"

def slugify(text: str) -> str:
    """Convert text to URL-friendly slug"""
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def calculate_price_with_margin(cost: float, margin: float) -> float:
    """Calculate selling price based on cost and margin"""
    return round(cost * (1 + margin), 2)

def hash_api_key(api_key: str) -> str:
    """Hash API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()
