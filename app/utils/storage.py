# app/utils/storage.py
import boto3
import aiohttp
import os
from loguru import logger
from typing import Optional
import hashlib
from datetime import datetime


class StorageManager:
    """Handle image storage to AWS S3"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_S3_REGION', 'eu-west-2')
        )
        self.bucket = os.getenv('AWS_S3_BUCKET', 'ai-pod-platform-images')
        self.region = os.getenv('AWS_S3_REGION', 'eu-west-2')
        self.public_url = os.getenv('AWS_S3_PUBLIC_URL') or f'https://{self.bucket}.s3.{self.region}.amazonaws.com'
        
        logger.info(f"✅ Storage Manager initialized: {self.bucket}")
    
    async def download_and_upload(
        self,
        source_url: str,
        destination_path: str
    ) -> Optional[str]:
        """
        Download image from Replicate and upload to S3
        
        Args:
            source_url: Replicate's temporary URL
            destination_path: Path in S3 bucket (e.g., 'artwork/2024/10/image.png')
            
        Returns:
            Permanent public URL
        """
        try:
            logger.info(f"📥 Downloading from: {source_url[:80]}...")
            
            # Download from Replicate
            async with aiohttp.ClientSession() as session:
                async with session.get(source_url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    if response.status != 200:
                        logger.error(f"Failed to download image: HTTP {response.status}")
                        return None
                    
                    image_data = await response.read()
                    logger.info(f"✅ Downloaded {len(image_data)} bytes")
            
            # Generate filename with hash to avoid duplicates
            file_hash = hashlib.md5(image_data).hexdigest()[:8]
            timestamp = datetime.now().strftime('%Y/%m/%d')
            final_path = f"artwork/{timestamp}/{file_hash}.png"
            
            # Upload to S3
            logger.info(f"📤 Uploading to S3: {final_path}")
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=final_path,
                Body=image_data,
                ContentType='image/png',
                ACL='public-read',  # Make publicly readable
                CacheControl='max-age=31536000'  # Cache for 1 year
            )
            
            # Return public URL
            public_url = f"{self.public_url}/{final_path}"
            logger.info(f"✅ Image uploaded: {public_url}")
            
            return public_url
            
        except aiohttp.ClientError as e:
            logger.error(f"❌ Download error: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Upload error: {e}")
            return None
    
    def get_signed_upload_url(self, filename: str, expiration: int = 3600) -> str:
        """Generate pre-signed URL for direct uploads (optional)"""
        try:
            url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket,
                    'Key': f"uploads/{filename}",
                    'ContentType': 'image/png'
                },
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            logger.error(f"Error generating signed URL: {e}")
            return ""


# Singleton
storage_manager = StorageManager()
