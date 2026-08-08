from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.token import Token, TokenType
from app.schemas.user import UserCreate, UserOut
from app.core.security import hash_password
from app.core.config import settings
from app.services.email import send_verification_email
from fastapi.responses import HTMLResponse
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


def _verification_page(success: bool, title: str, message: str) -> str:
    """Génère une page HTML autonome (pas de dépendance externe) pour le
    lien de vérification email, dans les couleurs de la marque TripMatch."""
    icon = "✓" if success else "✕"
    accent = "#16a34a" if success else "#dc2626"
    accent_bg = "#dcfce7" if success else "#fee2e2"

    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TripMatch — Vérification email</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            .card {{
                background: white;
                border-radius: 24px;
                padding: 40px 32px;
                max-width: 400px;
                width: 100%;
                text-align: center;
                box-shadow: 0 20px 50px rgba(0,0,0,0.2);
            }}
            .icon-circle {{
                width: 72px;
                height: 72px;
                border-radius: 50%;
                background: {accent_bg};
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 24px;
                font-size: 32px;
                color: {accent};
                font-weight: bold;
            }}
            h1 {{
                font-size: 22px;
                color: #111827;
                margin-bottom: 12px;
            }}
            p {{
                color: #6b7280;
                font-size: 15px;
                line-height: 1.5;
                margin-bottom: 8px;
            }}
            .brand {{
                margin-top: 28px;
                font-size: 13px;
                color: #9ca3af;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="icon-circle">{icon}</div>
            <h1>{title}</h1>
            <p>{message}</p>
            <div class="brand">TRIPMATCH</div>
        </div>
    </body>
    </html>
    """


@router.get("/verify-email", response_class=HTMLResponse)
def verify_email(token: str, db: Session = Depends(get_db)):
    # 1. Chercher le token
    token_obj = db.query(Token).filter(
        Token.token == token,
        Token.token_type == TokenType.EMAIL_VERIFICATION,
    ).first()

    if not token_obj:
        return HTMLResponse(
            _verification_page(False, "Lien invalide", "Ce lien de vérification n'existe pas ou a déjà été utilisé."),
            status_code=400,
        )

    # 2. Vérifier qu'il n'a pas déjà été utilisé
    if token_obj.used:
        return HTMLResponse(
            _verification_page(False, "Déjà vérifié", "Ce compte a déjà été activé. Vous pouvez vous connecter."),
            status_code=400,
        )

    # 3. Vérifier qu'il n'est pas expiré
    if token_obj.expires_at < datetime.now(timezone.utc):
        return HTMLResponse(
            _verification_page(False, "Lien expiré", "Ce lien de vérification a expiré. Demandez-en un nouveau depuis l'application."),
            status_code=400,
        )

    # 4. Activer le compte
    user = db.query(User).filter(User.id == token_obj.user_id).first()
    if not user:
        return HTMLResponse(
            _verification_page(False, "Utilisateur introuvable", "Impossible de retrouver ce compte."),
            status_code=404,
        )

    user.is_verified = True
    token_obj.used = True
    db.commit()

    return HTMLResponse(
        _verification_page(True, "Compte activé !", "Votre email a été vérifié avec succès. Vous pouvez maintenant vous connecter à TripMatch.")
    )


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


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Retourne les informations de l'utilisateur actuellement connecté."""
    return current_user