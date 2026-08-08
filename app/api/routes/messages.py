from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.db.session import get_db
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.message import MessageCreate, MessageOut, ConversationOut
from app.api.deps import get_current_user

router = APIRouter(tags=["Messagerie"])


def _get_or_create_conversation(db: Session, user_id_1: int, user_id_2: int) -> Conversation:
    """Récupère la conversation entre deux utilisateurs, ou la crée si elle n'existe pas."""
    user_a_id, user_b_id = sorted([user_id_1, user_id_2])

    conversation = db.query(Conversation).filter(
        Conversation.user_a_id == user_a_id,
        Conversation.user_b_id == user_b_id,
    ).first()

    if not conversation:
        conversation = Conversation(user_a_id=user_a_id, user_b_id=user_b_id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    return conversation


@router.post("/conversations/with/{other_user_id}", response_model=ConversationOut)
def start_conversation(
    other_user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Démarre (ou récupère) une conversation avec un autre utilisateur."""
    if other_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas démarrer une conversation avec vous-même.",
        )

    other_user = db.query(User).filter(User.id == other_user_id).first()
    if not other_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")

    conversation = _get_or_create_conversation(db, current_user.id, other_user_id)

    return _build_conversation_out(db, conversation, current_user.id)


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Liste toutes les conversations de l'utilisateur connecté, triées par activité récente."""
    conversations = db.query(Conversation).filter(
        or_(Conversation.user_a_id == current_user.id, Conversation.user_b_id == current_user.id)
    ).all()

    results = [_build_conversation_out(db, conv, current_user.id) for conv in conversations]
    results.sort(
        key=lambda c: c.last_message.created_at if c.last_message else c.created_at,
        reverse=True,
    )
    return results


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
def get_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Récupère tous les messages d'une conversation (polling côté client)."""
    conversation = _get_conversation_or_403(db, conversation_id, current_user.id)

    messages = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.created_at.asc()).all()

    # Marque comme lus les messages envoyés par l'autre utilisateur
    db.query(Message).filter(
        Message.conversation_id == conversation.id,
        Message.sender_id != current_user.id,
        Message.is_read == False,  # noqa: E712
    ).update({"is_read": True})
    db.commit()

    return messages


@router.post("/conversations/{conversation_id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
def send_message(
    conversation_id: int,
    payload: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Envoie un message dans une conversation."""
    conversation = _get_conversation_or_403(db, conversation_id, current_user.id)

    message = Message(
        conversation_id=conversation.id,
        sender_id=current_user.id,
        content=payload.content,
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    return message


def _get_conversation_or_403(db: Session, conversation_id: int, user_id: int) -> Conversation:
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation introuvable.")
    if user_id not in (conversation.user_a_id, conversation.user_b_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé à cette conversation.")
    return conversation


def _build_conversation_out(db: Session, conversation: Conversation, current_user_id: int) -> ConversationOut:
    other_user_id = (
        conversation.user_b_id if conversation.user_a_id == current_user_id else conversation.user_a_id
    )
    other_user = db.query(User).filter(User.id == other_user_id).first()

    last_message = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.created_at.desc()).first()

    unread_count = db.query(Message).filter(
        Message.conversation_id == conversation.id,
        Message.sender_id != current_user_id,
        Message.is_read == False,  # noqa: E712
    ).count()

    return ConversationOut(
        id=conversation.id,
        other_user=other_user,
        last_message=last_message,
        unread_count=unread_count,
        created_at=conversation.created_at,
    )