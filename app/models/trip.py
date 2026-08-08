import enum
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Float, DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class TripStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    driver_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Départ
    departure_city: Mapped[str] = mapped_column(String(150), nullable=False)
    departure_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    departure_lon: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Arrivée
    arrival_city: Mapped[str] = mapped_column(String(150), nullable=False)
    arrival_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    arrival_lon: Mapped[float | None] = mapped_column(Float, nullable=True)

    departure_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    price: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    total_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    available_seats: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[TripStatus] = mapped_column(Enum(TripStatus), default=TripStatus.ACTIVE, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    driver = relationship("User", backref="trips_as_driver")