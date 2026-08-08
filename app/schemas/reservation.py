from datetime import datetime

from pydantic import BaseModel, field_validator

from app.models.reservation import ReservationStatus
from app.schemas.trip import TripOut


class ReservationCreate(BaseModel):
    """US-11 — nombre de places à réserver."""
    seats_booked: int = 1

    @field_validator("seats_booked")
    @classmethod
    def validate_seats(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Le nombre de places doit être au moins 1.")
        return value


class ReservationOut(BaseModel):
    id: int
    trip_id: int
    passenger_id: int
    seats_booked: int
    status: ReservationStatus
    created_at: datetime
    trip: TripOut  # détails du trajet inclus, pour affichage direct côté app

    class Config:
        from_attributes = True