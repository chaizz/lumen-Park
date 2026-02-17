
import pytest
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.database.base import Base
from src.apps.interactions.service import get_comments_by_post
from src.apps.interactions.models import Comment, CommentLike
from src.apps.users.models import User
from src.apps.tags.models import post_tags
from src.apps.posts.models import Post

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.mark.asyncio
async def test_comments():
    engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # Create user
        user = User(username="testuser", email="test@example.com", hashed_password="hashedpassword")
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Create post
        post = Post(title="Test Post", user_id=user.id)
        db.add(post)
        await db.commit()
        await db.refresh(post)

        # Create comments
        c1 = Comment(content="Comment 1", user_id=user.id, post_id=post.id)
        c2 = Comment(content="Comment 2", user_id=user.id, post_id=post.id)
        db.add_all([c1, c2])
        await db.commit()
        await db.refresh(c1)
        await db.refresh(c2)

        # Like comments
        l1 = CommentLike(user_id=user.id, comment_id=c1.id)
        db.add(l1)
        await db.commit()

        # Test N+1 fix
        comments = await get_comments_by_post(db, post.id, current_user_id=user.id)
        
        assert len(comments) == 2
        
        # Verify counts and status
        # Comment 1 should have 1 like and be liked by user
        c1_res = next(c for c in comments if c.id == c1.id)
        assert c1_res.likes_count == 1
        assert c1_res.is_liked == True
        
        # Comment 2 should have 0 likes and not be liked
        c2_res = next(c for c in comments if c.id == c2.id)
        assert c2_res.likes_count == 0
        assert c2_res.is_liked == False

    await engine.dispose()
