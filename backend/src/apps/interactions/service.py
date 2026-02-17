from sqlalchemy import update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from src.apps.interactions.models import Bookmark, Comment, CommentLike, Follow, Like
from src.apps.notifications.service import create_notification
from src.apps.notifications.schemas import NotificationCreate, NotificationType
from src.apps.posts.models import Post

# ... existing code ...

from sqlalchemy.exc import IntegrityError

async def bookmark_post(db: AsyncSession, post_id: str, user_id: str) -> bool:
    try:
        new_bookmark = Bookmark(user_id=user_id, post_id=post_id)
        db.add(new_bookmark)
        await db.commit()
        return True # Bookmarked
    except IntegrityError:
        await db.rollback()
        # If insertion fails due to duplicate, it means it was already bookmarked.
        # So we should unbookmark it.
        # But wait, standard logic is toggle. 
        # If we rely on IntegrityError, we assume it exists.
        # Let's try to delete.
        result = await db.execute(
            select(Bookmark).filter(Bookmark.user_id == user_id, Bookmark.post_id == post_id)
        )
        existing_bookmark = result.scalars().first()
        if existing_bookmark:
            await db.delete(existing_bookmark)
            await db.commit()
            return False # Unbookmarked
        # If we are here, it means integrity error was something else or race condition resolved weirdly.
        return False

async def delete_bookmarks(db: AsyncSession, post_ids: list[str], user_id: str):
    await db.execute(
        delete(Bookmark).where(
            Bookmark.user_id == user_id,
            Bookmark.post_id.in_(post_ids)
        )
    )
    await db.commit()

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
            selectinload(Comment.likes),
            selectinload(Comment.post) # Load post to get author
        )
        .filter(Comment.id == db_comment.id)
    )
    comment = result.scalars().first()
    
    # Set computed fields for schema
    comment.likes_count = 0
    comment.is_liked = False
    
    # --- Notification Trigger ---
    # Notify Post Author
    if comment.post.user_id != user_id:
        await create_notification(
            db,
            NotificationCreate(
                recipient_id=comment.post.user_id,
                sender_id=user_id,
                type=NotificationType.COMMENT,
                post_id=comment.post_id,
                comment_id=comment.id,
                content=f"评论了你的作品: {comment.content[:20]}"
            )
        )
        
    # Notify Parent Comment Author (if reply)
    if comment.parent_id:
        # We need to fetch parent comment to get its author
        parent_result = await db.execute(select(Comment).filter(Comment.id == comment.parent_id))
        parent_comment = parent_result.scalars().first()
        
        if parent_comment and parent_comment.user_id != user_id and parent_comment.user_id != comment.post.user_id:
            # Avoid double notification if parent author is also post author
             await create_notification(
                db,
                NotificationCreate(
                    recipient_id=parent_comment.user_id,
                    sender_id=user_id,
                    type=NotificationType.COMMENT,
                    post_id=comment.post_id,
                    comment_id=comment.id,
                    content=f"回复了你的评论: {comment.content[:20]}"
                )
            )

    return comment

from sqlalchemy.orm.attributes import set_committed_value


async def get_comments_by_post(db: AsyncSession, post_id: str, current_user_id: str = None) -> list[Comment]:
    # Fetch all comments for the post
    # Using subquery to count likes to avoid N+1
    # Actually, we can just load the likes relationship eagerly (selectinload) if N is small,
    # but for scalability, we should use a separate query or count.
    # However, to check is_liked, we need to know if current user liked it.
    
    # Current implementation uses selectinload(Comment.likes) which loads ALL likes.
    # If a comment has 10k likes, this is bad.
    
    # Better approach:
    # 1. Fetch comments.
    # 2. Fetch like counts for these comments (group by comment_id).
    # 3. Fetch if current user liked these comments (where user_id = current).
    
    # Let's keep it simple but optimized:
    # We will still fetch comments, but we won't load ALL likes.
    # We will issue a separate query to get counts and user status.
    
    query = select(Comment).options(
        selectinload(Comment.user)
        # remove selectinload(Comment.likes) to avoid loading all objects
    ).filter(
        Comment.post_id == post_id
    ).order_by(Comment.created_at.asc())
    
    result = await db.execute(query)
    all_comments = result.scalars().all()
    
    if not all_comments:
        return []

    comment_ids = [c.id for c in all_comments]
    
    # 1. Get Like Counts
    # SELECT comment_id, COUNT(*) FROM comment_likes WHERE comment_id IN (...) GROUP BY comment_id
    from sqlalchemy import func
    likes_count_stmt = (
        select(CommentLike.comment_id, func.count())
        .where(CommentLike.comment_id.in_(comment_ids))
        .group_by(CommentLike.comment_id)
    )
    likes_count_result = await db.execute(likes_count_stmt)
    likes_count_map = {row[0]: row[1] for row in likes_count_result.all()}
    
    # 2. Get User Like Status
    liked_map = {}
    if current_user_id:
        user_likes_stmt = (
            select(CommentLike.comment_id)
            .where(
                CommentLike.comment_id.in_(comment_ids),
                CommentLike.user_id == current_user_id
            )
        )
        user_likes_result = await db.execute(user_likes_stmt)
        liked_map = {row[0]: True for row in user_likes_result.all()}
    
    # Organize comments into a tree structure
    comment_map = {}
    root_comments = []
    
    # First pass: Initialize all comments and put them in a map
    for comment in all_comments:
        # Calculate likes count and status from maps
        comment.likes_count = likes_count_map.get(comment.id, 0)
        comment.is_liked = liked_map.get(comment.id, False)
        
        # Initialize replies list
        set_committed_value(comment, "replies", [])
        
        comment_map[comment.id] = comment
        
    # Second pass: Build the tree
    for comment in all_comments:
        if comment.parent_id:
            parent = comment_map.get(comment.parent_id)
            if parent:
                parent.replies.append(comment)
            else:
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
    try:
        new_like = Like(user_id=user_id, post_id=post_id)
        db.add(new_like)
        # Optimistic update: increment count
        await db.execute(
            update(Post).where(Post.id == post_id).values(likes_count=Post.likes_count + 1)
        )
        await db.commit()
        
        # --- Notification Trigger ---
        # Fetch post to get author
        post_result = await db.execute(select(Post).filter(Post.id == post_id))
        post = post_result.scalars().first()
        
        if post and post.user_id != user_id:
            await create_notification(
                db,
                NotificationCreate(
                    recipient_id=post.user_id,
                    sender_id=user_id,
                    type=NotificationType.LIKE,
                    post_id=post_id,
                    content="赞了你的作品"
                )
            )

        return True # Liked
    except IntegrityError:
        await db.rollback()
        # Already liked, so unlike
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
        return False

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
        
        # --- Notification Trigger ---
        await create_notification(
            db,
            NotificationCreate(
                recipient_id=target_user_id,
                sender_id=current_user_id,
                type=NotificationType.FOLLOW,
                content="关注了你"
            )
        )
        
        return True # Followed

async def get_follow_status(db: AsyncSession, target_user_id: str, current_user_id: str) -> bool:
    if not current_user_id:
        return False
    result = await db.execute(
        select(Follow).filter(Follow.follower_id == current_user_id, Follow.followed_id == target_user_id)
    )
    return result.scalars().first() is not None
