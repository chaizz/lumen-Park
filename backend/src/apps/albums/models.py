import enum
import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, Enum, Text, DateTime, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.base import Base

class AlbumStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"

class Album(Base):
    __tablename__ = "albums"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    short_id = Column(String(8), unique=True, index=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    cover_url = Column(String(255), nullable=True)
    status = Column(Enum(AlbumStatus), default=AlbumStatus.DRAFT, nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", backref="albums")
    posts_association = relationship("AlbumPost", back_populates="album", cascade="all, delete-orphan")

class AlbumPost(Base):
    __tablename__ = "album_posts"

    album_id = Column(String(36), ForeignKey("albums.id"), primary_key=True)
    post_id = Column(String(36), ForeignKey("posts.id"), primary_key=True)
    order = Column(Integer, default=0, nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now(), default=func.now(), nullable=False)

    # Relationships
    album = relationship("Album", back_populates="posts_association")
    post = relationship("Post")
