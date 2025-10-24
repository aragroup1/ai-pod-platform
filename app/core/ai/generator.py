import replicate
import os
from typing import Dict, Optional, Literal, List
from loguru import logger
import asyncio
import aiohttp
from datetime import datetime

ArtStyle = Literal[
    'typography', 'abstract', 'minimalist', 'vintage',
    'photography', 'watercolor', 'line_art', 'botanical'
]


class IntelligentModelSelector:
    """
    Intelligently selects the best AI model based on:
    - Art style being generated
    - Keyword characteristics (text-heavy, photorealistic, etc.)
    - Quality vs cost optimization
    """
    
    # Available AI models with their characteristics
    MODELS = {
        'flux-schnell': {
            'id': 'black-forest-labs/flux-schnell',
            'cost': 0.003,
            'speed': 5,  # seconds
            'quality': 7,  # 0-10 scale
            'text_rendering': 5,
            'photorealism': 6,
            'style_control': 6,
            'best_for': ['minimalist', 'abstract', 'testing']
        },
        'flux-dev': {
            'id': 'black-forest-labs/flux-dev',
            'cost': 0.025,
            'speed': 8,
            'quality': 8,
            'text_rendering': 7,
            'photorealism': 8,
            'style_control': 8,
            'best_for': ['watercolor', 'line_art', 'botanical']
        },
        'flux-pro': {
            'id': 'black-forest-labs/flux-1.1-pro',
            'cost': 0.04,
            'speed': 10,
            'quality': 9,
            'text_rendering': 7,
            'photorealism': 9,
            'style_control': 8,
            'best_for': ['photography', 'vintage', 'abstract']
        },
        'ideogram-turbo': {
            'id': 'ideogram-ai/ideogram-v3-turbo',
            'cost': 0.025,
            'speed': 6,
            'quality': 8,
            'text_rendering': 10,  # BEST for text!
            'photorealism': 7,
            'style_control': 7,
            'best_for': ['typography', 'quotes', 'text-heavy']
        }
    }
    
    def __init__(self, budget_mode: str = "balanced"):
        """
        Initialize model selector
        
        Args:
            budget_mode: "cheap" | "balanced" | "quality"
        """
        self.budget_mode = budget_mode
    
    def select_model(self, style: str, keyword: str) -> Dict:
        """
        Intelligently select the best model
        
        Args:
            style: Art style (minimalist, abstract, typography, etc.)
            keyword: The keyword/prompt
            
        Returns:
            Dict with model selection and reasoning
        """
        style_lower = style.lower()
        keyword_lower = keyword.lower()
        
        reasoning = []
        
        # Rule 1: Typography & Text-Heavy Content
        if self._needs_text_rendering(style_lower, keyword_lower):
            selected = 'ideogram-turbo'
            reasoning.append("Text-heavy content detected")
            reasoning.append("Ideogram has best text rendering (10/10)")
        
        # Rule 2: Photorealism & Photography
        elif style_lower in ['photography', 'photorealistic']:
            if self.budget_mode == "quality":
                selected = 'flux-pro'
                reasoning.append("Photography requires high quality")
                reasoning.append("FLUX Pro offers best photorealism (9/10)")
            else:
                selected = 'flux-dev'
                reasoning.append("Photography with balanced quality/cost")
                reasoning.append("FLUX Dev provides good photorealism (8/10)")
        
        # Rule 3: Detailed/Artistic Styles
        elif style_lower in ['watercolor', 'botanical', 'line_art']:
            selected = 'flux-dev'
            reasoning.append(f"Artistic style '{style}' detected")
            reasoning.append("FLUX Dev excels at artistic rendering")
        
        # Rule 4: Budget Mode Override
        elif self.budget_mode == "cheap":
            selected = 'flux-schnell'
            reasoning.append("Budget mode: using fastest/cheapest")
            reasoning.append("FLUX Schnell at $0.003 per image")
        
        # Rule 5: Style-Based Selection
        else:
            selected = self._select_by_style(style_lower)
            reasoning.append(f"Style-optimized selection for '{style}'")
        
        model_info = self.MODELS[selected]
        
        return {
            'model_key': selected,
            'model_id': model_info['id'],
            'cost': model_info['cost'],
            'quality_score': model_info['quality'],
            'estimated_time': model_info['speed'],
            'reasoning': reasoning,
            'specs': model_info
        }
    
    def _needs_text_rendering(self, style: str, keyword: str) -> bool:
        """Check if text rendering is critical"""
        text_indicators = [
            'typography', 'text', 'quote', 'saying', 'words',
            'lettering', 'font', 'script', 'motivational',
            'inspirational', 'affirmation', 'slogan', 'phrase',
            'message', 'sign'
        ]
        return any(ind in style for ind in text_indicators) or \
               any(ind in keyword for ind in text_indicators)
    
    def _select_by_style(self, style: str) -> str:
        """Select model based on art style"""
        style_map = {
            'typography': 'ideogram-turbo',
            'photography': 'flux-pro',
            'vintage': 'flux-pro',
            'abstract': 'flux-dev',
            'watercolor': 'flux-dev',
            'botanical': 'flux-dev',
            'line_art': 'flux-dev',
            'minimalist': 'flux-schnell'
        }
        
        for style_key, model in style_map.items():
            if style_key in style:
                return model
        
        # Default based on budget mode
        if self.budget_mode == "cheap":
            return 'flux-schnell'
        elif self.budget_mode == "quality":
            return 'flux-pro'
        return 'flux-dev'
    
    def estimate_batch_cost(self, keywords: List[str], styles: List[str]) -> Dict:
        """
        Estimate total cost for batch generation
        
        Args:
            keywords: List of keywords
            styles: List of styles
            
        Returns:
            Cost breakdown
        """
        total_cost = 0
        breakdown = {}
        
        for keyword in keywords:
            for style in styles:
                selection = self.select_model(style, keyword)
                key = f"{keyword[:20]}... - {style}"
                breakdown[key] = {
                    'model': selection['model_key'],
                    'cost': selection['cost']
                }
                total_cost += selection['cost']
        
        return {
            'total_cost': round(total_cost, 4),
            'total_images': len(keywords) * len(styles),
            'avg_cost': round(total_cost / (len(keywords) * len(styles)), 4),
            'breakdown': breakdown
        }


class AIArtGenerator:
    """
    Multi-model AI art generation with intelligent model selection
    Automatically chooses the best AI model for each generation
    """
    
    def __init__(self, testing_mode: bool = False, budget_mode: str = "balanced"):
        """
        Initialize AI Art Generator
        
        Args:
            testing_mode: If True, force use FLUX-Schnell for all generations
            budget_mode: "cheap" | "balanced" | "quality" - affects model selection
        """
        self.api_token = os.getenv('REPLICATE_API_TOKEN')
        self.testing_mode = testing_mode
        self.budget_mode = budget_mode
        
        if not self.api_token:
            logger.error("❌ REPLICATE_API_TOKEN not found in environment!")
            raise ValueError("Replicate API token required")
        
        # Verify token format
        if not self.api_token.startswith('r8_'):
            logger.warning("⚠️ API token doesn't start with 'r8_' - might be invalid")
        
        os.environ['REPLICATE_API_TOKEN'] = self.api_token
        
        # Initialize intelligent model selector
        self.model_selector = IntelligentModelSelector(budget_mode=budget_mode)
        
        mode = "TESTING (cheap)" if testing_mode else f"PRODUCTION ({budget_mode})"
        logger.info(f"✅ AI Generator initialized - Mode: {mode}")
    
    def get_model_for_style(self, style: ArtStyle, keyword: str) -> Dict:
        """
        Get the best model for a given art style and keyword
        
        Returns full selection details including reasoning
        """
        if self.testing_mode:
            return {
                'model_key': 'flux-schnell',
                'model_id': 'black-forest-labs/flux-schnell',
                'cost': 0.003,
                'quality_score': 7,
                'reasoning': ['Testing mode: using cheapest model']
            }
        
        return self.model_selector.select_model(style, keyword)
    
    async def generate_image(
        self,
        prompt: str,
        style: ArtStyle,
        keyword: str = "",
        aspect_ratio: str = "1:1",
        width: int = 1024,
        height: int = 1024
    ) -> Dict:
        """
        Generate AI artwork with intelligent model selection
        
        Args:
            prompt: Text description of the image
            style: Art style category
            keyword: Main keyword (helps with model selection)
            aspect_ratio: Image ratio (1:1, 16:9, 3:4, etc.)
            width: Image width in pixels
            height: Image height in pixels
            
        Returns:
            Dict with image_url, model_used, style, prompt, and selection reasoning
        """
        # Get intelligent model selection
        model_selection = self.get_model_for_style(style, keyword)
        model_id = model_selection['model_id']
        model_key = model_selection['model_key']
        
        logger.info(f"🎨 Generating {style} image")
        logger.info(f"🤖 Selected: {model_key} (${model_selection['cost']})")
        logger.info(f"💡 Reasoning: {', '.join(model_selection['reasoning'])}")
        logger.debug(f"📝 Prompt: {prompt[:100]}...")
        
        try:
            # Run generation in thread pool (Replicate SDK is synchronous)
            loop = asyncio.get_event_loop()
            output = await loop.run_in_executor(
                None,
                self._generate_sync,
                model_id,
                model_key,
                prompt,
                aspect_ratio,
                width,
                height
            )
            
            # Extract image URL from output
            if isinstance(output, list) and len(output) > 0:
                image_url = str(output[0])
            elif hasattr(output, 'url'):
                image_url = str(output.url)
            else:
                image_url = str(output)
            
            result = {
                'image_url': image_url,
                'model_used': model_id,
                'model_key': model_key,
                'style': style,
                'prompt': prompt,
                'keyword': keyword,
                'generated_at': datetime.utcnow().isoformat(),
                'dimensions': f"{width}x{height}",
                'generation_cost': model_selection['cost'],
                'quality_score': model_selection['quality_score'],
                'selection_reasoning': model_selection['reasoning']
            }
            
            logger.info(f"✅ Image generated successfully!")
            logger.debug(f"🔗 URL: {image_url[:80]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error generating image: {e}")
            raise
    
    def _generate_sync(
        self,
        model_id: str,
        model_key: str,
        prompt: str,
        aspect_ratio: str,
        width: int,
        height: int
    ):
        """Synchronous generation (runs in executor)"""
        
        # Different models have different parameters
        if 'flux-schnell' in model_id:
            # FLUX-Schnell - Fast and cheap
            logger.debug("Using FLUX-Schnell (4 steps, fast)")
            output = replicate.run(
                model_id,
                input={
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "num_inference_steps": 4,
                    "output_format": "png",
                    "output_quality": 90
                }
            )
            
        elif 'flux-dev' in model_id:
            # FLUX-Dev - Good quality
            logger.debug("Using FLUX-Dev (balanced quality/speed)")
            output = replicate.run(
                model_id,
                input={
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "guidance_scale": 7.5,
                    "num_inference_steps": 50,
                    "output_format": "png",
                    "output_quality": 95
                }
            )
            
        elif 'flux-1.1-pro' in model_id:
            # FLUX-1.1-Pro - Best quality
            logger.debug("Using FLUX-1.1-Pro (premium quality)")
            output = replicate.run(
                model_id,
                input={
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "prompt_upsampling": True,
                    "output_format": "png",
                    "output_quality": 100,
                    "safety_tolerance": 2
                }
            )
            
        elif 'ideogram' in model_id:
            # Ideogram v3 Turbo - Great for typography
            logger.debug("Using Ideogram v3 Turbo (text optimized)")
            output = replicate.run(
                model_id,
                input={
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "magic_prompt_option": "Auto",
                    "output_format": "png"
                }
            )
            
        else:
            # Generic fallback
            logger.debug(f"Using generic parameters for {model_id}")
            output = replicate.run(
                model_id,
                input={
                    "prompt": prompt,
                    "width": width,
                    "height": height
                }
            )
        
        return output
    
    async def upscale_image(
        self,
        image_url: str,
        scale: int = 4
    ) -> Dict:
        """
        Upscale image for print quality using Topaz Labs
        
        Args:
            image_url: URL of image to upscale
            scale: Upscale factor (2 or 4)
            
        Returns:
            Dict with upscaled_url
        """
        logger.info(f"📈 Upscaling image {scale}x for print quality")
        
        try:
            loop = asyncio.get_event_loop()
            output = await loop.run_in_executor(
                None,
                replicate.run,
                "topazlabs/image-upscale",
                {
                    "image": image_url,
                    "scale": scale,
                    "face_enhance": False
                }
            )
            
            upscaled_url = str(output) if not isinstance(output, list) else str(output[0])
            
            result = {
                'upscaled_url': upscaled_url,
                'scale': scale,
                'upscaled_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ Image upscaled successfully to {scale}x")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error upscaling image: {e}")
            raise
    
    async def generate_product_artwork(
        self,
        keyword: str,
        style: ArtStyle,
        upscale_for_print: bool = False
    ) -> Dict:
        """
        Complete workflow: Generate and optionally upscale
        
        Args:
            keyword: Main keyword/trend
            style: Art style to use
            upscale_for_print: Whether to upscale to 4K
            
        Returns:
            Complete artwork data with model selection details
        """
        from app.core.ai.prompt_templates import get_prompt_for_style
        
        # Get optimized prompt for this style
        prompt_config = get_prompt_for_style(keyword, style)
        
        # Generate base image with intelligent model selection
        result = await self.generate_image(
            prompt=prompt_config['prompt'],
            style=style,
            keyword=keyword
        )
        
        # Upscale if needed for print
        if upscale_for_print:
            upscaled = await self.upscale_image(
                result['image_url'],
                scale=4
            )
            result['print_url'] = upscaled['upscaled_url']
            result['print_ready'] = True
        else:
            result['print_ready'] = False
        
        return result
    
    async def batch_generate(
        self,
        keywords: List[str],
        styles: List[ArtStyle],
        upscale: bool = False
    ) -> List[Dict]:
        """
        Generate multiple artworks in batch
        
        Args:
            keywords: List of keywords/trends
            styles: List of styles to generate for each
            upscale: Whether to upscale all images
            
        Returns:
            List of generated artworks with model selection details
        """
        results = []
        total = len(keywords) * len(styles)
        
        logger.info(f"🚀 Starting batch generation: {len(keywords)} keywords × {len(styles)} styles = {total} images")
        
        # Show cost estimate
        cost_estimate = self.model_selector.estimate_batch_cost(keywords, styles)
        logger.info(f"💰 Estimated total cost: ${cost_estimate['total_cost']}")
        logger.info(f"📊 Average cost per image: ${cost_estimate['avg_cost']}")
        
        for i, keyword in enumerate(keywords):
            for j, style in enumerate(styles):
                try:
                    logger.info(f"Progress: {len(results)+1}/{total} - {keyword} ({style})")
                    
                    artwork = await self.generate_product_artwork(
                        keyword=keyword,
                        style=style,
                        upscale_for_print=upscale
                    )
                    
                    results.append(artwork)
                    
                    # Rate limiting - wait between generations
                    if len(results) < total:
                        await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Failed to generate {keyword} ({style}): {e}")
                    continue
        
        logger.info(f"✅ Batch complete: {len(results)}/{total} images generated")
        
        # Calculate actual costs
        total_cost = sum(r.get('generation_cost', 0) for r in results)
        logger.info(f"💰 Actual total cost: ${total_cost:.4f}")
        
        return results


# Singleton instance
_generator = None

def get_ai_generator(testing_mode: bool = False, budget_mode: str = "balanced") -> AIArtGenerator:
    """Get or create AI generator instance"""
    global _generator
    if _generator is None:
        _generator = AIArtGenerator(testing_mode=testing_mode, budget_mode=budget_mode)
    return _generator
