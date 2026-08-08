from fastapi import APIRouter, Depends, HTTPException, status
from app.services.geocoding_service import geocode_city
from datetime import date, datetime, time
from sqlalchemy.orm import Session, joinedload
from app.db.session import get_db
from app.models.user import User
from app.models.trip import Trip
from app.schemas.trip import TripCreate, TripOut
from app.api.deps import get_current_user




router = APIRouter(prefix="/trips", tags=["Trajets"])


@router.post("", response_model=TripOut, status_code=status.HTTP_201_CREATED)
def create_trip(
    payload: TripCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Publie un nouveau trajet (US-06). Réservé aux conducteurs vérifiés."""

    # TODO (à activer une fois US-17/18 construites) :
    # if not current_user.is_driver_verified:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Seuls les conducteurs vérifiés peuvent publier un trajet.",
    #     )

    departure_coords = geocode_city(payload.departure_city)
    arrival_coords = geocode_city(payload.arrival_city)

    new_trip = Trip(
        driver_id=current_user.id,
        departure_city=payload.departure_city,
        departure_lat=departure_coords[0] if departure_coords else None,
        departure_lon=departure_coords[1] if departure_coords else None,
        arrival_city=payload.arrival_city,
        arrival_lat=arrival_coords[0] if arrival_coords else None,
        arrival_lon=arrival_coords[1] if arrival_coords else None,
        departure_datetime=payload.departure_datetime,
        price=payload.price,
        total_seats=payload.total_seats,
        available_seats=payload.total_seats,
    )

    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)

    # Recharge avec la relation driver pour que TripOut puisse la sérialiser
    db.refresh(new_trip, attribute_names=["driver"])

    return new_trip

@router.get("", response_model=list[TripOut])
def search_trips(
    departure_city: str | None = None,
    arrival_city: str | None = None,
    departure_date: date | None = None,
    db: Session = Depends(get_db),
):
    """Recherche des trajets par ville de départ/arrivée et date (US-07)."""
    query = db.query(Trip).options(joinedload(Trip.driver)).filter(Trip.status == "active")

    if departure_city:
        query = query.filter(Trip.departure_city.ilike(f"%{departure_city}%"))

    if arrival_city:
        query = query.filter(Trip.arrival_city.ilike(f"%{arrival_city}%"))

    if departure_date:
        start_of_day = datetime.combine(departure_date, time.min)
        end_of_day = datetime.combine(departure_date, time.max)
        query = query.filter(Trip.departure_datetime.between(start_of_day, end_of_day))

    trips = query.order_by(Trip.departure_datetime.asc()).all()

    return trips