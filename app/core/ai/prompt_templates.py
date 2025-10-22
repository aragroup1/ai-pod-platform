from typing import Dict

STYLE_PROMPTS = {
    'minimalist': {
        'template': 'Minimalist {keyword}, clean lines, simple shapes, limited color palette, modern design, white background, professional',
        'negative': 'cluttered, busy, detailed, ornate, complex, photographic',
        'guidance': 7.5,
        'steps': 50
    },
    
    'abstract': {
        'template': 'Abstract art inspired by {keyword}, geometric shapes, bold colors, contemporary, dynamic composition, professional gallery quality',
        'negative': 'realistic, photographic, representational, figurative',
        'guidance': 8.0,
        'steps': 60
    },
    
    'vintage': {
        'template': 'Vintage {keyword}, retro style, aged paper texture, muted colors, classic design, nostalgic aesthetic, high quality print',
        'negative': 'modern, digital, bright, contemporary, clean',
        'guidance': 7.5,
        'steps': 50
    },
    
    'watercolor': {
        'template': 'Watercolor painting of {keyword}, soft edges, flowing colors, artistic, delicate, hand-painted look, white background',
        'negative': 'digital, photograph, sharp edges, bold, harsh',
        'guidance': 7.0,
        'steps': 50
    },
    
    'line_art': {
        'template': 'Elegant line art illustration of {keyword}, continuous line drawing, minimalist, black lines on white, simple and sophisticated',
        'negative': 'colored, filled, shaded, photographic, complex',
        'guidance': 8.0,
        'steps': 40
    },
    
    'photography': {
        'template': 'Professional photograph of {keyword}, high quality, sharp focus, beautiful lighting, stunning composition, award-winning',
        'negative': 'illustration, drawing, painting, artificial, low quality',
        'guidance': 7.0,
        'steps': 50
    },
    
    'typography': {
        'template': '"{keyword}" - Beautiful typography design, modern font, inspiring quote, elegant layout, professional, clean background',
        'negative': 'image, illustration, photo, cluttered, busy',
        'guidance': 8.5,
        'steps': 40
    },
    
    'botanical': {
        'template': 'Botanical illustration of {keyword}, scientific style, detailed plant drawing, vintage naturalist aesthetic, cream background',
        'negative': 'cartoon, modern, abstract, photographic, colorful',
        'guidance': 7.5,
        'steps': 50
    }
}


def get_prompt_for_style(keyword: str, style: str) -> Dict:
    """Generate prompt from template"""
    config = STYLE_PROMPTS.get(style, STYLE_PROMPTS['abstract'])
    
    return {
        'prompt': config['template'].format(keyword=keyword),
        'negative_prompt': config['negative'],
        'guidance_scale': config['guidance'],
        'num_inference_steps': config['steps']
    }
