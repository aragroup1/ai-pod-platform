import boto3
from botocore.exceptions import ClientError
import os
from datetime import datetime
import mimetypes
from typing import Optional, Dict
import aiohttp
import asyncio
from loguru import logger


class S3StorageManager:
    """
    AWS S3 Storage Manager for AI POD Platform
    Handles secure image storage with private bucket and pre-signed URLs
    """
    
    def __init__(self):
        """Initialize S3 client with credentials from environment variables"""
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        
        if not all([self.aws_access_key, self.aws_secret_key, self.bucket_name]):
            logger.error("❌ Missing AWS credentials in environment variables")
            raise ValueError("Missing required AWS credentials in environment variables")
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.region
        )
        
        logger.info(f"✅ S3 Storage Manager initialized for bucket: {self.bucket_name}")
    
    async def download_and_upload_from_url(
        self,
        source_url: str,
        folder: str = 'products',
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Download image from URL (e.g., Replicate) and upload to S3
        
        Args:
            source_url: URL of the image to download
            folder: Folder in S3 bucket
            metadata: Optional metadata to attach
            
        Returns:
            S3 key (path) if successful
        """
        try:
            logger.info(f"📥 Downloading image from: {source_url[:100]}...")
            
            # Download image
            async with aiohttp.ClientSession() as session:
                async with session.get(source_url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    if response.status != 200:
                        logger.error(f"❌ Failed to download image: HTTP {response.status}")
                        return None
                    
                    image_data = await response.read()
                    logger.info(f"✅ Downloaded {len(image_data)} bytes")
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            filename = f"image_{timestamp}.png"
            
            # Upload to S3
            s3_key = await self.upload_image(
                image_data=image_data,
                filename=filename,
                folder=folder,
                metadata=metadata
            )
            
            return s3_key
            
        except Exception as e:
            logger.error(f"❌ Error in download_and_upload: {e}")
            return None
    
    async def upload_image(
        self, 
        image_data: bytes, 
        filename: str, 
        folder: str = 'products',
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Upload image to S3 bucket
        
        Returns S3 key (path), not URL
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_name, ext = os.path.splitext(filename)
            unique_filename = f"{base_name}_{timestamp}{ext}"
            s3_key = f"{folder}/{unique_filename}"
            
            content_type = mimetypes.guess_type(filename)[0] or 'image/png'
            
            upload_params = {
                'Bucket': self.bucket_name,
                'Key': s3_key,
                'Body': image_data,
                'ContentType': content_type
            }
            
            if metadata:
                upload_params['Metadata'] = {k: str(v) for k, v in metadata.items()}
            
            # Run sync S3 upload in executor to not block event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3_client.put_object(**upload_params)
            )
            
            logger.info(f"✅ Uploaded to S3: {s3_key}")
            return s3_key
            
        except Exception as e:
            logger.error(f"❌ Error uploading to S3: {e}")
            return None
    
    def get_presigned_url(
        self, 
        s3_key: str, 
        expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate a pre-signed URL for private S3 object
        
        Args:
            s3_key: S3 object key (path)
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Pre-signed URL if successful
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            return url
            
        except Exception as e:
            logger.error(f"❌ Error generating pre-signed URL: {e}")
            return None
    
    def delete_image(self, s3_key: str) -> bool:
        """Delete image from S3 bucket"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"✅ Deleted from S3: {s3_key}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deleting from S3: {e}")
            return False
    
    def check_image_exists(self, s3_key: str) -> bool:
        """Check if image exists in S3 bucket"""
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"❌ Error checking S3 object: {e}")
            return False


# Global instance
_storage_manager = None

def get_storage_manager() -> S3StorageManager:
    """Get or create global S3 storage manager instance"""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = S3StorageManager()
    return _storage_manager
