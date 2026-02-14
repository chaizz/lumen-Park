from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.apps.posts import schemas, service
from src.apps.users.models import User
from src.core import deps
from src.database.session import get_db

router = APIRouter()

@router.post("/", response_model=schemas.PostResponse)
async def create_post(
    post_in: schemas.PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    post = await service.create_post(db, post_in=post_in, user_id=current_user.id)
    return post

@router.get("/", response_model=List[schemas.PostResponse])
async def read_posts(
    skip: int = 0,
    limit: int = 100,
    user_id: str = None,
    db: AsyncSession = Depends(get_db),
) -> Any:
    posts = await service.get_posts(db, skip=skip, limit=limit, user_id=user_id)
    return posts

@router.get("/liked/{user_id}", response_model=List[schemas.PostResponse])
async def read_liked_posts(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await service.get_liked_posts(db, user_id=user_id)

@router.get("/bookmarked/{user_id}", response_model=List[schemas.PostResponse])
async def read_bookmarked_posts(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await service.get_bookmarked_posts(db, user_id=user_id)

@router.get("/{post_id}", response_model=schemas.PostResponse)
async def read_post(
    post_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    # Increment view count
    await service.increment_views(db, post_id)
    
    post = await service.get_post(db, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post
