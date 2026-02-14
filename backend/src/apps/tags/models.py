from sqlalchemy import Column, String, Integer, Table, ForeignKey
from sqlalchemy.orm import relationship
from src.database.base import Base
import uuid

# Many-to-Many association table
post_tags = Table(
    'post_tags',
    Base.metadata,
    Column('post_id', String(36), ForeignKey('posts.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', String(36), ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), unique=True, index=True, nullable=False)
    type = Column(String(20), default='other') # lighting, subject, location, other
    count = Column(Integer, default=0) # Usage count for sorting

    # Relationships
    posts = relationship("Post", secondary=post_tags, back_populates="tags")
