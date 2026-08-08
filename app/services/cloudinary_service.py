import cloudinary
import cloudinary.uploader

from app.core.config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)


def upload_profile_photo(file_bytes: bytes, user_id: int) -> str:
    """Upload une photo de profil sur Cloudinary et retourne l'URL sécurisée."""
    result = cloudinary.uploader.upload(
        file_bytes,
        folder="tripmatch/profile_photos",
        public_id=f"user_{user_id}",
        overwrite=True,
        resource_type="image",
        transformation=[
            {"width": 500, "height": 500, "crop": "fill", "gravity": "face"},
        ],
    )
    return result["secure_url"]