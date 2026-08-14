from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.user import User
from app.models.rating import Rating
from app.schemas.rating import RatingCreate, RatingOut, RatingSummary
from app.api.deps import get_current_user

router = APIRouter(tags=["Notation"])


@router.post("/users/{user_id}/ratings", response_model=RatingOut, status_code=status.HTTP_201_CREATED)
def rate_user(
    user_id: int,
    payload: RatingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Note un autre utilisateur. Si une note existe déjà pour cette paire, elle est mise à jour."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas vous noter vous-même.",
        )

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")

    existing_rating = db.query(Rating).filter(
        Rating.rater_id == current_user.id,
        Rating.rated_user_id == user_id,
    ).first()

    if existing_rating:
        existing_rating.score = payload.score
        existing_rating.comment = payload.comment
        db.commit()
        db.refresh(existing_rating)
        return existing_rating

    new_rating = Rating(
        rater_id=current_user.id,
        rated_user_id=user_id,
        score=payload.score,
        comment=payload.comment,
    )
    db.add(new_rating)
    db.commit()
    db.refresh(new_rating)
    return new_rating


@router.get("/users/{user_id}/ratings", response_model=list[RatingOut])
def get_user_ratings(user_id: int, db: Session = Depends(get_db)):
    """Liste toutes les notes reçues par un utilisateur."""
    ratings = db.query(Rating).filter(Rating.rated_user_id == user_id).order_by(Rating.created_at.desc()).all()
    return ratings


@router.get("/users/{user_id}/ratings/summary", response_model=RatingSummary)
def get_rating_summary(user_id: int, db: Session = Depends(get_db)):
    """Note moyenne et nombre total de notes reçues (pour affichage compact sur le profil)."""
    result = db.query(
        func.avg(Rating.score),
        func.count(Rating.id),
    ).filter(Rating.rated_user_id == user_id).first()

    average, count = result
    return RatingSummary(
        average_score=round(float(average), 1) if average is not None else None,
        total_ratings=count or 0,
    )


@router.get("/users/{user_id}/ratings/mine", response_model=RatingOut | None)
def get_my_rating_for_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ma propre note donnée à cet utilisateur, si elle existe (pour pré-remplir le formulaire)."""
    rating = db.query(Rating).filter(
        Rating.rater_id == current_user.id,
        Rating.rated_user_id == user_id,
    ).first()
    return rating