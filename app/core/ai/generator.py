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


class AIArtGenerator:
    """
    Multi-model AI art generation optimized for Print-on-Demand
    Uses Replicate's free tier models strategically
    """
    
    # Model selection based on quality needs and cost
    MODEL_STRATEGY = {
        'typography': {
            'model': 'ideogram-ai/ideogram-v3-turbo',
            'reason': 'Best for text rendering in images'
        },
        'abstract': {
            'model': 'black-forest-labs/flux-1.1-pro',
            'reason': 'High quality abstract art'
        },
        'minimalist': {
            'model': 'black-forest-labs/flux-1.1-pro',
            'reason': 'Clean professional results'
        },
        'vintage': {
            'model': 'black-forest-labs/flux-1.1-pro',
            'reason': 'Great texture and detail'
        },
        'photography': {
            'model': 'black-forest-labs/flux-1.1-pro',
            'reason': 'Photorealistic quality'
        },
        'watercolor': {
            'model': 'black-forest-labs/flux-dev',
            'reason': 'Good artistic quality'
        },
        'line_art': {
            'model': 'black-forest-labs/flux-dev',
            'reason': 'Clean lines'
        },
        'botanical': {
            'model': 'black-forest-labs/flux-dev',
            'reason': 'Detailed illustrations'
        }
    }
    
    # Testing mode uses fastest/cheapest model
    TESTING_MODEL = 'black-forest-labs/flux-schnell'
    
    def __init__(self, testing_mode: bool = False):
        """
        Initialize AI Art Generator
        
        Args:
            testing_mode: If True, use FLUX-Schnell for cheap testing
        """
        self.api_token = os.getenv('REPLICATE_API_TOKEN')
        self.testing_mode = testing_mode
        
        if not self.api_token:
            logger.error("❌ REPLICATE_API_TOKEN not found in environment!")
            raise ValueError("Replicate API token required")
        
        # Verify token format
        if not self.api_token.startswith('r8_'):
            logger.warning("⚠️ API token doesn't start with 'r8_' - might be invalid")
        
        os.environ['REPLICATE_API_TOKEN'] = self.api_token
        
        mode = "TESTING (cheap)" if testing_mode else "PRODUCTION (quality)"
        logger.info(f"✅ AI Generator initialized - Mode: {mode}")
    
    def get_model_for_style(self, style: ArtStyle) -> str:
        """Get the best model for a given art style"""
        if self.testing_mode:
            return self.TESTING_MODEL
        
        strategy = self.MODEL_STRATEGY.get(style)
        if not strategy:
            return 'black-forest-labs/flux-1.1-pro'
        
        return strategy['model']
    
    async def generate_image(
        self,
        prompt: str,
        style: ArtStyle,
        aspect_ratio: str = "1:1",
        width: int = 1024,
        height: int = 1024
    ) -> Dict:
        """
        Generate AI artwork
        
        Args:
            prompt: Text description of the image
            style: Art style category
            aspect_ratio: Image ratio (1:1, 16:9, 3:4, etc.)
            width: Image width in pixels
            height: Image height in pixels
            
        Returns:
            Dict with image_url, model_used, style, prompt
        """
        model_name = self.get_model_for_style(style)
        
        logger.info(f"🎨 Generating {style} image with {model_name}")
        logger.debug(f"📝 Prompt: {prompt[:100]}...")
        
        try:
            # Run generation in thread pool (Replicate SDK is synchronous)
            loop = asyncio.get_event_loop()
            output = await loop.run_in_executor(
                None,
                self._generate_sync,
                model_name,
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
                'model_used': model_name,
                'style': style,
                'prompt': prompt,
                'generated_at': datetime.utcnow().isoformat(),
                'dimensions': f"{width}x{height}"
            }
            
            logger.info(f"✅ Image generated successfully!")
            logger.debug(f"🔗 URL: {image_url[:80]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error generating image: {e}")
            raise
    
    def _generate_sync(
        self,
        model_name: str,
        prompt: str,
        aspect_ratio: str,
        width: int,
        height: int
    ):
        """Synchronous generation (runs in executor)"""
        
        # Different models have different parameters
        if 'flux-schnell' in model_name:
            # FLUX-Schnell - Fast and cheap
            logger.debug("Using FLUX-Schnell (4 steps, fast)")
            output = replicate.run(
                model_name,
                input={
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "num_inference_steps": 4,
                    "output_format": "png",
                    "output_quality": 90
                }
            )
            
        elif 'flux-dev' in model_name:
            # FLUX-Dev - Good quality
            logger.debug("Using FLUX-Dev (balanced quality/speed)")
            output = replicate.run(
                model_name,
                input={
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "guidance_scale": 7.5,
                    "num_inference_steps": 50,
                    "output_format": "png",
                    "output_quality": 95
                }
            )
            
        elif 'flux-1.1-pro' in model_name:
            # FLUX-1.1-Pro - Best quality
            logger.debug("Using FLUX-1.1-Pro (premium quality)")
            output = replicate.run(
                model_name,
                input={
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "prompt_upsampling": True,
                    "output_format": "png",
                    "output_quality": 100,
                    "safety_tolerance": 2
                }
            )
            
        elif 'ideogram' in model_name:
            # Ideogram v3 Turbo - Great for typography
            logger.debug("Using Ideogram v3 Turbo (text optimized)")
            output = replicate.run(
                model_name,
                input={
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "magic_prompt_option": "Auto",
                    "output_format": "png"
                }
            )
            
        elif 'imagen-4' in model_name:
            # Google Imagen-4
            logger.debug("Using Google Imagen-4 (high quality)")
            output = replicate.run(
                model_name,
                input={
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "output_format": "png"
                }
            )
            
        else:
            # Generic fallback
            logger.debug(f"Using generic parameters for {model_name}")
            output = replicate.run(
                model_name,
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
            Complete artwork data
        """
        from app.core.ai.prompt_templates import get_prompt_for_style
        
        # Get optimized prompt for this style
        prompt_config = get_prompt_for_style(keyword, style)
        
        # Generate base image
        result = await self.generate_image(
            prompt=prompt_config['prompt'],
            style=style
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
        
        result['keyword'] = keyword
        
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
            List of generated artworks
        """
        results = []
        total = len(keywords) * len(styles)
        
        logger.info(f"🚀 Starting batch generation: {len(keywords)} keywords × {len(styles)} styles = {total} images")
        
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
        return results


# Singleton instance
_generator = None

def get_ai_generator(testing_mode: bool = False) -> AIArtGenerator:
    """Get or create AI generator instance"""
    global _generator
    if _generator is None:
        _generator = AIArtGenerator(testing_mode=testing_mode)
    return _generator
