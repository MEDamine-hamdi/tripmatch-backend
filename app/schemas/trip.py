from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator
from app.schemas.user import PublicProfile
from app.models.trip import TripStatus


class TripCreate(BaseModel):
    """Données reçues pour publier un trajet (US-06)."""
    departure_city: str
    arrival_city: str
    departure_datetime: datetime
    price: Decimal
    total_seats: int

    @field_validator("departure_city", "arrival_city")
    @classmethod
    def validate_city_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Le nom de la ville ne peut pas être vide.")
        return value.strip()

    @field_validator("price")
    @classmethod
    def validate_price_positive(cls, value: Decimal) -> Decimal:
        if value < 0:
            raise ValueError("Le prix ne peut pas être négatif.")
        return value

    @field_validator("total_seats")
    @classmethod
    def validate_seats_range(cls, value: int) -> int:
        if value < 1 or value > 8:
            raise ValueError("Le nombre de places doit être entre 1 et 8.")
        return value

    @field_validator("departure_datetime")
    @classmethod
    def validate_departure_in_future(cls, value: datetime) -> datetime:
        # On compare en naïf pour éviter les soucis de fuseau horaire côté client
        now = datetime.now(value.tzinfo) if value.tzinfo else datetime.now()
        if value <= now:
            raise ValueError("La date de départ doit être dans le futur.")
        return value


class TripOut(BaseModel):
    """Données renvoyées pour un trajet."""
    id: int
    driver_id: int
    driver: PublicProfile
    departure_city: str
    departure_lat: float | None
    departure_lon: float | None
    arrival_city: str
    arrival_lat: float | None
    arrival_lon: float | None
    departure_datetime: datetime
    price: Decimal
    total_seats: int
    available_seats: int
    status: TripStatus
    created_at: datetime

    class Config:
        from_attributes = True