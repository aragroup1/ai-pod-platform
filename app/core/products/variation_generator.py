# app/core/products/variation_generator.py
"""
Product Variation Generator with Multi-Panel Support
Generates single canvas, 2-panel, and 3-panel split variations
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class ProductVariation:
    """Product variation configuration"""
    id: str
    name: str
    format_type: str  # 'single', 'diptych', 'triptych'
    orientation: str  # 'horizontal', 'vertical', 'square'
    width: int  # inches per panel
    height: int  # inches per panel
    panel_count: int
    panel_spacing: int  # inches between panels
    price_multiplier: float
    popularity_score: int  # 1-10
    total_width: int  # calculated total width
    total_height: int  # calculated total height
    
    def __post_init__(self):
        """Calculate total dimensions"""
        if self.orientation == 'horizontal' and self.panel_count > 1:
            self.total_width = (self.width * self.panel_count) + (self.panel_spacing * (self.panel_count - 1))
            self.total_height = self.height
        elif self.orientation == 'vertical' and self.panel_count > 1:
            self.total_width = self.width
            self.total_height = (self.height * self.panel_count) + (self.panel_spacing * (self.panel_count - 1))
        else:
            self.total_width = self.width
            self.total_height = self.height


# Comprehensive variation catalog
VARIATIONS = [
    # ========================================
    # SINGLE CANVAS - VERTICAL
    # ========================================
    ProductVariation(
        id='single_v_16x20',
        name='16x20" Vertical Canvas',
        format_type='single',
        orientation='vertical',
        width=16, height=20,
        panel_count=1, panel_spacing=0,
        price_multiplier=1.0,
        popularity_score=8,
        total_width=0, total_height=0
    ),
    ProductVariation(
        id='single_v_18x24',
        name='18x24" Vertical Canvas',
        format_type='single',
        orientation='vertical',
        width=18, height=24,
        panel_count=1, panel_spacing=0,
        price_multiplier=1.2,
        popularity_score=9,
        total_width=0, total_height=0
    ),
    ProductVariation(
        id='single_v_24x36',
        name='24x36" Vertical Canvas',
        format_type='single',
        orientation='vertical',
        width=24, height=36,
        panel_count=1, panel_spacing=0,
        price_multiplier=1.8,
        popularity_score=7,
        total_width=0, total_height=0
    ),
    
    # ========================================
    # SINGLE CANVAS - HORIZONTAL
    # ========================================
    ProductVariation(
        id='single_h_20x16',
        name='20x16" Horizontal Canvas',
        format_type='single',
        orientation='horizontal',
        width=20, height=16,
        panel_count=1, panel_spacing=0,
        price_multiplier=1.0,
        popularity_score=8,
        total_width=0, total_height=0
    ),
    ProductVariation(
        id='single_h_24x18',
        name='24x18" Horizontal Canvas',
        format_type='single',
        orientation='horizontal',
        width=24, height=18,
        panel_count=1, panel_spacing=0,
        price_multiplier=1.2,
        popularity_score=9,
        total_width=0, total_height=0
    ),
    ProductVariation(
        id='single_h_36x24',
        name='36x24" Horizontal Canvas',
        format_type='single',
        orientation='horizontal',
        width=36, height=24,
        panel_count=1, panel_spacing=0,
        price_multiplier=1.8,
        popularity_score=7,
        total_width=0, total_height=0
    ),
    
    # ========================================
    # SINGLE CANVAS - SQUARE
    # ========================================
    ProductVariation(
        id='single_sq_20x20',
        name='20x20" Square Canvas',
        format_type='single',
        orientation='square',
        width=20, height=20,
        panel_count=1, panel_spacing=0,
        price_multiplier=1.1,
        popularity_score=8,
        total_width=0, total_height=0
    ),
    ProductVariation(
        id='single_sq_30x30',
        name='30x30" Square Canvas',
        format_type='single',
        orientation='square',
        width=30, height=30,
        panel_count=1, panel_spacing=0,
        price_multiplier=1.6,
        popularity_score=6,
        total_width=0, total_height=0
    ),
    
    # ========================================
    # 3-PANEL SPLIT (TRIPTYCH) - MOST POPULAR!
    # ========================================
    ProductVariation(
        id='triptych_h_12x16',
        name='3-Panel Canvas (12x16" each) - 40" wide',
        format_type='triptych',
        orientation='horizontal',
        width=12, height=16,
        panel_count=3, panel_spacing=2,
        price_multiplier=2.5,
        popularity_score=10,  # HIGHEST!
        total_width=0, total_height=0
    ),
    ProductVariation(
        id='triptych_h_16x20',
        name='3-Panel Canvas (16x20" each) - 52" wide',
        format_type='triptych',
        orientation='horizontal',
        width=16, height=20,
        panel_count=3, panel_spacing=2,
        price_multiplier=3.2,
        popularity_score=10,  # HIGHEST!
        total_width=0, total_height=0
    ),
    ProductVariation(
        id='triptych_h_20x30',
        name='3-Panel Canvas (20x30" each) - 64" wide',
        format_type='triptych',
        orientation='horizontal',
        width=20, height=30,
        panel_count=3, panel_spacing=2,
        price_multiplier=4.5,
        popularity_score=9,
        total_width=0, total_height=0
    ),
    ProductVariation(
        id='triptych_v_16x20',
        name='3-Panel Vertical Canvas (16x20" each) - 64" tall',
        format_type='triptych',
        orientation='vertical',
        width=16, height=20,
        panel_count=3, panel_spacing=2,
        price_multiplier=3.0,
        popularity_score=8,
        total_width=0, total_height=0
    ),
    
    # ========================================
    # 2-PANEL SPLIT (DIPTYCH)
    # ========================================
    ProductVariation(
        id='diptych_h_20x24',
        name='2-Panel Canvas (20x24" each) - 42" wide',
        format_type='diptych',
        orientation='horizontal',
        width=20, height=24,
        panel_count=2, panel_spacing=2,
        price_multiplier=2.0,
        popularity_score=8,
        total_width=0, total_height=0
    ),
    ProductVariation(
        id='diptych_h_24x30',
        name='2-Panel Canvas (24x30" each) - 50" wide',
        format_type='diptych',
        orientation='horizontal',
        width=24, height=30,
        panel_count=2, panel_spacing=2,
        price_multiplier=2.5,
        popularity_score=7,
        total_width=0, total_height=0
    ),
    ProductVariation(
        id='diptych_v_16x20',
        name='2-Panel Vertical Canvas (16x20" each) - 42" tall',
        format_type='diptych',
        orientation='vertical',
        width=16, height=20,
        panel_count=2, panel_spacing=2,
        price_multiplier=1.8,
        popularity_score=7,
        total_width=0, total_height=0
    ),
]


class VariationGenerator:
    """Generate product variations with proper dimensions and pricing"""
    
    def __init__(self):
        self.variations = {v.id: v for v in VARIATIONS}
    
    def get_top_variations(self, count: int = 5) -> List[ProductVariation]:
        """Get most popular variations"""
        sorted_variations = sorted(VARIATIONS, key=lambda x: x.popularity_score, reverse=True)
        return sorted_variations[:count]
    
    def get_triptych_variations(self) -> List[ProductVariation]:
        """Get all 3-panel variations (most popular format)"""
        return [v for v in VARIATIONS if v.format_type == 'triptych']
    
    def get_single_variations(self) -> List[ProductVariation]:
        """Get single canvas variations"""
        return [v for v in VARIATIONS if v.format_type == 'single']
    
    def calculate_price(self, base_price: float, variation_id: str) -> float:
        """Calculate price for a variation"""
        variation = self.variations.get(variation_id)
        if not variation:
            return base_price
        return round(base_price * variation.price_multiplier, 2)
    
    def generate_title(self, keyword: str, style: str, variation_id: str) -> str:
        """Generate product title"""
        variation = self.variations.get(variation_id)
        if not variation:
            return f"{keyword.title()} - {style.title()} Canvas Art"
        
        style_name = style.replace('_', ' ').title()
        keyword_title = keyword.title()
        
        if variation.panel_count > 1:
            return f"{keyword_title} {style_name} - {variation.name}"
        else:
            return f"{keyword_title} {style_name} - {variation.name}"
    
    def generate_description(self, keyword: str, style: str, variation_id: str) -> str:
        """Generate product description"""
        variation = self.variations.get(variation_id)
        if not variation:
            return f"Premium {style.replace('_', ' ')} artwork featuring {keyword}."
        
        base = f"Premium {style.replace('_', ' ')} artwork featuring {keyword}. "
        
        if variation.panel_count > 1:
            desc = (
                f"{base}This stunning {variation.panel_count}-panel canvas set "
                f"creates a dramatic focal point. Each panel measures {variation.width}x{variation.height}\", "
                f"with {variation.panel_spacing}\" spacing between panels. "
                f"Total display area: {variation.total_width}x{variation.total_height}\". "
            )
        else:
            desc = (
                f"{base}High-quality {variation.width}x{variation.height}\" canvas print. "
            )
        
        desc += (
            "Printed on premium canvas with vibrant colors. "
            "Gallery-wrapped edges. Ready to hang."
        )
        
        return desc
    
    def get_recommended_for_style(self, style: str) -> List[ProductVariation]:
        """Get recommended variations for a specific art style"""
        # Photography and landscapes work well horizontally
        if style in ['photography', 'vintage', 'watercolor']:
            return [
                self.variations['triptych_h_16x20'],  # Most popular
                self.variations['single_h_24x18'],
                self.variations['diptych_h_20x24']
            ]
        
        # Typography and portraits work well vertically
        elif style in ['typography', 'line_art']:
            return [
                self.variations['single_v_18x24'],
                self.variations['triptych_h_12x16'],  # Still include triptych (most popular)
                self.variations['diptych_v_16x20']
            ]
        
        # Abstract and minimalist work with any orientation
        else:
            return [
                self.variations['triptych_h_16x20'],  # Most popular
                self.variations['single_sq_20x20'],
                self.variations['single_h_24x18']
            ]


# Singleton
_generator = None

def get_variation_generator() -> VariationGenerator:
    """Get variation generator instance"""
    global _generator
    if _generator is None:
        _generator = VariationGenerator()
    return _generator
