from datetime import datetime

from pydantic import BaseModel, field_validator


class RatingCreate(BaseModel):
    """Note laissée à un autre utilisateur (1 à 5 étoiles)."""
    score: int
    comment: str | None = None

    @field_validator("score")
    @classmethod
    def validate_score_range(cls, value: int) -> int:
        if value < 1 or value > 5:
            raise ValueError("La note doit être comprise entre 1 et 5.")
        return value

    @field_validator("comment")
    @classmethod
    def validate_comment_length(cls, value: str | None) -> str | None:
        if value is not None and len(value) > 500:
            raise ValueError("Le commentaire est trop long (max 500 caractères).")
        return value


class RatingOut(BaseModel):
    id: int
    rater_id: int
    rated_user_id: int
    score: int
    comment: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RatingSummary(BaseModel):
    """Résumé des notes reçues par un utilisateur (pour affichage sur son profil)."""
    average_score: float | None = None
    total_ratings: int = 0