from typing import Dict

STYLE_PROMPTS = {
    'minimalist': {
        'template': 'Minimalist {keyword}, clean lines, simple shapes, limited color palette, modern design, professional, high quality',
        'negative': 'cluttered, busy, detailed, ornate, complex, photographic'
    },
    
    'abstract': {
        'template': 'Abstract art inspired by {keyword}, geometric shapes, bold colors, contemporary style, dynamic composition, professional gallery quality',
        'negative': 'realistic, photographic, representational'
    },
    
    'vintage': {
        'template': 'Vintage {keyword}, retro style, aged paper texture, muted colors, classic design, nostalgic aesthetic, high quality print',
        'negative': 'modern, digital, bright, contemporary'
    },
    
    'watercolor': {
        'template': 'Beautiful watercolor painting of {keyword}, soft edges, flowing colors, artistic, delicate, hand-painted aesthetic, professional',
        'negative': 'digital, photograph, sharp edges, bold'
    },
    
    'line_art': {
        'template': 'Elegant line art illustration of {keyword}, continuous line drawing, minimalist, sophisticated, clean, professional quality',
        'negative': 'colored, filled, shaded, photographic'
    },
    
    'photography': {
        'template': 'Professional photograph of {keyword}, high quality, sharp focus, beautiful lighting, stunning composition, award-winning photography',
        'negative': 'illustration, drawing, painting, artificial'
    },
    
    'typography': {
        'template': 'Beautiful typography poster with text "{keyword}", modern elegant font, inspiring design, clean layout, professional, high contrast',
        'negative': 'image, illustration, photo, cluttered'
    },
    
    'botanical': {
        'template': 'Detailed botanical illustration of {keyword}, scientific naturalist style, vintage aesthetic, professional quality, cream background',
        'negative': 'cartoon, modern, abstract, photographic'
    }
}


def get_prompt_for_style(keyword: str, style: str) -> Dict:
    """
    Generate optimized prompt for a keyword and style
    
    Args:
        keyword: Main subject/trend
        style: Art style name
        
    Returns:
        Dict with prompt and negative_prompt
    """
    config = STYLE_PROMPTS.get(style, STYLE_PROMPTS['abstract'])
    
    return {
        'prompt': config['template'].format(keyword=keyword),
        'negative_prompt': config.get('negative', '')
    }


# Premium pricing based on artwork complexity
STYLE_PRICING = {
    'minimalist': {'base_price': 39.99, 'margin': 0.70},  # 70% profit
    'abstract': {'base_price': 44.99, 'margin': 0.70},
    'vintage': {'base_price': 42.99, 'margin': 0.70},
    'watercolor': {'base_price': 47.99, 'margin': 0.72},
    'line_art': {'base_price': 39.99, 'margin': 0.70},
    'photography': {'base_price': 54.99, 'margin': 0.75},
    'typography': {'base_price': 34.99, 'margin': 0.68},
    'botanical': {'base_price': 49.99, 'margin': 0.72}
}


def get_pricing_for_style(style: str) -> Dict:
    """Get recommended pricing for a style"""
    return STYLE_PRICING.get(style, {'base_price': 44.99, 'margin': 0.70})
