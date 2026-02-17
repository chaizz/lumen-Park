import nanoid
import string
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, func, update, and_
from sqlalchemy.orm import selectinload
from src.apps.albums.models import Album, AlbumPost, AlbumStatus
from src.apps.albums.schemas import AlbumCreate, AlbumUpdate, AlbumPostReorder
from src.apps.posts.models import Post, PostImage

# --- Helper ---
def generate_short_id(size=8):
    alphabet = string.ascii_letters + string.digits
    return nanoid.generate(alphabet=alphabet, size=size)

# --- Service ---

async def create_album(db: AsyncSession, album_in: AlbumCreate, user_id: str) -> Album:
    # 1. Generate unique short_id
    while True:
        short_id = generate_short_id()
        existing = await db.execute(select(Album).filter(Album.short_id == short_id))
        if not existing.scalars().first():
            break
            
    # 2. Create Album
    db_album = Album(
        user_id=user_id,
        short_id=short_id,
        title=album_in.title,
        description=album_in.description,
        cover_url=album_in.cover_url,
        status=album_in.status,
        is_public=album_in.is_public
    )
    db.add(db_album)
    await db.flush() # Get ID
    
    # 3. Add Posts if any
    if album_in.post_ids:
        # Verify posts belong to user (MVP requirement)
        posts_result = await db.execute(select(Post).options(selectinload(Post.images)).filter(Post.id.in_(album_in.post_ids), Post.user_id == user_id))
        valid_posts = posts_result.scalars().all()
        valid_post_map = {p.id: p for p in valid_posts}
        
        for idx, post_id in enumerate(album_in.post_ids): # Use input order
            if post_id in valid_post_map:
                db.add(AlbumPost(album_id=db_album.id, post_id=post_id, order=idx))
                
                # If no cover provided, use first post's cover
                if not db_album.cover_url and idx == 0:
                    post = valid_post_map[post_id]
                    if post.images:
                        # PostImage might not have image_url property if it's a Pydantic schema mismatch or ORM object
                        # Let's check model definition. PostImage has image_path.
                        # We should use image_path or constructed URL.
                        # Assuming image_path is relative, we might need full URL if frontend expects it.
                        # But Post model usually returns image_url property via hybrid property or schema.
                        # Here we are dealing with ORM object directly.
                        # PostImage model has image_path.
                        # Let's use image_path for now, or check if we have a property.
                        # If PostImage is ORM, it has image_path.
                        db_album.cover_url = post.images[0].image_path
    
    await db.commit()
    await db.refresh(db_album)
    return db_album

async def get_albums(db: AsyncSession, user_id: str, include_drafts: bool = False, skip: int = 0, limit: int = 20) -> List[Album]:
    query = select(Album).filter(Album.user_id == user_id)
    if not include_drafts:
        query = query.filter(Album.status == AlbumStatus.PUBLISHED)
        
    query = query.order_by(Album.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    albums = result.scalars().all()
    
    # Fill post_count
    for album in albums:
        count_res = await db.execute(select(func.count()).select_from(AlbumPost).filter(AlbumPost.album_id == album.id))
        album.post_count = count_res.scalar()
        
    return albums

async def get_album_by_id(db: AsyncSession, album_id: str) -> Optional[Album]:
    result = await db.execute(select(Album).filter(Album.id == album_id))
    return result.scalars().first()

async def get_album_by_short_id(db: AsyncSession, short_id: str) -> Optional[Album]:
    result = await db.execute(select(Album).filter(Album.short_id == short_id))
    return result.scalars().first()

async def update_album(db: AsyncSession, album: Album, album_in: AlbumUpdate, user_id: str) -> Album:
    update_data = album_in.model_dump(exclude_unset=True)
    
    # Handle post_ids replacement if provided
    post_ids = update_data.pop('post_ids', None)
    if post_ids is not None:
        # Clear existing
        await db.execute(delete(AlbumPost).where(AlbumPost.album_id == album.id))
        
        # Add new
        # Verify posts belong to user
        posts_result = await db.execute(select(Post).filter(Post.id.in_(post_ids), Post.user_id == user_id))
        valid_posts = posts_result.scalars().all()
        valid_post_ids = {p.id for p in valid_posts}
        
        for idx, post_id in enumerate(post_ids):
            if post_id in valid_post_ids:
                db.add(AlbumPost(album_id=album.id, post_id=post_id, order=idx))

    # Update fields
    for field, value in update_data.items():
        setattr(album, field, value)
        
    await db.commit()
    await db.refresh(album)
    return album

async def delete_album(db: AsyncSession, album: Album):
    await db.delete(album)
    await db.commit()

async def get_album_posts(db: AsyncSession, album_id: str) -> List[Post]:
    # Join AlbumPost and Post, order by AlbumPost.order
    query = (
        select(Post)
        .join(AlbumPost, AlbumPost.post_id == Post.id)
        .where(AlbumPost.album_id == album_id)
        .order_by(AlbumPost.order.asc())
        .options(
            selectinload(Post.images).selectinload(PostImage.exif), 
            selectinload(Post.images).selectinload(PostImage.recipe),
            selectinload(Post.user),
            selectinload(Post.tags)
        ) # Eager load for display
    )
    result = await db.execute(query)
    return result.scalars().all()

async def add_posts_to_album(db: AsyncSession, album: Album, post_ids: List[str], user_id: str):
    # Verify posts
    posts_result = await db.execute(select(Post).filter(Post.id.in_(post_ids), Post.user_id == user_id))
    valid_posts = posts_result.scalars().all()
    valid_post_ids = {p.id for p in valid_posts}
    
    # Get current max order
    max_order_res = await db.execute(select(func.max(AlbumPost.order)).filter(AlbumPost.album_id == album.id))
    current_max = max_order_res.scalar() or -1
    
    new_items = []
    for idx, post_id in enumerate(post_ids):
        if post_id in valid_post_ids:
            # Check if already exists to avoid duplicate
            exists = await db.execute(select(AlbumPost).filter(AlbumPost.album_id == album.id, AlbumPost.post_id == post_id))
            if not exists.scalars().first():
                current_max += 1
                new_items.append(AlbumPost(album_id=album.id, post_id=post_id, order=current_max))
    
    if new_items:
        db.add_all(new_items)
        await db.commit()

async def reorder_album_posts(db: AsyncSession, album: Album, post_ids: List[str]):
    # post_ids is the new ordered list of IDs
    # We update the 'order' field for each matching post
    for idx, post_id in enumerate(post_ids):
        await db.execute(
            update(AlbumPost)
            .where(and_(AlbumPost.album_id == album.id, AlbumPost.post_id == post_id))
            .values(order=idx)
        )
    await db.commit()
