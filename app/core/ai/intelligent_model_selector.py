"""
Intelligent AI Model Selector
Automatically chooses the best model based on art style, keyword, and requirements
"""

from typing import Dict, Optional
from enum import Enum
from loguru import logger


class AIModel(str, Enum):
    """Available AI models with their strengths"""
    
    # CHEAPEST - Best for general use
    FLUX_SCHNELL = "black-forest-labs/flux-schnell"  # $0.003 - Fast, cheap, general
    
    # TEXT-FOCUSED - Best for typography
    IDEOGRAM_V3_TURBO = "ideogram-ai/ideogram-v3-turbo"  # $0.025 - Best text rendering
    
    # HIGH-QUALITY - Best for photorealism
    FLUX_PRO = "black-forest-labs/flux-1.1-pro"  # $0.04 - Best overall quality
    
    # STYLE CONTROL - Best for specific aesthetics
    FLUX_KONTEXT = "black-forest-labs/flux-kontext-pro"  # $0.06 - Best style control
    
    # PREMIUM - Best for maximum quality
    IMAGEN_4 = "google/imagen-4"  # $0.08 - Google's best


class ModelSelector:
    """
    Intelligently selects the best AI model based on:
    - Art style being generated
    - Keyword characteristics
    - Budget constraints
    - Quality requirements
    """
    
    def __init__(self, budget_mode: str = "balanced"):
        """
        Initialize model selector
        
        Args:
            budget_mode: "cheap" | "balanced" | "quality"
        """
        self.budget_mode = budget_mode
        
        # Model characteristics
        self.model_specs = {
            AIModel.FLUX_SCHNELL: {
                "cost": 0.003,
                "speed": 5,  # seconds
                "quality": 7,  # 0-10 scale
                "text_rendering": 5,
                "photorealism": 6,
                "style_control": 6,
                "strengths": ["fast", "cheap", "general"],
                "best_for": ["minimalist", "abstract", "general"]
            },
            AIModel.IDEOGRAM_V3_TURBO: {
                "cost": 0.025,
                "speed": 6,
                "quality": 8,
                "text_rendering": 10,  # BEST for text!
                "photorealism": 7,
                "style_control": 7,
                "strengths": ["text", "typography", "quotes", "posters"],
                "best_for": ["typography", "line_art", "posters"]
            },
            AIModel.FLUX_PRO: {
                "cost": 0.04,
                "speed": 10,
                "quality": 9,
                "text_rendering": 7,
                "photorealism": 9,
                "style_control": 8,
                "strengths": ["quality", "photorealism", "diversity"],
                "best_for": ["photography", "watercolor", "vintage"]
            },
            AIModel.FLUX_KONTEXT: {
                "cost": 0.06,
                "speed": 12,
                "quality": 9,
                "text_rendering": 8,
                "photorealism": 9,
                "style_control": 10,  # BEST for style control!
                "strengths": ["style_control", "photoreal", "illustrated"],
                "best_for": ["botanical", "vintage", "specific_styles"]
            },
            AIModel.IMAGEN_4: {
                "cost": 0.08,
                "speed": 15,
                "quality": 10,  # BEST quality!
                "text_rendering": 8,
                "photorealism": 10,
                "style_control": 9,
                "strengths": ["premium", "detail", "lighting"],
                "best_for": ["photography", "high_end", "print_quality"]
            }
        }
    
    def select_model(
        self,
        style: str,
        keyword: str,
        quality_priority: Optional[int] = None
    ) -> Dict:
        """
        Intelligently select the best model
        
        Args:
            style: Art style (minimalist, abstract, typography, etc.)
            keyword: The keyword/prompt
            quality_priority: Override quality (1-10), higher = better/more expensive
            
        Returns:
            Dict with model selection and reasoning
        """
        style_lower = style.lower()
        keyword_lower = keyword.lower()
        
        # Rule-based selection
        selected_model = None
        reasoning = []
        
        # ==========================================
        # RULE 1: Typography & Text-Heavy
        # ==========================================
        if self._needs_text_rendering(style_lower, keyword_lower):
            selected_model = AIModel.IDEOGRAM_V3_TURBO
            reasoning.append("Typography/text-heavy content detected")
            reasoning.append("Ideogram has best text rendering capabilities")
        
        # ==========================================
        # RULE 2: Photorealism & Photography
        # ==========================================
        elif style_lower in ["photography", "photorealistic"] and self.budget_mode != "cheap":
            if self.budget_mode == "quality":
                selected_model = AIModel.IMAGEN_4
                reasoning.append("Photography style with quality priority")
                reasoning.append("Imagen 4 offers best photorealism")
            else:
                selected_model = AIModel.FLUX_PRO
                reasoning.append("Photography style detected")
                reasoning.append("FLUX Pro balances quality and cost")
        
        # ==========================================
        # RULE 3: Specific Style Control
        # ==========================================
        elif self._needs_style_control(style_lower, keyword_lower):
            if self.budget_mode == "quality":
                selected_model = AIModel.FLUX_KONTEXT
                reasoning.append("Complex style requirements detected")
                reasoning.append("FLUX Kontext offers best style control")
            else:
                selected_model = AIModel.FLUX_PRO
                reasoning.append("Style control needed, using FLUX Pro for balance")
        
        # ==========================================
        # RULE 4: Budget Mode Overrides
        # ==========================================
        elif self.budget_mode == "cheap":
            selected_model = AIModel.FLUX_SCHNELL
            reasoning.append("Budget mode: using cheapest model")
            reasoning.append("FLUX Schnell is fast and cost-effective")
        
        # ==========================================
        # RULE 5: Quality Priority Override
        # ==========================================
        elif quality_priority and quality_priority >= 9:
            selected_model = AIModel.IMAGEN_4
            reasoning.append("High quality priority (9+) specified")
            reasoning.append("Using premium Imagen 4 model")
        
        # ==========================================
        # RULE 6: Default Based on Style
        # ==========================================
        else:
            selected_model = self._select_by_style(style_lower)
            reasoning.append(f"Style-based selection for '{style}'")
        
        # Get model specs
        specs = self.model_specs[selected_model]
        
        return {
            "model": selected_model,
            "model_id": selected_model.value,
            "cost": specs["cost"],
            "estimated_time": specs["speed"],
            "quality_score": specs["quality"],
            "reasoning": reasoning,
            "specs": specs
        }
    
    def _needs_text_rendering(self, style: str, keyword: str) -> bool:
        """Check if text rendering is critical"""
        text_indicators = [
            # Style indicators
            "typography", "text", "quote", "saying", "words",
            "lettering", "font", "script", "calligraphy",
            
            # Keyword indicators
            "quote", "saying", "words", "message", "sign",
            "motivational", "inspirational", "affirmation",
            "slogan", "phrase", "text", "typography"
        ]
        
        return any(indicator in style for indicator in text_indicators) or \
               any(indicator in keyword for indicator in text_indicators)
    
    def _needs_style_control(self, style: str, keyword: str) -> bool:
        """Check if precise style control is needed"""
        style_control_indicators = [
            # Specific styles
            "vintage", "retro", "art deco", "bauhaus", "art nouveau",
            "baroque", "renaissance", "impressionist", "cubist",
            
            # Complex requirements
            "specific", "precise", "exact", "particular",
            
            # Detailed styles
            "botanical", "detailed", "intricate", "complex"
        ]
        
        return any(indicator in style for indicator in style_control_indicators) or \
               any(indicator in keyword for indicator in style_control_indicators)
    
    def _select_by_style(self, style: str) -> AIModel:
        """Select model based on art style"""
        
        # Style-to-model mapping
        style_map = {
            # Text-focused styles
            "typography": AIModel.IDEOGRAM_V3_TURBO,
            "text": AIModel.IDEOGRAM_V3_TURBO,
            
            # Photorealistic styles
            "photography": AIModel.FLUX_PRO,
            "photorealistic": AIModel.FLUX_PRO,
            "realistic": AIModel.FLUX_PRO,
            
            # Detailed/Complex styles
            "botanical": AIModel.FLUX_KONTEXT if self.budget_mode == "quality" else AIModel.FLUX_PRO,
            "vintage": AIModel.FLUX_PRO,
            "watercolor": AIModel.FLUX_PRO,
            
            # Simple/Fast styles
            "minimalist": AIModel.FLUX_SCHNELL,
            "abstract": AIModel.FLUX_SCHNELL,
            "line_art": AIModel.FLUX_SCHNELL if self.budget_mode == "cheap" else AIModel.IDEOGRAM_V3_TURBO,
        }
        
        # Check if style matches
        for style_key, model in style_map.items():
            if style_key in style:
                return model
        
        # Default based on budget mode
        if self.budget_mode == "cheap":
            return AIModel.FLUX_SCHNELL
        elif self.budget_mode == "quality":
            return AIModel.FLUX_PRO
        else:  # balanced
            return AIModel.FLUX_SCHNELL
    
    def get_batch_recommendations(
        self,
        styles: list,
        keyword: str
    ) -> Dict[str, Dict]:
        """
        Get model recommendations for multiple styles
        
        Args:
            styles: List of style names
            keyword: The keyword
            
        Returns:
            Dict mapping style to model recommendation
        """
        recommendations = {}
        
        for style in styles:
            recommendations[style] = self.select_model(style, keyword)
        
        return recommendations
    
    def estimate_batch_cost(
        self,
        styles: list,
        keyword: str
    ) -> Dict:
        """
        Estimate total cost for generating all styles
        
        Args:
            styles: List of style names
            keyword: The keyword
            
        Returns:
            Cost breakdown and total
        """
        recommendations = self.get_batch_recommendations(styles, keyword)
        
        total_cost = sum(rec["cost"] for rec in recommendations.values())
        total_time = sum(rec["estimated_time"] for rec in recommendations.values())
        
        breakdown = {
            style: {
                "model": rec["model"],
                "cost": rec["cost"]
            }
            for style, rec in recommendations.items()
        }
        
        return {
            "total_cost": round(total_cost, 4),
            "total_time_seconds": total_time,
            "average_cost": round(total_cost / len(styles), 4),
            "breakdown": breakdown,
            "cheapest_style": min(breakdown.items(), key=lambda x: x[1]["cost"]),
            "most_expensive_style": max(breakdown.items(), key=lambda x: x[1]["cost"])
        }


# ==========================================
# USAGE EXAMPLES
# ==========================================

def example_usage():
    """Show how to use the intelligent model selector"""
    
    # Initialize with budget mode
    selector = ModelSelector(budget_mode="balanced")
    
    # Example 1: Typography poster
    result = selector.select_model(
        style="typography",
        keyword="motivational quote poster"
    )
    print(f"\n📝 Typography Example:")
    print(f"Selected: {result['model']}")
    print(f"Cost: ${result['cost']}")
    print(f"Reasoning: {', '.join(result['reasoning'])}")
    
    # Example 2: Photorealistic landscape
    result = selector.select_model(
        style="photography",
        keyword="mountain landscape sunset"
    )
    print(f"\n📸 Photography Example:")
    print(f"Selected: {result['model']}")
    print(f"Cost: ${result['cost']}")
    print(f"Reasoning: {', '.join(result['reasoning'])}")
    
    # Example 3: Minimalist design (cheap!)
    result = selector.select_model(
        style="minimalist",
        keyword="simple geometric shapes"
    )
    print(f"\n✨ Minimalist Example:")
    print(f"Selected: {result['model']}")
    print(f"Cost: ${result['cost']}")
    print(f"Reasoning: {', '.join(result['reasoning'])}")
    
    # Example 4: Batch cost estimation
    all_styles = [
        "minimalist", "abstract", "vintage", "watercolor",
        "line_art", "photography", "typography", "botanical"
    ]
    
    cost_estimate = selector.estimate_batch_cost(
        styles=all_styles,
        keyword="mountain landscape"
    )
    
    print(f"\n💰 Batch Cost Estimate (8 styles):")
    print(f"Total Cost: ${cost_estimate['total_cost']}")
    print(f"Total Time: {cost_estimate['total_time_seconds']}s")
    print(f"Average: ${cost_estimate['average_cost']}/image")
    print(f"\nCheapest: {cost_estimate['cheapest_style'][0]} (${cost_estimate['cheapest_style'][1]['cost']})")
    print(f"Most Expensive: {cost_estimate['most_expensive_style'][0]} (${cost_estimate['most_expensive_style'][1]['cost']})")


# ==========================================
# INTEGRATION HELPER
# ==========================================

def get_model_for_generation(
    style: str,
    keyword: str,
    budget_mode: str = "balanced"
) -> str:
    """
    Simple helper function to get model ID
    
    Args:
        style: Art style name
        keyword: Keyword/prompt
        budget_mode: "cheap" | "balanced" | "quality"
        
    Returns:
        Model ID string for Replicate API
    """
    selector = ModelSelector(budget_mode=budget_mode)
    result = selector.select_model(style, keyword)
    
    logger.info(f"🤖 Selected {result['model']} for {style}")
    logger.info(f"💰 Cost: ${result['cost']}, Time: ~{result['estimated_time']}s")
    logger.info(f"📋 Reasoning: {', '.join(result['reasoning'])}")
    
    return result["model_id"]


if __name__ == "__main__":
    example_usage()
