"""Cloudinary service for image uploads"""
import cloudinary
import cloudinary.uploader
from app.core.config import settings
from typing import BinaryIO
import tempfile
import os

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)


class CloudinaryService:
    async def upload_image(self, file: BinaryIO, folder: str = "uploads") -> str:
        """Upload image to Cloudinary and return URL"""
        try:
            # Save to temp file first
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                temp_file.write(file.read())
                temp_path = temp_file.name

            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                temp_path,
                folder=folder,
                resource_type="image"
            )

            # Clean up temp file
            os.unlink(temp_path)

            return result["secure_url"]
        except Exception as e:
            raise Exception(f"Cloudinary upload failed: {str(e)}")


cloudinary_service = CloudinaryService()
