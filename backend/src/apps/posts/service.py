from sqlalchemy import update, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from src.apps.interactions.models import Bookmark, Like
from src.apps.posts.models import ExifData, FujiRecipe, Post, PostImage
from src.apps.posts.schemas import PostCreate
from src.apps.tags.service import get_or_create_tags, increment_tag_count

# ... existing code ...

async def get_liked_posts(db: AsyncSession, user_id: str) -> list[Post]:
    query = select(Post).join(Like, Like.post_id == Post.id).options(
        selectinload(Post.user),
        selectinload(Post.images).selectinload(PostImage.exif),
        selectinload(Post.images).selectinload(PostImage.recipe),
        selectinload(Post.tags)
    ).filter(
        Like.user_id == user_id
    ).order_by(Like.created_at.desc())
    
    result = await db.execute(query)
    posts = result.scalars().all()
    # Ensure likes_count
    for post in posts:
        if post.likes_count is None: post.likes_count = 0
    return posts

async def get_bookmarked_posts(db: AsyncSession, user_id: str, keyword: str = None) -> list[Post]:
    query = select(Post).join(Bookmark, Bookmark.post_id == Post.id).options(
        selectinload(Post.user),
        selectinload(Post.images).selectinload(PostImage.exif),
        selectinload(Post.images).selectinload(PostImage.recipe),
        selectinload(Post.tags)
    ).filter(
        Bookmark.user_id == user_id
    )

    if keyword:
        query = query.filter(or_(Post.title.ilike(f"%{keyword}%"), Post.description.ilike(f"%{keyword}%")))

    query = query.order_by(Bookmark.created_at.desc())
    
    result = await db.execute(query)
    posts = result.scalars().all()
    # Ensure likes_count
    for post in posts:
        if post.likes_count is None: post.likes_count = 0
    return posts


async def create_post(db: AsyncSession, post_in: PostCreate, user_id: str) -> Post:
    # 1. Handle Tags First (to avoid lazy load issues with new object)
    tags = []
    if post_in.tags:
        tags = await get_or_create_tags(db, post_in.tags)
        # Increment usage count
        for tag in tags:
            await increment_tag_count(db, tag.id)

    # 2. Create Post with tags
    # Determine cover image (first one)
    cover_image_path = post_in.images[0].image_path if post_in.images else None
    
    db_post = Post(
        user_id=user_id,
        image_path=cover_image_path, # Backward compatibility / Cover
        title=post_in.title,
        description=post_in.description,
        tags=tags # Assign tags directly in constructor
    )
    db.add(db_post)
    await db.flush() # flush to get ID

    # 2. Create PostImages and related Exif/Recipe
    for idx, img_in in enumerate(post_in.images):
        db_image = PostImage(
            post_id=db_post.id,
            image_path=img_in.image_path,
            width=img_in.width,
            height=img_in.height,
            order=idx
        )
        db.add(db_image)
        await db.flush() # get image ID
        
        if img_in.exif:
            db_exif = ExifData(
                image_id=db_image.id,
                **img_in.exif.model_dump()
            )
            db.add(db_exif)
            
        if img_in.recipe:
            db_recipe = FujiRecipe(
                image_id=db_image.id,
                **img_in.recipe.model_dump()
            )
            db.add(db_recipe)
        
    await db.commit()
    
    # Remove the object from the session to force a clean reload from the database
    # This avoids issues with the Identity Map reusing the stale object and 
    # prevents MissingGreenlet errors during lazy/eager loading.
    db.expunge(db_post)
    
    return await get_post(db, db_post.id)

async def increment_views(db: AsyncSession, post_id: str):
    await db.execute(
        update(Post).where(Post.id == post_id).values(views_count=Post.views_count + 1)
    )
    await db.commit()

async def get_post(db: AsyncSession, post_id: str) -> Post | None:
    result = await db.execute(
        select(Post)
        .options(
            selectinload(Post.user),
            selectinload(Post.images).selectinload(PostImage.exif),
            selectinload(Post.images).selectinload(PostImage.recipe),
            selectinload(Post.tags)
        )
        .filter(Post.id == post_id)
    )
    return result.scalars().first()

async def get_posts(db: AsyncSession, skip: int = 0, limit: int = 100, user_id: str = None, tag_ids: list[str] = None, keyword: str = None) -> list[Post]:
    query = select(Post).options(
        selectinload(Post.user),
        # For list view, we might only need the first image or all, let's load all for now
        selectinload(Post.images).selectinload(PostImage.exif),
        selectinload(Post.images).selectinload(PostImage.recipe),
        selectinload(Post.tags)
    )
    
    if user_id:
        query = query.filter(Post.user_id == user_id)
        
    if tag_ids:
        # Filter posts that have ANY of the given tags (OR logic)
        # For AND logic (posts that have ALL tags), we'd need multiple joins or group by having count
        # Let's start with simple IN logic
        from src.apps.tags.models import post_tags
        query = query.join(Post.tags).filter(post_tags.c.tag_id.in_(tag_ids)).distinct()
    
    if keyword:
        query = query.filter(or_(Post.title.ilike(f"%{keyword}%"), Post.description.ilike(f"%{keyword}%")))
        
    query = query.offset(skip).limit(limit).order_by(Post.created_at.desc())
    
    result = await db.execute(query)
    posts = result.scalars().all()
    
    # Ensure likes_count is populated if it's None (though model default is 0)
    for post in posts:
        if post.likes_count is None:
            post.likes_count = 0
            
    return posts
