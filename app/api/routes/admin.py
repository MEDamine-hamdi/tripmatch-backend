from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User, DriverVerificationStatus
from app.models.notification import Notification, NotificationType
from app.schemas.user import DriverVerificationAdminOut, DriverVerificationReject, AdminUserOut
from app.api.deps import get_current_user

router = APIRouter(prefix="/admin", tags=["Administration"])


def _require_admin(current_user: User) -> None:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs.",
        )


@router.get("/driver-verifications", response_model=list[DriverVerificationAdminOut])
def list_pending_verifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Liste les demandes de vérification conducteur en attente (US-18)."""
    _require_admin(current_user)
    users = (
        db.query(User)
        .filter(User.driver_verification_status == DriverVerificationStatus.PENDING)
        .order_by(User.created_at.asc())
        .all()
    )
    return users


@router.patch("/driver-verifications/{user_id}/approve", response_model=DriverVerificationAdminOut)
def approve_driver_verification(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Approuve la demande de vérification conducteur d'un utilisateur (US-18)."""
    _require_admin(current_user)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")

    if user.driver_verification_status != DriverVerificationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette demande n'est pas en attente de validation.",
        )

    user.driver_verification_status = DriverVerificationStatus.APPROVED
    user.is_driver_verified = True
    user.driver_verification_rejection_reason = None

    notification = Notification(
        user_id=user.id,
        type=NotificationType.DRIVER_VERIFICATION_APPROVED,
        message="Votre vérification conducteur a été approuvée ! Vous pouvez maintenant publier des trajets.",
    )
    db.add(notification)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/driver-verifications/{user_id}/reject", response_model=DriverVerificationAdminOut)
def reject_driver_verification(
    user_id: int,
    payload: DriverVerificationReject,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Rejette la demande de vérification conducteur d'un utilisateur, avec motif (US-18)."""
    _require_admin(current_user)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")

    if user.driver_verification_status != DriverVerificationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette demande n'est pas en attente de validation.",
        )

    user.driver_verification_status = DriverVerificationStatus.REJECTED
    user.is_driver_verified = False
    user.driver_verification_rejection_reason = payload.reason

    notification = Notification(
        user_id=user.id,
        type=NotificationType.DRIVER_VERIFICATION_REJECTED,
        message=f"Votre vérification conducteur a été refusée. Motif : {payload.reason}",
    )
    db.add(notification)
    db.commit()
    db.refresh(user)
    return user

@router.get("/users", response_model=list[AdminUserOut])
def list_all_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Liste tous les utilisateurs de la plateforme (panneau admin)."""
    _require_admin(current_user)
    users = db.query(User).order_by(User.created_at.desc()).all()
    return users


@router.patch("/users/{user_id}/block", response_model=AdminUserOut)
def block_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bloque un utilisateur (désactive son compte)."""
    _require_admin(current_user)

    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas bloquer votre propre compte.",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")

    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/unblock", response_model=AdminUserOut)
def unblock_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Débloque un utilisateur (réactive son compte)."""
    _require_admin(current_user)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")

    user.is_active = True
    db.commit()
    db.refresh(user)
    return user