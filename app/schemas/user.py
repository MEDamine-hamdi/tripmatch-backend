import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    """Données reçues à l'inscription (US-01)."""
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères.")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Le mot de passe doit contenir au moins une majuscule.")
        if not re.search(r"[a-z]", value):
            raise ValueError("Le mot de passe doit contenir au moins une minuscule.")
        if not re.search(r"[0-9]", value):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre.")
        return value


class UserOut(BaseModel):
    """Données renvoyées au client (jamais le mot de passe)."""
    id: int
    email: EmailStr
    is_verified: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    """Données reçues à la connexion (US-03)."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Réponse renvoyée après une connexion réussie."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class ForgotPasswordRequest(BaseModel):
    """Données reçues pour demander une réinitialisation (US-04)."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Données reçues pour effectuer la réinitialisation (US-04)."""
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password_complexity(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères.")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Le mot de passe doit contenir au moins une majuscule.")
        if not re.search(r"[a-z]", value):
            raise ValueError("Le mot de passe doit contenir au moins une minuscule.")
        if not re.search(r"[0-9]", value):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre.")
        return value


class MessageResponse(BaseModel):
    """Réponse générique avec un message de confirmation."""
    message: str