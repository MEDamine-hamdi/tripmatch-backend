import enum
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import String, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class TokenType(str, enum.Enum):
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"


class Token(Base):
    __tablename__ = "tokens"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    token_type: Mapped[TokenType] = mapped_column(Enum(TokenType), nullable=False)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    @staticmethod
    def generate_token_value() -> str:
        """Génère une chaîne aléatoire sécurisée pour servir de token."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def compute_expiry(hours: int = 0, minutes: int = 0) -> datetime:
        """Calcule la date d'expiration à partir de maintenant."""
        return datetime.now(timezone.utc) + timedelta(hours=hours, minutes=minutes)
