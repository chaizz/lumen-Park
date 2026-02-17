
import pytest
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.database.base import Base
from src.apps.interactions.service import like_post
from src.apps.users.models import User
from src.apps.tags.models import post_tags
from src.apps.posts.models import Post

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.mark.asyncio
async def test_like():
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
        post = Post(title="Test Post", user_id=user.id, likes_count=0)
        db.add(post)
        await db.commit()
        await db.refresh(post)

        # 1. Like
        result = await like_post(db, post.id, user.id)
        assert result == True
        await db.refresh(post)
        assert post.likes_count == 1

        # 2. Duplicate Like (Race Condition Logic)
        # We can't easily simulate race condition here without threads, 
        # but we can verify the logic handles re-entry correctly (toggle behavior)
        
        # Standard toggle behavior: calling like_post again should UNLIKE
        result = await like_post(db, post.id, user.id)
        assert result == False
        await db.refresh(post)
        assert post.likes_count == 0

    await engine.dispose()
