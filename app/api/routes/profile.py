from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserOut, ProfileUpdate
from app.api.deps import get_current_user
from app.services.cloudinary_service import upload_profile_photo
from app.schemas.user import UserOut, ProfileUpdate, PublicProfile
router = APIRouter(prefix="/profile", tags=["Profil"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE_MB = 5


@router.patch("", response_model=UserOut)
def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Met à jour le prénom/nom de l'utilisateur connecté (US-05)."""
    if payload.first_name is not None:
        current_user.first_name = payload.first_name
    if payload.last_name is not None:
        current_user.last_name = payload.last_name
    if payload.phone is not None:
        current_user.phone = payload.phone

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/photo", response_model=UserOut)
async def upload_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload/remplace la photo de profil sur Cloudinary (US-05)."""
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format d'image non supporté. Utilisez JPEG, PNG ou WebP.",
        )

    file_bytes = await file.read()

    if len(file_bytes) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"L'image ne doit pas dépasser {MAX_IMAGE_SIZE_MB} Mo.",
        )

    photo_url = upload_profile_photo(file_bytes, current_user.id)

    current_user.profile_photo_url = photo_url
    db.commit()
    db.refresh(current_user)

    return current_user

@router.get("/{user_id}", response_model=PublicProfile)
def get_public_profile(user_id: int, db: Session = Depends(get_db)):
    """Profil public d'un utilisateur, consultable par tous (US-15)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")
    return user