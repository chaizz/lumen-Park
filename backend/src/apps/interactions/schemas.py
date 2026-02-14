from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from src.apps.users.schemas import UserResponse

class CommentBase(BaseModel):
    content: str
    parent_id: Optional[str] = None

class CommentCreate(CommentBase):
    post_id: str

class CommentResponse(CommentBase):
    id: str
    user_id: str
    post_id: str
    created_at: datetime
    user: Optional[UserResponse] = None
    replies: List['CommentResponse'] = []
    likes_count: int = 0
    is_liked: bool = False
    
    model_config = ConfigDict(from_attributes=True)

class LikeCreate(BaseModel):
    post_id: str

class LikeResponse(BaseModel):
    status: str # "liked" or "unliked"

class FollowCreate(BaseModel):
    user_id: str

class FollowResponse(BaseModel):
    status: str # "followed" or "unfollowed"

class BookmarkCreate(BaseModel):
    post_id: str

class BookmarkResponse(BaseModel):
    status: str # "bookmarked" or "unbookmarked"
