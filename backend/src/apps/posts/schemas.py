from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from src.apps.posts.models import DynamicRange, FilmSimulation
from src.apps.users.schemas import UserResponse
from src.apps.tags.schemas import TagResponse

class ExifDataBase(BaseModel):
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    lens: Optional[str] = None
    iso: Optional[int] = None
    aperture: Optional[float] = None
    shutter_speed: Optional[str] = None
    focal_length: Optional[float] = None

class ExifDataCreate(ExifDataBase):
    pass

class ExifDataResponse(ExifDataBase):
    model_config = ConfigDict(from_attributes=True)

class FujiRecipeBase(BaseModel):
    simulation: Optional[FilmSimulation] = None
    dynamic_range: Optional[DynamicRange] = None
    wb: Optional[str] = None
    wb_shift_r: Optional[int] = None
    wb_shift_b: Optional[int] = None
    color: Optional[int] = None
    sharpness: Optional[int] = None
    highlights: Optional[int] = None
    shadows: Optional[int] = None
    grain: Optional[str] = None
    color_chrome: Optional[str] = None
    color_chrome_blue: Optional[str] = None
    clarity: Optional[int] = None

class FujiRecipeCreate(FujiRecipeBase):
    pass

class FujiRecipeResponse(FujiRecipeBase):
    model_config = ConfigDict(from_attributes=True)

class PostImageCreate(BaseModel):
    image_path: str
    width: Optional[int] = None
    height: Optional[int] = None
    order: int = 0
    exif: Optional[ExifDataCreate] = None
    recipe: Optional[FujiRecipeCreate] = None

class PostImageResponse(BaseModel):
    id: str
    image_path: str
    width: Optional[int] = None
    height: Optional[int] = None
    order: int
    exif: Optional[ExifDataResponse] = None
    recipe: Optional[FujiRecipeResponse] = None
    model_config = ConfigDict(from_attributes=True)

class PostBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class PostCreate(PostBase):
    # Support multiple images. Backward compatible if needed but let's switch to new structure.
    images: List[PostImageCreate]
    tags: List[str] = [] # List of tag names

class PostResponse(PostBase):
    id: str
    user_id: str
    image_path: Optional[str] = None # Cover image
    created_at: datetime
    views_count: int = 0
    likes_count: int = 0
    
    images: List[PostImageResponse] = []
    tags: List[TagResponse] = []
    
    user: Optional[UserResponse] = None
    
    model_config = ConfigDict(from_attributes=True)
