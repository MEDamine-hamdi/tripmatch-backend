from fastapi import APIRouter, Depends, HTTPException, status
from app.services.geocoding_service import geocode_city
from datetime import date, datetime, time
from sqlalchemy.orm import Session, joinedload
from app.db.session import get_db
from app.models.user import User
from app.models.trip import Trip, TripStatus
from app.schemas.trip import TripCreate, TripOut
from app.api.deps import get_current_user
from app.models.reservation import Reservation, ReservationStatus
from app.models.notification import Notification, NotificationType



router = APIRouter(prefix="/trips", tags=["Trajets"])


@router.post("", response_model=TripOut, status_code=status.HTTP_201_CREATED)
def create_trip(
    payload: TripCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Publie un nouveau trajet (US-06). Réservé aux conducteurs vérifiés."""

    if not current_user.is_driver_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les conducteurs vérifiés peuvent publier un trajet.",
        )

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

@router.delete("/{trip_id}", response_model=TripOut)
def cancel_trip(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Annule un trajet publié (US-XX). Réservé au conducteur propriétaire.
    Annule aussi automatiquement toutes les réservations actives liées,
    et notifie chaque passager concerné."""
    trip = db.query(Trip).options(joinedload(Trip.driver)).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trajet introuvable.")

    if trip.driver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez annuler que vos propres trajets.",
        )

    if trip.status == TripStatus.CANCELLED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ce trajet est déjà annulé.")

    # Annule toutes les réservations actives liées à ce trajet
    active_reservations = (
        db.query(Reservation)
        .filter(Reservation.trip_id == trip_id, Reservation.status == ReservationStatus.CONFIRMED)
        .all()
    )

    for reservation in active_reservations:
        reservation.status = ReservationStatus.CANCELLED
        notification = Notification(
            user_id=reservation.passenger_id,
            type=NotificationType.TRIP_CANCELLED,
            message=f"Le trajet {trip.departure_city} → {trip.arrival_city} du "
                    f"{trip.departure_datetime.strftime('%d/%m/%Y à %Hh%M')} a été annulé par le conducteur.",
            trip_id=trip.id,
            reservation_id=reservation.id,
        )
        db.add(notification)

    trip.status = TripStatus.CANCELLED

    db.commit()
    db.refresh(trip)

    return trip