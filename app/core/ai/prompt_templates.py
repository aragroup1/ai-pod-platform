# app/core/ai/prompt_templates.py
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
        # FIXED: More specific prompts for better text rendering
        'template': 'Typography poster design, text reads "{keyword}", modern elegant sans-serif font, minimalist layout, high contrast black and white, clean composition, professional graphic design, centered text, bold letters, readable, sharp, Helvetica style',
        'negative': 'images, photos, illustrations, decorative elements, ornate, script font, handwriting, cursive, messy, blurry text, unreadable'
    },
    
    'botanical': {
        'template': 'Detailed botanical illustration of {keyword}, scientific naturalist style, vintage aesthetic, professional quality, cream background',
        'negative': 'cartoon, modern, abstract, photographic'
    }
}

# Typography-specific phrases that work well
TYPOGRAPHY_PHRASES = {
    'motivational': [
        'Stay Strong',
        'Never Give Up',
        'You Got This',
        'Dream Big',
        'Be Kind',
        'Choose Joy',
        'Think Positive',
        'Stay Focused',
        'Keep Going',
        'Believe'
    ],
    'home': [
        'Home Sweet Home',
        'Gather',
        'Family First',
        'Love Lives Here',
        'Blessed',
        'Welcome',
        'Together',
        'Home',
        'Cozy Vibes',
        'Relax'
    ],
    'kitchen': [
        'Bon Appetit',
        'Eat Well',
        'Fresh Daily',
        'Gather Here',
        'Good Food Good Mood',
        'Kitchen',
        'Homemade',
        'Bless This Mess',
        'Coffee Time',
        'Sweet Life'
    ],
    'office': [
        'Focus',
        'Work Hard Dream Big',
        'Make It Happen',
        'Do Epic Things',
        'Hustle',
        'Goals',
        'Success',
        'Grind',
        'Execute',
        'Build'
    ],
    'bedroom': [
        'Sleep Tight',
        'Dream',
        'Rest',
        'Sweet Dreams',
        'Good Night',
        'Peaceful',
        'Relax',
        'Breathe',
        'Calm',
        'Serenity'
    ],
    'bathroom': [
        'Wash Your Hands',
        'Relax Renew Refresh',
        'Spa Vibes',
        'Clean',
        'Fresh',
        'Bubbles',
        'Pamper',
        'Unwind',
        'Soak',
        'Self Care'
    ],
    'gym': [
        'No Pain No Gain',
        'Train Insane',
        'Beast Mode',
        'Stronger',
        'Lift Heavy',
        'Fitness',
        'Power',
        'Sweat Now Shine Later',
        'Push Yourself',
        'Transform'
    ],
    'love': [
        'Love Wins',
        'All You Need Is Love',
        'Love Always',
        'Forever',
        'Together',
        'My Heart',
        'Soulmate',
        'True Love',
        'Always',
        'Romance'
    ]
}


def get_prompt_for_style(keyword: str, style: str) -> Dict:
    """
    Generate optimized prompt for a keyword and style
    
    IMPROVED: Better typography handling
    """
    config = STYLE_PROMPTS.get(style, STYLE_PROMPTS['abstract'])
    
    # Special handling for typography
    if style == 'typography':
        # Check if keyword matches a category
        for category, phrases in TYPOGRAPHY_PHRASES.items():
            if category in keyword.lower():
                # Use a proven phrase instead of keyword
                import random
                phrase = random.choice(phrases)
                return {
                    'prompt': config['template'].format(keyword=phrase),
                    'negative_prompt': config.get('negative', ''),
                    'actual_text': phrase
                }
        
        # For general typography, clean up the keyword
        clean_keyword = keyword.replace('quote', '').replace('poster', '').strip()
        # Limit to 3-4 words max for better rendering
        words = clean_keyword.split()[:4]
        short_phrase = ' '.join(words).title()
        
        return {
            'prompt': config['template'].format(keyword=short_phrase),
            'negative_prompt': config.get('negative', ''),
            'actual_text': short_phrase
        }
    
    return {
        'prompt': config['template'].format(keyword=keyword),
        'negative_prompt': config.get('negative', '')
    }


# Premium pricing based on artwork complexity
STYLE_PRICING = {
    'minimalist': {'base_price': 39.99, 'margin': 0.70},
    'abstract': {'base_price': 44.99, 'margin': 0.70},
    'vintage': {'base_price': 42.99, 'margin': 0.70},
    'watercolor': {'base_price': 47.99, 'margin': 0.72},
    'line_art': {'base_price': 39.99, 'margin': 0.70},
    'photography': {'base_price': 54.99, 'margin': 0.75},
    'typography': {'base_price': 29.99, 'margin': 0.68},  # Lower since faster/cheaper
    'botanical': {'base_price': 49.99, 'margin': 0.72}
}


def get_pricing_for_style(style: str) -> Dict:
    """Get recommended pricing for a style"""
    return STYLE_PRICING.get(style, {'base_price': 44.99, 'margin': 0.70})
