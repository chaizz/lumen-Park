import enum
from sqlalchemy import Column, String, Boolean, ForeignKey, Enum, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.base import Base
import uuid

class NotificationType(str, enum.Enum):
    LIKE = "like"
    COMMENT = "comment"
    FOLLOW = "follow"
    SYSTEM = "system"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recipient_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    sender_id = Column(String(36), ForeignKey("users.id"), nullable=True) # System messages might not have sender
    
    type = Column(Enum(NotificationType), nullable=False)
    
    # Optional references
    post_id = Column(String(36), ForeignKey("posts.id"), nullable=True)
    comment_id = Column(String(36), ForeignKey("comments.id"), nullable=True)
    
    content = Column(Text, nullable=True) # Preview text or system message
    is_read = Column(Boolean, default=False, index=True)
    
    created_at = Column(DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False)
    
    # Relationships
    recipient = relationship("User", foreign_keys=[recipient_id], backref="notifications_received")
    sender = relationship("User", foreign_keys=[sender_id], backref="notifications_sent")
    post = relationship("Post")
    comment = relationship("Comment")
