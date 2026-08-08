from datetime import datetime

from pydantic import BaseModel, field_validator


class MessageCreate(BaseModel):
    """Contenu d'un nouveau message."""
    content: str

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Le message ne peut pas être vide.")
        if len(value) > 2000:
            raise ValueError("Le message est trop long (max 2000 caractères).")
        return value.strip()


class MessageOut(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    content: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationParticipant(BaseModel):
    id: int
    email: str
    first_name: str | None = None
    last_name: str | None = None
    profile_photo_url: str | None = None

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: int
    other_user: ConversationParticipant  # l'autre participant, du point de vue de l'utilisateur connecté
    last_message: MessageOut | None = None
    unread_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True