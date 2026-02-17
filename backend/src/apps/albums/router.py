from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.apps.albums import schemas, service
from src.apps.users.models import User
from src.core import deps
from src.database.session import get_db

router = APIRouter()

@router.post("/", response_model=schemas.AlbumResponse)
async def create_album(
    album_in: schemas.AlbumCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    return await service.create_album(db, album_in, current_user.id)

@router.get("/my", response_model=List[schemas.AlbumResponse])
async def read_my_albums(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    return await service.get_albums(db, user_id=current_user.id, include_drafts=True, skip=skip, limit=limit)

@router.get("/u/{user_id}", response_model=List[schemas.AlbumResponse])
async def read_user_albums(
    user_id: str,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await service.get_albums(db, user_id=user_id, include_drafts=False, skip=skip, limit=limit)

@router.get("/{id}", response_model=schemas.AlbumDetailResponse)
async def read_album(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user_optional),
) -> Any:
    album = await service.get_album_by_id(db, id)
    if not album:
        # Try short_id
        album = await service.get_album_by_short_id(db, id)
        
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
        
    # Check visibility
    if not album.is_public:
        if not current_user or current_user.id != album.user_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this album")
            
    # Fetch posts
    posts = await service.get_album_posts(db, album.id)
    
    # Construct response manually or use Pydantic magic if nested models match
    # AlbumDetailResponse expects posts list.
    # We need to serialize posts to dicts or schemas.
    # Since PostResponse is complex, let's verify if ORM objects work directly.
    # Yes, from_attributes=True in Pydantic V2 should handle it.
    
    album.posts = posts
    album.post_count = len(posts)
    return album

@router.put("/{id}", response_model=schemas.AlbumResponse)
async def update_album(
    id: str,
    album_in: schemas.AlbumUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    album = await service.get_album_by_id(db, id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
        
    if album.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    return await service.update_album(db, album, album_in, current_user.id)

@router.delete("/{id}")
async def delete_album(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    album = await service.get_album_by_id(db, id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
        
    if album.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    await service.delete_album(db, album)
    return {"message": "Album deleted"}

@router.post("/{id}/posts")
async def add_posts_to_album(
    id: str,
    data: schemas.AlbumPostAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    album = await service.get_album_by_id(db, id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
        
    if album.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    await service.add_posts_to_album(db, album, data.post_ids, current_user.id)
    return {"message": "Posts added"}

@router.put("/{id}/reorder")
async def reorder_album_posts(
    id: str,
    data: schemas.AlbumPostReorder,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    album = await service.get_album_by_id(db, id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
        
    if album.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    await service.reorder_album_posts(db, album, data.post_ids)
    return {"message": "Order updated"}
