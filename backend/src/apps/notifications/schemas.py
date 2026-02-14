from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from src.apps.notifications.models import NotificationType

class NotificationBase(BaseModel):
    pass

class NotificationResponse(BaseModel):
    id: str
    recipient_id: str
    sender_id: Optional[str] = None
    type: NotificationType
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    is_read: bool
    content: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
