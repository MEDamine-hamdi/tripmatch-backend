import enum
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class DriverVerificationStatus(str, enum.Enum):
    UNSUBMITTED = "unsubmitted"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class DriverDocumentType(str, enum.Enum):
    DRIVING_LICENSE = "driving_license"
    NATIONAL_ID = "national_id"
    STUDENT_CARD = "student_card"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Informations de profil (US-05)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    profile_photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Statut du compte
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Vérification d'identité conducteur (US-17/18)
    is_driver_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    driver_verification_status: Mapped[DriverVerificationStatus] = mapped_column(
        Enum(DriverVerificationStatus), default=DriverVerificationStatus.UNSUBMITTED, nullable=False
    )
    driver_document_type: Mapped[DriverDocumentType | None] = mapped_column(
        Enum(DriverDocumentType), nullable=True
    )
    driver_document_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    driver_verification_rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )