from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from src.apps.albums.models import AlbumStatus
from src.apps.posts.schemas import PostResponse

class AlbumBase(BaseModel):
    title: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    status: AlbumStatus = AlbumStatus.DRAFT
    is_public: bool = True

class AlbumCreate(AlbumBase):
    post_ids: Optional[List[str]] = None

class AlbumUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    status: Optional[AlbumStatus] = None
    is_public: Optional[bool] = None
    post_ids: Optional[List[str]] = None # If provided, replaces existing posts

class AlbumPostAdd(BaseModel):
    post_ids: List[str]

class AlbumPostReorder(BaseModel):
    post_ids: List[str] # Ordered list of post IDs

class AlbumResponse(AlbumBase):
    id: str
    short_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    post_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)

class AlbumDetailResponse(AlbumResponse):
    posts: List[PostResponse] = [] # Use PostResponse schema

