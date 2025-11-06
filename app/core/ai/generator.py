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
            'speed': 5,
            'quality': 7,
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
            'text_rendering': 10,
            'photorealism': 7,
            'style_control': 7,
            'best_for': ['typography', 'quotes', 'text-heavy']
        }
    }
    
    def __init__(self, budget_mode: str = "balanced"):
        self.budget_mode = budget_mode
    
    def select_model(self, style: str, keyword: str) -> Dict:
        style_lower = style.lower()
        keyword_lower = keyword.lower()
        
        reasoning = []
        
        if self._needs_text_rendering(style_lower, keyword_lower):
            selected = 'ideogram-turbo'
            reasoning.append("Text-heavy content detected")
            reasoning.append("Ideogram has best text rendering (10/10)")
        
        elif style_lower in ['photography', 'photorealistic']:
            if self.budget_mode == "quality":
                selected = 'flux-pro'
                reasoning.append("Photography requires high quality")
                reasoning.append("FLUX Pro offers best photorealism (9/10)")
            else:
                selected = 'flux-dev'
                reasoning.append("Photography with balanced quality/cost")
                reasoning.append("FLUX Dev provides good photorealism (8/10)")
        
        elif style_lower in ['watercolor', 'botanical', 'line_art']:
            selected = 'flux-dev'
            reasoning.append(f"Artistic style '{style}' detected")
            reasoning.append("FLUX Dev excels at artistic rendering")
        
        elif self.budget_mode == "cheap":
            selected = 'flux-schnell'
            reasoning.append("Budget mode: using fastest/cheapest")
            reasoning.append("FLUX Schnell at $0.003 per image")
        
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
        text_indicators = [
            'typography', 'text', 'quote', 'saying', 'words',
            'lettering', 'font', 'script', 'motivational',
            'inspirational', 'affirmation', 'slogan', 'phrase',
            'message', 'sign'
        ]
        return any(ind in style for ind in text_indicators) or \
               any(ind in keyword for ind in text_indicators)
    
    def _select_by_style(self, style: str) -> str:
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
        
        if self.budget_mode == "cheap":
            return 'flux-schnell'
        elif self.budget_mode == "quality":
            return 'flux-pro'
        return 'flux-dev'


class AIArtGenerator:
    """
    Multi-model AI art generation with intelligent model selection
    """
    
    def __init__(self, testing_mode: bool = False, budget_mode: str = "balanced"):
        self.api_token = os.getenv('REPLICATE_API_TOKEN')
        self.testing_mode = testing_mode
        self.budget_mode = budget_mode
        
        if not self.api_token:
            logger.error("❌ REPLICATE_API_TOKEN not found in environment!")
            raise ValueError("Replicate API token required")
        
        if not self.api_token.startswith('r8_'):
            logger.warning("⚠️ API token doesn't start with 'r8_' - might be invalid")
        
        os.environ['REPLICATE_API_TOKEN'] = self.api_token
        
        self.model_selector = IntelligentModelSelector(budget_mode=budget_mode)
        
        mode = "TESTING (cheap)" if testing_mode else f"PRODUCTION ({budget_mode})"
        logger.info(f"✅ AI Generator initialized - Mode: {mode}")
    
    def get_model_for_style(self, style: ArtStyle, keyword: str) -> Dict:
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
        
        CRITICAL FIX: Properly extract and return image URL
        """
        model_selection = self.get_model_for_style(style, keyword)
        model_id = model_selection['model_id']
        model_key = model_selection['model_key']
        
        logger.info(f"🎨 Generating {style} image")
        logger.info(f"🤖 Selected: {model_key} (${model_selection['cost']})")
        logger.info(f"💡 Reasoning: {', '.join(model_selection['reasoning'])}")
        logger.debug(f"📝 Prompt: {prompt[:100]}...")
        
        try:
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
            
            # ✅ CRITICAL FIX: Properly extract image URL
            image_url = self._extract_image_url(output)
            
            if not image_url:
                raise ValueError(f"Failed to extract image URL from output: {output}")
            
            logger.info(f"✅ Image generated successfully!")
            logger.info(f"🔗 URL: {image_url[:100]}...")
            
            result = {
                'image_url': image_url,  # ✅ This is the actual URL string
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
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error generating image: {e}")
            logger.exception("Full traceback:")
            raise
    
    def _extract_image_url(self, output) -> str:
        """
        ✅ CRITICAL FIX: Extract image URL from various output formats
        """
        logger.debug(f"🔍 Extracting URL from output type: {type(output)}")
        logger.debug(f"🔍 Output value: {output}")
        
        # Case 1: List with URL string
        if isinstance(output, list) and len(output) > 0:
            url = str(output[0])
            logger.debug(f"✅ Extracted from list: {url}")
            return url
        
        # Case 2: Direct URL string
        if isinstance(output, str):
            logger.debug(f"✅ Direct string: {output}")
            return output
        
        # Case 3: Object with url attribute
        if hasattr(output, 'url'):
            url = str(output.url)
            logger.debug(f"✅ From .url attribute: {url}")
            return url
        
        # Case 4: Dict with url key
        if isinstance(output, dict) and 'url' in output:
            url = str(output['url'])
            logger.debug(f"✅ From dict['url']: {url}")
            return url
        
        # Case 5: FileOutput object (Replicate's type)
        if hasattr(output, '__iter__') and not isinstance(output, (str, bytes)):
            try:
                first_item = next(iter(output))
                url = str(first_item)
                logger.debug(f"✅ From iterator: {url}")
                return url
            except:
                pass
        
        # Fallback: Convert to string
        url = str(output)
        logger.warning(f"⚠️ Fallback string conversion: {url}")
        return url
    
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
        
        logger.debug(f"🔧 Starting sync generation with model: {model_id}")
        
        if 'flux-schnell' in model_id:
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
            logger.debug(f"Using generic parameters for {model_id}")
            output = replicate.run(
                model_id,
                input={
                    "prompt": prompt,
                    "width": width,
                    "height": height
                }
            )
        
        logger.debug(f"✅ Generation complete, output type: {type(output)}")
        return output
    
    async def generate_product_artwork(
        self,
        keyword: str,
        style: ArtStyle,
        upscale_for_print: bool = False
    ) -> Dict:
        """Complete workflow: Generate and optionally upscale"""
        from app.core.ai.prompt_templates import get_prompt_for_style
        
        prompt_config = get_prompt_for_style(keyword, style)
        
        result = await self.generate_image(
            prompt=prompt_config['prompt'],
            style=style,
            keyword=keyword
        )
        
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


# Singleton instance
_generator = None

def get_ai_generator(testing_mode: bool = False, budget_mode: str = "balanced") -> AIArtGenerator:
    """Get or create AI generator instance"""
    global _generator
    if _generator is None:
        _generator = AIArtGenerator(testing_mode=testing_mode, budget_mode=budget_mode)
    return _generator
