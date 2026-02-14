from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref
from src.database.base import Base
import uuid
from datetime import datetime

class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    post_id: Mapped[str] = mapped_column(String(36), ForeignKey("posts.id"), nullable=False)
    parent_id: Mapped[str] = mapped_column(String(36), ForeignKey("comments.id"), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", backref="comments")
    post = relationship("Post", backref="comments")
    replies = relationship("Comment", 
        backref=backref('parent', remote_side=[id]), 
        cascade="all, delete-orphan"
    )
    likes = relationship("CommentLike", back_populates="comment", cascade="all, delete-orphan")

class Like(Base):
    __tablename__ = "likes"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
    post_id: Mapped[str] = mapped_column(String(36), ForeignKey("posts.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class CommentLike(Base):
    __tablename__ = "comment_likes"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
    comment_id: Mapped[str] = mapped_column(String(36), ForeignKey("comments.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    comment = relationship("Comment", back_populates="likes")

class Follow(Base):
    __tablename__ = "follows"

    follower_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
    followed_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Bookmark(Base):
    __tablename__ = "bookmarks"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
    post_id: Mapped[str] = mapped_column(String(36), ForeignKey("posts.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
