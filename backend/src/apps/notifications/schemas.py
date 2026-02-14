from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from src.apps.notifications.models import NotificationType
from src.apps.users.schemas import UserResponse

class NotificationBase(BaseModel):
    recipient_id: str
    sender_id: Optional[str] = None
    type: NotificationType
    post_id: Optional[str] = None
    comment_id: Optional[str] = None
    content: Optional[str] = None
    is_read: bool = False

class NotificationCreate(NotificationBase):
    pass

class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None

class NotificationResponse(NotificationBase):
    id: str
    created_at: Optional[datetime] = None
    sender: Optional[UserResponse] = None
    # We could include post preview here if needed, but let's keep it simple for now
    
    model_config = ConfigDict(from_attributes=True)

class UnreadCount(BaseModel):
    count: int