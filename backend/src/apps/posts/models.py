import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import Base


class FilmSimulation(str, enum.Enum):
    PROVIA = "Provia"
    VELVIA = "Velvia"
    ASTIA = "Astia"
    CLASSIC_CHROME = "Classic Chrome"
    PRO_NEG_HI = "PRO Neg. Hi"
    PRO_NEG_STD = "PRO Neg. Std"
    CLASSIC_NEG = "Classic Neg"
    ETERNA = "Eterna"
    ETERNA_BLEACH_BYPASS = "Eterna Bleach Bypass"
    ACROS = "Acros"
    MONOCHROME = "Monochrome"
    SEPIA = "Sepia"
    NOSTALGIC_NEG = "Nostalgic Neg"
    REALA_ACE = "Reala Ace"

class DynamicRange(str, enum.Enum):
    DR100 = "DR100"
    DR200 = "DR200"
    DR400 = "DR400"
    DR_P = "DR-P"
    DR_AUTO = "DR-Auto"

class Post(Base):
    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    # image_path moved to PostImage table for multi-image support. 
    # But for backward compatibility or cover image, we can keep a cover_image field.
    # For now, let's keep image_path as "cover image" or deprecate it in favor of images[0].
    # To avoid breaking existing code immediately, let's keep it but also add relationship.
    image_path: Mapped[str] = mapped_column(String(255), nullable=True) # Made nullable
    
    title: Mapped[str] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Stats
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    likes_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    user = relationship("User", back_populates="posts")
    
    # One-to-Many relationship with PostImage
    images = relationship("PostImage", back_populates="post", cascade="all, delete-orphan")

class PostImage(Base):
    __tablename__ = "post_images"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id: Mapped[str] = mapped_column(String(36), ForeignKey("posts.id"), nullable=False)
    image_path: Mapped[str] = mapped_column(String(255), nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=True)
    height: Mapped[int] = mapped_column(Integer, nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0) # To maintain order
    
    post = relationship("Post", back_populates="images")
    
    # One-to-One relationship with ExifData and FujiRecipe per image
    exif = relationship("ExifData", back_populates="image", uselist=False, cascade="all, delete-orphan")
    recipe = relationship("FujiRecipe", back_populates="image", uselist=False, cascade="all, delete-orphan")

class ExifData(Base):
    __tablename__ = "exif_data"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Changed from post_id to image_id
    image_id: Mapped[str] = mapped_column(String(36), ForeignKey("post_images.id"), nullable=False)
    
    image = relationship("PostImage", back_populates="exif")

    camera_make: Mapped[str] = mapped_column(String(50), nullable=True)
    camera_model: Mapped[str] = mapped_column(String(50), nullable=True)
    lens: Mapped[str] = mapped_column(String(100), nullable=True)
    iso: Mapped[int] = mapped_column(Integer, nullable=True)
    aperture: Mapped[float] = mapped_column(Float, nullable=True)
    shutter_speed: Mapped[str] = mapped_column(String(20), nullable=True)
    focal_length: Mapped[float] = mapped_column(Float, nullable=True)

class FujiRecipe(Base):
    __tablename__ = "fuji_recipes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Changed from post_id to image_id
    image_id: Mapped[str] = mapped_column(String(36), ForeignKey("post_images.id"), nullable=False)
    
    image = relationship("PostImage", back_populates="recipe")

    simulation: Mapped[FilmSimulation] = mapped_column(SQLAlchemyEnum(FilmSimulation), nullable=True)
    dynamic_range: Mapped[DynamicRange] = mapped_column(SQLAlchemyEnum(DynamicRange), nullable=True)
    wb: Mapped[str] = mapped_column(String(50), nullable=True)
    wb_shift_r: Mapped[int] = mapped_column(Integer, nullable=True)
    wb_shift_b: Mapped[int] = mapped_column(Integer, nullable=True)
    color: Mapped[int] = mapped_column(Integer, nullable=True)
    sharpness: Mapped[int] = mapped_column(Integer, nullable=True)
    highlights: Mapped[int] = mapped_column(Integer, nullable=True)
    shadows: Mapped[int] = mapped_column(Integer, nullable=True)
    grain: Mapped[str] = mapped_column(String(50), nullable=True)
    color_chrome: Mapped[str] = mapped_column(String(50), nullable=True)
    color_chrome_blue: Mapped[str] = mapped_column(String(50), nullable=True)
    clarity: Mapped[int] = mapped_column(Integer, nullable=True)
