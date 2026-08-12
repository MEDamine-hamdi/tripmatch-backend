import re
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator
from app.models.user import DriverVerificationStatus, DriverDocumentType


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
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    profile_photo_url: str | None = None
    is_verified: bool
    is_active: bool
    is_admin: bool
    is_driver_verified: bool
    driver_verification_status: DriverVerificationStatus
    driver_document_type: DriverDocumentType | None = None
    driver_verification_rejection_reason: str | None = None
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


class ProfileUpdate(BaseModel):
    """Données reçues pour mettre à jour le profil (US-05)."""
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None


class PublicProfile(BaseModel):
    """Profil public d'un utilisateur, visible par les autres (US-15)."""
    id: int
    first_name: str | None = None
    last_name: str | None = None
    profile_photo_url: str | None = None
    is_verified: bool
    created_at: datetime  # utilisé pour calculer l'ancienneté du compte

    class Config:
        from_attributes = True


class DriverVerificationOut(BaseModel):
    """Statut de vérification conducteur de l'utilisateur connecté (US-17)."""
    is_driver_verified: bool
    driver_verification_status: DriverVerificationStatus
    driver_document_type: DriverDocumentType | None = None
    driver_document_url: str | None = None
    driver_verification_rejection_reason: str | None = None

    class Config:
        from_attributes = True


class DriverVerificationAdminOut(BaseModel):
    """Vue admin d'une demande de vérification conducteur, avec les infos
    de l'utilisateur nécessaires pour l'examiner (US-18)."""
    id: int
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    driver_verification_status: DriverVerificationStatus
    driver_document_type: DriverDocumentType | None = None
    driver_document_url: str | None = None
    driver_verification_rejection_reason: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class DriverVerificationReject(BaseModel):
    """Données reçues pour rejeter une demande de vérification (US-18)."""
    reason: str

class AdminUserOut(BaseModel):
    """Vue complète d'un utilisateur pour le panneau admin."""
    id: int
    email: str
    first_name: str | None
    last_name: str | None
    phone: str | None
    profile_photo_url: str | None
    is_verified: bool
    is_active: bool
    is_admin: bool
    is_driver_verified: bool
    driver_verification_status: str | None
    driver_document_type: str | None = None
    driver_document_url: str | None = None
    driver_verification_rejection_reason: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True