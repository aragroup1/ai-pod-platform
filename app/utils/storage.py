import boto3
import aiohttp
import os
from loguru import logger
from typing import Optional

class StorageManager:
    """Handle image storage to Cloudflare R2"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=os.getenv('CLOUDFLARE_R2_ENDPOINT'),
            aws_access_key_id=os.getenv('CLOUDFLARE_R2_ACCESS_KEY'),
            aws_secret_access_key=os.getenv('CLOUDFLARE_R2_SECRET_KEY'),
            region_name='auto'
        )
        self.bucket = os.getenv('CLOUDFLARE_R2_BUCKET', 'pod-assets')
        self.public_url = os.getenv('CLOUDFLARE_R2_PUBLIC_URL')
    
    async def download_and_upload(
        self,
        source_url: str,
        destination_path: str
    ) -> Optional[str]:
        """
        Download image from Replicate and upload to R2
        
        Args:
            source_url: Replicate's temporary URL
            destination_path: Path in R2 bucket (e.g., 'artwork/123.png')
            
        Returns:
            Permanent public URL
        """
        try:
            # Download from Replicate
            async with aiohttp.ClientSession() as session:
                async with session.get(source_url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to download image: {response.status}")
                        return None
                    
                    image_data = await response.read()
            
            # Upload to R2
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=destination_path,
                Body=image_data,
                ContentType='image/png',
                ACL='public-read'
            )
            
            # Return public URL
            public_url = f"{self.public_url}/{destination_path}"
            logger.info(f"✅ Image uploaded to: {public_url}")
            
            return public_url
            
        except Exception as e:
            logger.error(f"❌ Error uploading image: {e}")
            return None

storage_manager = StorageManager()
