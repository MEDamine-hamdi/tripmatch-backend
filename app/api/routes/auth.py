from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.token import Token, TokenType
from app.schemas.user import UserCreate, UserOut
from app.core.security import hash_password
from app.core.config import settings
from app.services.email import send_verification_email
from app.schemas.user import (
    UserCreate, UserOut, LoginRequest, TokenResponse,
    ForgotPasswordRequest, ResetPasswordRequest, MessageResponse,
)
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token

from app.services.email import send_verification_email, send_password_reset_email
router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # 1. Vérifier que l'email n'est pas déjà utilisé
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un compte existe déjà avec cet email.",
        )

    # 2. Créer l'utilisateur (inactif tant que l'email n'est pas vérifié)
    new_user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        is_verified=False,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 3. Générer le token de vérification email
    verification_token = Token(
        user_id=new_user.id,
        token=Token.generate_token_value(),
        token_type=TokenType.EMAIL_VERIFICATION,
        expires_at=Token.compute_expiry(hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS),
    )
    db.add(verification_token)
    db.commit()

    # 4. Envoyer l'email (simulé en mode console pour l'instant)
    send_verification_email(new_user.email, verification_token.token)

    return new_user


from datetime import datetime, timezone


@router.get("/verify-email", response_model=UserOut)
def verify_email(token: str, db: Session = Depends(get_db)):
    # 1. Chercher le token
    token_obj = db.query(Token).filter(
        Token.token == token,
        Token.token_type == TokenType.EMAIL_VERIFICATION,
    ).first()

    if not token_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de vérification invalide.",
        )

    # 2. Vérifier qu'il n'a pas déjà été utilisé
    if token_obj.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce lien de vérification a déjà été utilisé.",
        )

    # 3. Vérifier qu'il n'est pas expiré
    if token_obj.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce lien de vérification a expiré. Demandez-en un nouveau.",
        )

    # 4. Activer le compte
    user = db.query(User).filter(User.id == token_obj.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable.",
        )

    user.is_verified = True
    token_obj.used = True
    db.commit()
    db.refresh(user)

    return user

@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect.",
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Veuillez vérifier votre email avant de vous connecter.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte a été désactivé.",
        )

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    generic_message = MessageResponse(
        message="Si un compte existe avec cet email, un lien de réinitialisation a été envoyé."
    )

    user = db.query(User).filter(User.email == payload.email).first()

    # Réponse générique dans tous les cas, pour ne pas révéler si l'email existe (anti-énumération)
    if not user:
        return generic_message

    reset_token = Token(
        user_id=user.id,
        token=Token.generate_token_value(),
        token_type=TokenType.PASSWORD_RESET,
        expires_at=Token.compute_expiry(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES),
    )
    db.add(reset_token)
    db.commit()

    send_password_reset_email(user.email, reset_token.token)

    return generic_message


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    token_obj = db.query(Token).filter(
        Token.token == payload.token,
        Token.token_type == TokenType.PASSWORD_RESET,
    ).first()

    if not token_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de réinitialisation invalide.",
        )

    if token_obj.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce lien de réinitialisation a déjà été utilisé.",
        )

    if token_obj.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce lien de réinitialisation a expiré. Demandez-en un nouveau.",
        )

    user = db.query(User).filter(User.id == token_obj.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable.",
        )

    user.hashed_password = hash_password(payload.new_password)
    token_obj.used = True
    db.commit()

    return MessageResponse(message="Mot de passe réinitialisé avec succès.")