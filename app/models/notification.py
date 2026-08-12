import enum
from datetime import datetime, timezone
from sqlalchemy import Integer, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class NotificationType(str, enum.Enum):
    NEW_RESERVATION = "new_reservation"
    RESERVATION_CANCELLED = "reservation_cancelled"
    TRIP_CANCELLED = "trip_cancelled"
    DRIVER_VERIFICATION_APPROVED = "driver_verification_approved"
    DRIVER_VERIFICATION_REJECTED = "driver_verification_rejected"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType), nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    trip_id: Mapped[int | None] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), nullable=True)
    reservation_id: Mapped[int | None] = mapped_column(
        ForeignKey("reservations.id", ondelete="CASCADE"), nullable=True
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user = relationship("User", backref="notifications")
    trip = relationship("Trip")
    reservation = relationship("Reservation")