"""
Product Variation System
Generates multiple size and format variations including popular 3-panel canvas splits

Product Formats:
1. Single Canvas (vertical, horizontal, square)
2. 3-Panel Split (triptych) - VERY POPULAR
3. 2-Panel Split (diptych)
4. Poster sizes (various)
"""

from typing import List, Dict, Literal
from dataclasses import dataclass
from loguru import logger


ProductFormat = Literal[
    'single_vertical', 'single_horizontal', 'single_square',
    'triptych', 'diptych',
    'poster_small', 'poster_large'
]


@dataclass
class ProductVariation:
    """Defines a product variation with size and format"""
    format: ProductFormat
    width: int  # inches
    height: int  # inches
    panel_count: int
    display_name: str
    description: str
    base_price_multiplier: float  # Multiply base price by this
    popularity_score: int  # 1-10, for sorting
    aspect_ratio: str  # e.g., "16:9", "1:1", "split-3"
    
    # For multi-panel products
    panel_arrangement: str = "horizontal"  # horizontal, vertical
    panel_spacing: int = 2  # inches between panels


# POPULAR SIZE DEFINITIONS
PRODUCT_VARIATIONS = {
    # ==========================================
    # SINGLE CANVAS - VERTICAL (Portrait)
    # ==========================================
    'single_vertical_small': ProductVariation(
        format='single_vertical',
        width=16,
        height=20,
        panel_count=1,
        display_name="16x20\" Vertical Canvas",
        description="Classic vertical portrait canvas",
        base_price_multiplier=1.0,
        popularity_score=8,
        aspect_ratio="4:5"
    ),
    
    'single_vertical_medium': ProductVariation(
        format='single_vertical',
        width=18,
        height=24,
        panel_count=1,
        display_name="18x24\" Vertical Canvas",
        description="Popular vertical canvas size",
        base_price_multiplier=1.2,
        popularity_score=9,
        aspect_ratio="3:4"
    ),
    
    'single_vertical_large': ProductVariation(
        format='single_vertical',
        width=24,
        height=36,
        panel_count=1,
        display_name="24x36\" Vertical Canvas",
        description="Large statement piece",
        base_price_multiplier=1.8,
        popularity_score=7,
        aspect_ratio="2:3"
    ),
    
    # ==========================================
    # SINGLE CANVAS - HORIZONTAL (Landscape)
    # ==========================================
    'single_horizontal_small': ProductVariation(
        format='single_horizontal',
        width=20,
        height=16,
        panel_count=1,
        display_name="20x16\" Horizontal Canvas",
        description="Wide landscape canvas",
        base_price_multiplier=1.0,
        popularity_score=8,
        aspect_ratio="5:4"
    ),
    
    'single_horizontal_medium': ProductVariation(
        format='single_horizontal',
        width=24,
        height=18,
        panel_count=1,
        display_name="24x18\" Horizontal Canvas",
        description="Popular landscape size",
        base_price_multiplier=1.2,
        popularity_score=9,
        aspect_ratio="4:3"
    ),
    
    'single_horizontal_large': ProductVariation(
        format='single_horizontal',
        width=36,
        height=24,
        panel_count=1,
        display_name="36x24\" Horizontal Canvas",
        description="Extra wide panoramic",
        base_price_multiplier=1.8,
        popularity_score=7,
        aspect_ratio="3:2"
    ),
    
    # ==========================================
    # SINGLE CANVAS - SQUARE
    # ==========================================
    'single_square_small': ProductVariation(
        format='single_square',
        width=12,
        height=12,
        panel_count=1,
        display_name="12x12\" Square Canvas",
        description="Compact square design",
        base_price_multiplier=0.8,
        popularity_score=7,
        aspect_ratio="1:1"
    ),
    
    'single_square_medium': ProductVariation(
        format='single_square',
        width=20,
        height=20,
        panel_count=1,
        display_name="20x20\" Square Canvas",
        description="Classic square format",
        base_price_multiplier=1.1,
        popularity_score=8,
        aspect_ratio="1:1"
    ),
    
    'single_square_large': ProductVariation(
        format='single_square',
        width=30,
        height=30,
        panel_count=1,
        display_name="30x30\" Square Canvas",
        description="Large square statement",
        base_price_multiplier=1.6,
        popularity_score=6,
        aspect_ratio="1:1"
    ),
    
    # ==========================================
    # 3-PANEL SPLIT (TRIPTYCH) - MOST POPULAR!
    # ==========================================
    'triptych_horizontal_small': ProductVariation(
        format='triptych',
        width=12,  # per panel
        height=16,
        panel_count=3,
        display_name="3-Panel Canvas Set (12x16\" each)",
        description="Popular 3-panel horizontal split canvas - total width 40\"",
        base_price_multiplier=2.5,  # 3 canvases + premium
        popularity_score=10,  # HIGHEST POPULARITY
        aspect_ratio="split-3",
        panel_arrangement="horizontal",
        panel_spacing=2
    ),
    
    'triptych_horizontal_medium': ProductVariation(
        format='triptych',
        width=16,  # per panel
        height=20,
        panel_count=3,
        display_name="3-Panel Canvas Set (16x20\" each)",
        description="Large 3-panel horizontal split canvas - total width 52\"",
        base_price_multiplier=3.2,
        popularity_score=10,  # HIGHEST POPULARITY
        aspect_ratio="split-3",
        panel_arrangement="horizontal",
        panel_spacing=2
    ),
    
    'triptych_horizontal_large': ProductVariation(
        format='triptych',
        width=20,  # per panel
        height=30,
        panel_count=3,
        display_name="3-Panel Canvas Set (20x30\" each)",
        description="Extra large 3-panel canvas - total width 64\"",
        base_price_multiplier=4.5,
        popularity_score=9,
        aspect_ratio="split-3",
        panel_arrangement="horizontal",
        panel_spacing=2
    ),
    
    'triptych_vertical': ProductVariation(
        format='triptych',
        width=16,
        height=20,
        panel_count=3,
        display_name="3-Panel Vertical Canvas Set (16x20\" each)",
        description="Vertical 3-panel arrangement - total height 64\"",
        base_price_multiplier=3.0,
        popularity_score=8,
        aspect_ratio="split-3",
        panel_arrangement="vertical",
        panel_spacing=2
    ),
    
    # ==========================================
    # 2-PANEL SPLIT (DIPTYCH)
    # ==========================================
    'diptych_horizontal': ProductVariation(
        format='diptych',
        width=20,  # per panel
        height=24,
        panel_count=2,
        display_name="2-Panel Canvas Set (20x24\" each)",
        description="Modern 2-panel split canvas - total width 42\"",
        base_price_multiplier=2.0,
        popularity_score=8,
        aspect_ratio="split-2",
        panel_arrangement="horizontal",
        panel_spacing=2
    ),
    
    'diptych_vertical': ProductVariation(
        format='diptych',
        width=16,
        height=20,
        panel_count=2,
        display_name="2-Panel Vertical Canvas Set (16x20\" each)",
        description="Vertical 2-panel arrangement",
        base_price_multiplier=1.8,
        popularity_score=7,
        aspect_ratio="split-2",
        panel_arrangement="vertical",
        panel_spacing=2
    ),
    
    # ==========================================
    # POSTERS (Cheaper alternative)
    # ==========================================
    'poster_small': ProductVariation(
        format='poster_small',
        width=12,
        height=18,
        panel_count=1,
        display_name="12x18\" Art Poster",
        description="Budget-friendly poster print",
        base_price_multiplier=0.4,
        popularity_score=6,
        aspect_ratio="2:3"
    ),
    
    'poster_large': ProductVariation(
        format='poster_large',
        width=24,
        height=36,
        panel_count=1,
        display_name="24x36\" Large Poster",
        description="Large format poster",
        base_price_multiplier=0.6,
        popularity_score=7,
        aspect_ratio="2:3"
    ),
}


class ProductVariationGenerator:
    """
    Generates product variations based on popularity and size preferences
    """
    
    def get_top_variations(self, count: int = 5) -> List[ProductVariation]:
        """
        Get most popular variations
        Prioritizes 3-panel splits and popular single canvases
        """
        all_variations = list(PRODUCT_VARIATIONS.values())
        all_variations.sort(key=lambda x: x.popularity_score, reverse=True)
        return all_variations[:count]
    
    def get_variations_by_format(self, format: ProductFormat) -> List[ProductVariation]:
        """Get all variations of a specific format"""
        return [
            v for v in PRODUCT_VARIATIONS.values()
            if v.format == format
        ]
    
    def get_triptych_variations(self) -> List[ProductVariation]:
        """Get all 3-panel split variations (most popular)"""
        return self.get_variations_by_format('triptych')
    
    def calculate_price(self, base_price: float, variation: ProductVariation) -> float:
        """Calculate final price for a variation"""
        return round(base_price * variation.base_price_multiplier, 2)
    
    def generate_product_title(
        self,
        keyword: str,
        style: str,
        variation: ProductVariation
    ) -> str:
        """Generate SEO-friendly product title"""
        
        # Style names
        style_names = {
            'minimalist': 'Minimalist',
            'abstract': 'Abstract',
            'vintage': 'Vintage',
            'watercolor': 'Watercolor',
            'line_art': 'Line Art',
            'photography': 'Photographic',
            'typography': 'Typography',
            'botanical': 'Botanical'
        }
        
        style_name = style_names.get(style, style.title())
        keyword_title = keyword.title()
        
        if variation.panel_count > 1:
            return f"{keyword_title} {style_name} {variation.panel_count}-Panel Canvas Wall Art"
        else:
            return f"{keyword_title} {style_name} Canvas Wall Art - {variation.display_name}"
    
    def generate_product_description(
        self,
        keyword: str,
        style: str,
        variation: ProductVariation
    ) -> str:
        """Generate detailed product description"""
        
        base_desc = f"Premium {style.replace('_', ' ')} artwork featuring {keyword}. "
        
        if variation.panel_count > 1:
            desc = (
                f"{base_desc}"
                f"This stunning {variation.panel_count}-panel canvas set creates a "
                f"dramatic focal point in any room. Each panel measures {variation.width}x{variation.height}\", "
                f"with {variation.panel_spacing}\" spacing for optimal visual impact. "
                f"Perfect for living rooms, bedrooms, or offices. "
            )
        else:
            desc = (
                f"{base_desc}"
                f"High-quality {variation.width}x{variation.height}\" canvas print "
                f"perfect for home or office decor. "
            )
        
        desc += (
            f"Printed on premium canvas with vibrant colors and sharp detail. "
            f"Ready to hang with included hardware. "
            f"Gallery-wrapped edges for a professional finish."
        )
        
        return desc
    
    def get_recommended_variations_for_trend(
        self,
        keyword: str,
        style: str,
        include_triptych: bool = True,
        include_single: bool = True,
        include_poster: bool = False
    ) -> List[ProductVariation]:
        """
        Get recommended variations for a specific trend
        
        Default: Focus on most popular (triptych + best single canvas)
        """
        variations = []
        
        if include_triptych:
            # Always include most popular 3-panel
            variations.append(PRODUCT_VARIATIONS['triptych_horizontal_medium'])
        
        if include_single:
            # Add most popular single canvas based on style
            if style in ['photography', 'vintage']:
                # Landscape works better for these
                variations.append(PRODUCT_VARIATIONS['single_horizontal_medium'])
            else:
                # Vertical for most other styles
                variations.append(PRODUCT_VARIATIONS['single_vertical_medium'])
        
        if include_poster:
            # Add budget option
            variations.append(PRODUCT_VARIATIONS['poster_large'])
        
        return variations


# Singleton
_variation_generator = None

def get_variation_generator() -> ProductVariationGenerator:
    """Get variation generator instance"""
    global _variation_generator
    if _variation_generator is None:
        _variation_generator = ProductVariationGenerator()
    return _variation_generator
