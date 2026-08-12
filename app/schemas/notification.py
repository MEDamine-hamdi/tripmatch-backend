from datetime import datetime
from pydantic import BaseModel
from app.models.notification import NotificationType


class NotificationOut(BaseModel):
    id: int
    type: NotificationType
    message: str
    trip_id: int | None = None
    reservation_id: int | None = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True