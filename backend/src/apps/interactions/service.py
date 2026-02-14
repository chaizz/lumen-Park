from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from src.apps.interactions.models import Bookmark, Comment, CommentLike, Follow, Like

# ... existing code ...

async def bookmark_post(db: AsyncSession, post_id: str, user_id: str) -> bool:
    # Check if already bookmarked
    result = await db.execute(
        select(Bookmark).filter(Bookmark.user_id == user_id, Bookmark.post_id == post_id)
    )
    existing_bookmark = result.scalars().first()
    
    if existing_bookmark:
        await db.delete(existing_bookmark)
        await db.commit()
        return False # Unbookmarked
    else:
        new_bookmark = Bookmark(user_id=user_id, post_id=post_id)
        db.add(new_bookmark)
        await db.commit()
        return True # Bookmarked

async def get_bookmark_status(db: AsyncSession, post_id: str, user_id: str) -> bool:
    if not user_id:
        return False
    result = await db.execute(
        select(Bookmark).filter(Bookmark.user_id == user_id, Bookmark.post_id == post_id)
    )
    return result.scalars().first() is not None
from src.apps.interactions.schemas import CommentCreate
from src.apps.posts.models import Post


async def create_comment(db: AsyncSession, comment_in: CommentCreate, user_id: str) -> Comment:
    db_comment = Comment(
        user_id=user_id,
        post_id=comment_in.post_id,
        parent_id=comment_in.parent_id,
        content=comment_in.content
    )
    db.add(db_comment)
    await db.commit()
    await db.refresh(db_comment)
    
    # Reload with user relationship for response
    result = await db.execute(
        select(Comment)
        .options(
            selectinload(Comment.user),
            selectinload(Comment.replies),
            selectinload(Comment.likes)
        )
        .filter(Comment.id == db_comment.id)
    )
    comment = result.scalars().first()
    
    # Set computed fields for schema
    comment.likes_count = 0
    comment.is_liked = False
    
    return comment

from sqlalchemy.orm.attributes import set_committed_value


async def get_comments_by_post(db: AsyncSession, post_id: str, current_user_id: str = None) -> list[Comment]:
    # Fetch all comments for the post
    query = select(Comment).options(
        selectinload(Comment.user),
        selectinload(Comment.likes)
    ).filter(
        Comment.post_id == post_id
    ).order_by(Comment.created_at.asc()) # Order by created_at to ensure parents come before children
    
    result = await db.execute(query)
    all_comments = result.scalars().all()
    
    # Organize comments into a tree structure
    comment_map = {}
    root_comments = []
    
    # First pass: Initialize all comments and put them in a map
    for comment in all_comments:
        # Calculate likes count and status manually
        likes_list = comment.likes
        comment.likes_count = len(likes_list)
        comment.is_liked = any(l.user_id == current_user_id for l in likes_list) if current_user_id else False
        
        # Initialize replies list
        # Use set_committed_value to initialize the relationship without triggering a load.
        # This is critical to avoid "MissingGreenlet" errors in async context when 
        # assigning to a relationship that hasn't been loaded.
        set_committed_value(comment, "replies", [])
        
        comment_map[comment.id] = comment
        
    # Second pass: Build the tree
    for comment in all_comments:
        if comment.parent_id:
            parent = comment_map.get(comment.parent_id)
            if parent:
                parent.replies.append(comment)
            else:
                # Parent not found (maybe deleted?), treat as root or ignore?
                # Let's treat as root for now to avoid data loss in UI
                root_comments.append(comment)
        else:
            root_comments.append(comment)
            
    # Sort root comments by created_at desc (newest first)
    root_comments.sort(key=lambda x: x.created_at, reverse=True)
            
    return root_comments

async def delete_comment(db: AsyncSession, comment_id: str, user_id: str) -> bool:
    # 1. Fetch comment with post relationship to check permissions
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.post))
        .filter(Comment.id == comment_id)
    )
    comment = result.scalars().first()
    
    if not comment:
        return False
        
    # 2. Check permissions: 
    # - Post Author (Owner of the work) can delete ANY comment.
    # - Comment Author can delete THEIR OWN comment.
    is_post_author = comment.post.user_id == user_id
    is_comment_author = comment.user_id == user_id
    
    if not (is_post_author or is_comment_author):
        return False
        
    # 3. Delete (Cascade delete should handle replies if configured in model, usually it is)
    # Check model cascade: replies = relationship(..., cascade="all, delete-orphan") -> Yes.
    await db.delete(comment)
    await db.commit()
    return True

async def like_post(db: AsyncSession, post_id: str, user_id: str) -> bool:
    # Check if already liked
    result = await db.execute(
        select(Like).filter(Like.user_id == user_id, Like.post_id == post_id)
    )
    existing_like = result.scalars().first()
    
    if existing_like:
        await db.delete(existing_like)
        # Decrement post.likes_count
        await db.execute(
            update(Post).where(Post.id == post_id).values(likes_count=Post.likes_count - 1)
        )
        await db.commit()
        return False # Unliked
    else:
        new_like = Like(user_id=user_id, post_id=post_id)
        db.add(new_like)
        # Increment post.likes_count
        await db.execute(
            update(Post).where(Post.id == post_id).values(likes_count=Post.likes_count + 1)
        )
        await db.commit()
        return True # Liked

async def get_post_like_status(db: AsyncSession, post_id: str, user_id: str) -> bool:
    if not user_id:
        return False
    result = await db.execute(
        select(Like).filter(Like.user_id == user_id, Like.post_id == post_id)
    )
    return result.scalars().first() is not None

async def like_comment(db: AsyncSession, comment_id: str, user_id: str) -> bool:
    result = await db.execute(
        select(CommentLike).filter(CommentLike.user_id == user_id, CommentLike.comment_id == comment_id)
    )
    existing = result.scalars().first()
    
    if existing:
        await db.delete(existing)
        await db.commit()
        return False
    else:
        new_like = CommentLike(user_id=user_id, comment_id=comment_id)
        db.add(new_like)
        await db.commit()
        return True

async def follow_user(db: AsyncSession, target_user_id: str, current_user_id: str) -> bool:
    if target_user_id == current_user_id:
        return False # Cannot follow self
        
    result = await db.execute(
        select(Follow).filter(Follow.follower_id == current_user_id, Follow.followed_id == target_user_id)
    )
    existing = result.scalars().first()
    
    if existing:
        await db.delete(existing)
        await db.commit()
        return False # Unfollowed
    else:
        new_follow = Follow(follower_id=current_user_id, followed_id=target_user_id)
        db.add(new_follow)
        await db.commit()
        return True # Followed

async def get_follow_status(db: AsyncSession, target_user_id: str, current_user_id: str) -> bool:
    if not current_user_id:
        return False
    result = await db.execute(
        select(Follow).filter(Follow.follower_id == current_user_id, Follow.followed_id == target_user_id)
    )
    return result.scalars().first() is not None
