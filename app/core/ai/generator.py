import replicate
import os
from typing import Dict, Optional, Literal
from loguru import logger
import asyncio

ArtStyle = Literal[
    'typography', 'abstract', 'minimalist', 'vintage',
    'photography', 'watercolor', 'line_art', 'botanical'
]


class AIArtGenerator:
    """Multi-model AI art generation for POD"""
    
    # Model selection based on style and quality needs
    MODEL_STRATEGY = {
        'typography': {
            'model': 'ideogram-ai/ideogram-v3-turbo',
            'cost': 0.05,
            'reason': 'Best for text rendering'
        },
        'abstract': {
            'model': 'black-forest-labs/flux-1.1-pro',
            'cost': 0.04,
            'reason': 'High quality for premium abstract'
        },
        'minimalist': {
            'model': 'black-forest-labs/flux-1.1-pro',
            'cost': 0.04,
            'reason': 'Clean, professional results'
        },
        'vintage': {
            'model': 'black-forest-labs/flux-1.1-pro',
            'cost': 0.04,
            'reason': 'Great texture and detail'
        },
        'photography': {
            'model': 'black-forest-labs/flux-1.1-pro',
            'cost': 0.04,
            'reason': 'Photorealistic quality'
        },
        'watercolor': {
            'model': 'black-forest-labs/flux-dev',
            'cost': 0.03,
            'reason': 'Good artistic quality, cheaper'
        },
        'line_art': {
            'model': 'black-forest-labs/flux-dev',
            'cost': 0.03,
            'reason': 'Simple style, dev model sufficient'
        },
        'botanical': {
            'model': 'black-forest-labs/flux-dev',
            'cost': 0.03,
            'reason': 'Good detail at lower cost'
        }
    }
    
    # For testing phase, use cheap model
    TESTING_MODEL = 'black-forest-labs/flux-schnell'
    TESTING_COST = 0.003
    
    def __init__(self, testing_mode: bool = False):
        """
        Initialize AI Art Generator
        
        Args:
            testing_mode: If True, use cheap FLUX-Schnell for all generations
        """
        self.api_token = os.getenv('REPLICATE_API_TOKEN')
        self.testing_mode = testing_mode
        
        if not self.api_token:
            logger.error("REPLICATE_API_TOKEN not found!")
            raise ValueError("Replicate API token required")
        
        # Set up Replicate client
        os.environ['REPLICATE_API_TOKEN'] = self.api_token
        
        logger.info(f"AI Generator initialized (testing_mode={testing_mode})")
    
    def get_model_for_style(self, style: ArtStyle) -> tuple[str, float]:
        """
        Get the best model for a given art style
        
        Returns:
            (model_name, estimated_cost)
        """
        if self.testing_mode:
            return self.TESTING_MODEL, self.TESTING_COST
        
        strategy = self.MODEL_STRATEGY.get(style)
        if not strategy:
            # Default to FLUX-1.1-Pro
            return 'black-forest-labs/flux-1.1-pro', 0.04
        
        return strategy['model'], strategy['cost']
    
    async def generate_image(
        self,
        prompt: str,
        style: ArtStyle,
        aspect_ratio: str = "1:1",
        guidance_scale: float = 7.5,
        num_inference_steps: int = 50
    ) -> Dict:
        """
        Generate AI artwork
        
        Args:
            prompt: Text description
            style: Art style category
            aspect_ratio: Image ratio (1:1, 16:9, 9:16, etc.)
            guidance_scale: How closely to follow prompt (3-15)
            num_inference_steps: Quality vs speed (20-100)
            
        Returns:
            Dict with image_url, cost, model_used
        """
        model_name, estimated_cost = self.get_model_for_style(style)
        
        logger.info(f"Generating {style} image with {model_name}")
        logger.debug(f"Prompt: {prompt}")
        
        try:
            # Run generation in thread pool (Replicate SDK is synchronous)
            loop = asyncio.get_event_loop()
            output = await loop.run_in_executor(
                None,
                self._generate_sync,
                model_name,
                prompt,
                aspect_ratio,
                guidance_scale,
                num_inference_steps
            )
            
            # Extract image URL from output
            if isinstance(output, list) and len(output) > 0:
                image_url = output[0]
            else:
                image_url = output
            
            result = {
                'image_url': str(image_url),
                'model_used': model_name,
                'estimated_cost': estimated_cost,
                'style': style,
                'prompt': prompt
            }
            
            logger.info(f"✅ Image generated successfully: {image_url}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            raise
    
    def _generate_sync(
        self,
        model_name: str,
        prompt: str,
        aspect_ratio: str,
        guidance_scale: float,
        num_inference_steps: int
    ):
        """Synchronous generation (runs in executor)"""
        
        # Different models have different parameter formats
        if 'flux-schnell' in model_name:
            # FLUX-Schnell (fast, cheap)
            output = replicate.run(
                model_name,
                input={
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "num_inference_steps": 4,  # Schnell only needs 4 steps
                    "output_format": "png",
                    "output_quality": 90
                }
            )
        elif 'flux-dev' in model_name:
            # FLUX-Dev
            output = replicate.run(
                model_name,
                input={
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "guidance_scale": guidance_scale,
                    "num_inference_steps": num_inference_steps,
                    "output_format": "png",
                    "output_quality": 95
                }
            )
        elif 'flux-1.1-pro' in model_name:
            # FLUX-1.1-Pro
            output = replicate.run(
                model_name,
                input={
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "prompt_upsampling": True,  # Better prompt interpretation
                    "output_format": "png",
                    "output_quality": 100,
                    "safety_tolerance": 2  # Less restrictive for art
                }
            )
        elif 'ideogram' in model_name:
            # Ideogram v3 Turbo (great for typography)
            output = replicate.run(
                model_name,
                input={
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "magic_prompt_option": "Auto",  # Let AI enhance prompt
                    "output_format": "png"
                }
            )
        else:
            # Generic fallback
            output = replicate.run(
                model_name,
                input={"prompt": prompt}
            )
        
        return output
    
    async def upscale_image(
        self,
        image_url: str,
        scale: int = 4
    ) -> Dict:
        """
        Upscale image for print quality
        
        Args:
            image_url: URL of image to upscale
            scale: Upscale factor (2 or 4)
            
        Returns:
            Dict with upscaled_url, cost
        """
        logger.info(f"Upscaling image {scale}x")
        
        try:
            loop = asyncio.get_event_loop()
            output = await loop.run_in_executor(
                None,
                replicate.run,
                "topazlabs/image-upscale",
                {
                    "input": {
                        "image": image_url,
                        "scale": scale,
                        "face_enhance": False  # Not needed for art
                    }
                }
            )
            
            result = {
                'upscaled_url': str(output),
                'estimated_cost': 0.02,
                'scale': scale
            }
            
            logger.info(f"✅ Image upscaled successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error upscaling image: {e}")
            raise
    
    async def generate_with_upscale(
        self,
        prompt: str,
        style: ArtStyle,
        upscale: bool = True
    ) -> Dict:
        """
        Generate and optionally upscale in one call
        
        Args:
            prompt: Text description
            style: Art style
            upscale: Whether to upscale for print
            
        Returns:
            Dict with both original and upscaled URLs
        """
        # Generate base image
        result = await self.generate_image(prompt, style)
        
        total_cost = result['estimated_cost']
        
        # Upscale if needed
        if upscale:
            upscaled = await self.upscale_image(result['image_url'], scale=4)
            result['upscaled_url'] = upscaled['upscaled_url']
            total_cost += upscaled['estimated_cost']
        
        result['total_cost'] = total_cost
        
        return result


# Usage example
async def test_generator():
    """Test the AI generator"""
    generator = AIArtGenerator(testing_mode=False)
    
    result = await generator.generate_image(
        prompt="Minimalist mountain landscape, clean lines, sunset colors",
        style='minimalist'
    )
    
    print(f"Generated: {result['image_url']}")
    print(f"Cost: ${result['estimated_cost']}")
