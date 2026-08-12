from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.user import User
from app.models.trip import Trip, TripStatus
from app.models.reservation import Reservation, ReservationStatus
from app.schemas.reservation import ReservationCreate, ReservationOut
from app.schemas.trip import TripOut
from app.api.deps import get_current_user
from app.models.notification import Notification, NotificationType
router = APIRouter(tags=["Réservations"])


@router.post("/trips/{trip_id}/reservations", response_model=ReservationOut, status_code=status.HTTP_201_CREATED)
def create_reservation(
    trip_id: int,
    payload: ReservationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Réserver une ou plusieurs places sur un trajet publié (US-11)."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trajet introuvable.")

    if trip.status != TripStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ce trajet n'est plus disponible.")

    if trip.driver_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas réserver votre propre trajet.",
        )

    if payload.seats_booked > trip.available_seats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Seulement {trip.available_seats} place(s) disponible(s).",
        )

    # Empêche une double réservation active du même passager sur le même trajet
    existing = (
        db.query(Reservation)
        .filter(
            Reservation.trip_id == trip_id,
            Reservation.passenger_id == current_user.id,
            Reservation.status == ReservationStatus.CONFIRMED,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous avez déjà réservé une place sur ce trajet.",
        )

    reservation = Reservation(
        trip_id=trip_id,
        passenger_id=current_user.id,
        seats_booked=payload.seats_booked,
        status=ReservationStatus.CONFIRMED,
    )
    trip.available_seats -= payload.seats_booked

    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    # Notifie le conducteur qu'une nouvelle réservation a été faite sur son trajet
    seats_label = "place" if payload.seats_booked == 1 else "places"
    notification = Notification(
        user_id=trip.driver_id,
        type=NotificationType.NEW_RESERVATION,
        message=f"Nouvelle réservation : {payload.seats_booked} {seats_label} sur votre trajet "
                f"{trip.departure_city} → {trip.arrival_city}.",
        trip_id=trip.id,
        reservation_id=reservation.id,
    )
    db.add(notification)
    db.commit()

    return reservation


@router.delete("/reservations/{reservation_id}", response_model=ReservationOut)
def cancel_reservation(
    reservation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Annuler sa réservation avant le départ (US-12)."""
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Réservation introuvable.")

    if reservation.passenger_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez annuler que vos propres réservations.",
        )

    if reservation.status == ReservationStatus.CANCELLED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cette réservation est déjà annulée.")

    trip = db.query(Trip).filter(Trip.id == reservation.trip_id).first()
    if trip:
        trip.available_seats += reservation.seats_booked

    reservation.status = ReservationStatus.CANCELLED
    db.commit()
    db.refresh(reservation)

    # Notifie le conducteur que le passager a annulé sa réservation
    if trip:
        seats_label = "place" if reservation.seats_booked == 1 else "places"
        notification = Notification(
            user_id=trip.driver_id,
            type=NotificationType.RESERVATION_CANCELLED,
            message=f"Réservation annulée : {reservation.seats_booked} {seats_label} libérée(s) sur votre trajet "
                    f"{trip.departure_city} → {trip.arrival_city}.",
            trip_id=trip.id,
            reservation_id=reservation.id,
        )
        db.add(notification)
        db.commit()

    return reservation


@router.get("/reservations/me", response_model=list[ReservationOut])
def my_reservations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mes réservations en tant que passager (US-13)."""
    reservations = (
        db.query(Reservation)
        .options(joinedload(Reservation.trip))
        .filter(Reservation.passenger_id == current_user.id)
        .order_by(Reservation.created_at.desc())
        .all()
    )
    return reservations


@router.get("/trips/mine", response_model=list[TripOut])
def my_trips(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mes trajets publiés en tant que conducteur."""
    trips = (
        db.query(Trip)
        .filter(Trip.driver_id == current_user.id)
        .order_by(Trip.departure_datetime.desc())
        .all()
    )
    return trips