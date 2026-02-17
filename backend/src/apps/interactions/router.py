from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_db
from src.apps.interactions import service
from src.apps.interactions import schemas
from src.apps.users.models import User
from src.core import deps

router = APIRouter()

@router.get("/comments/{post_id}", response_model=List[schemas.CommentResponse])
async def read_comments(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user_optional), # Allow guests to view
) -> Any:
    user_id = current_user.id if current_user else None
    return await service.get_comments_by_post(db, post_id, user_id)

@router.post("/comments", response_model=schemas.CommentResponse)
async def create_comment(
    comment_in: schemas.CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    return await service.create_comment(db, comment_in, current_user.id)

@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> None:
    success = await service.delete_comment(db, comment_id, current_user.id)
    if not success:
        # Check if comment exists first to give 404 vs 403? 
        # For simplicity, service returns False for both non-existent and permission denied.
        # Let's assume it's permission error or not found, 403 or 404.
        # But based on service logic, if not found returns False, if no perm returns False.
        # We can stick with 403 or 404.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation failed: Comment not found or permission denied"
        )
    return None

@router.post("/comments/{comment_id}/like", response_model=schemas.LikeResponse)
async def like_comment(
    comment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    is_liked = await service.like_comment(db, comment_id, current_user.id)
    return {"status": "liked" if is_liked else "unliked"}

@router.post("/likes", response_model=schemas.LikeResponse)
async def like_post(
    like_in: schemas.LikeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    is_liked = await service.like_post(db, like_in.post_id, current_user.id)
    return {"status": "liked" if is_liked else "unliked"}

@router.get("/likes/status/{post_id}", response_model=schemas.LikeResponse)
async def get_like_status(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    is_liked = await service.get_post_like_status(db, post_id, current_user.id)
    return {"status": "liked" if is_liked else "unliked"}

@router.post("/follow", response_model=schemas.FollowResponse)
async def follow_user(
    follow_in: schemas.FollowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    is_followed = await service.follow_user(db, follow_in.user_id, current_user.id)
    return {"status": "followed" if is_followed else "unfollowed"}

@router.get("/follow/status/{user_id}", response_model=schemas.FollowResponse)
async def get_follow_status(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    is_followed = await service.get_follow_status(db, user_id, current_user.id)
    return {"status": "followed" if is_followed else "unfollowed"}

@router.post("/bookmarks", response_model=schemas.BookmarkResponse)
async def bookmark_post(
    bookmark_in: schemas.BookmarkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    is_bookmarked = await service.bookmark_post(db, bookmark_in.post_id, current_user.id)
    return {"status": "bookmarked" if is_bookmarked else "unbookmarked"}

@router.get("/bookmarks/status/{post_id}", response_model=schemas.BookmarkResponse)
async def get_bookmark_status(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    is_bookmarked = await service.get_bookmark_status(db, post_id, current_user.id)
    return {"status": "bookmarked" if is_bookmarked else "unbookmarked"}

@router.delete("/bookmarks", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookmarks(
    post_ids: List[str] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> None:
    await service.delete_bookmarks(db, post_ids, current_user.id)
    return None
