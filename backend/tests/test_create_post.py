import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.database.base import Base
from src.core.config import settings
from src.apps.posts import service, schemas
from src.apps.users import service as user_service
from src.apps.users.schemas import UserCreate
from src.apps.tags import service as tag_service
import uuid

# Use a separate test database or the existing one?
# For simplicity in this environment, let's use the existing one but be careful.
# Ideally we should use a test DB.
DATABASE_URL = settings.SQLALCHEMY_DATABASE_URI

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
    await engine.dispose()

@pytest.mark.asyncio
async def test_create_post_transaction_and_tags(db_session):
    # 1. Create a dummy user
    unique_id = str(uuid.uuid4())[:8]
    user_in = UserCreate(
        username=f"testuser_{unique_id}",
        email=f"test_{unique_id}@example.com",
        password="password123"
    )
    user = await user_service.create_user(db_session, user_in)
    
    # 2. Prepare post data
    post_in = schemas.PostCreate(
        title="Test Transaction Post",
        description="Testing transaction atomicity",
        tags=["TestTag1", "TestTag2"],
        images=[
            schemas.PostImageCreate(
                image_path="http://example.com/img1.jpg",
                width=800,
                height=600,
                exif=None,
                recipe=None
            )
        ]
    )

    # 3. Call create_post
    # This function should handle the transaction internally (commit)
    # But wait, in the service code:
    # db.add(db_post)
    # ...
    # await db.commit()
    # If it fails in the middle, does it rollback? 
    # The session passed in `db_session` fixture is used.
    # If create_post raises an exception, the session is not automatically rolled back 
    # INSIDE create_post unless we add a try/except block there.
    # However, standard FastAPI dependency injection pattern relies on the caller (FastAPI) to close/rollback on error,
    # OR the service method should be robust.
    
    try:
        post = await service.create_post(db_session, post_in, user.id)
        
        # 4. Verify Post Created
        assert post.id is not None
        assert post.title == "Test Transaction Post"
        
        # 5. Verify Tags Associated (and Loaded!)
        # This was the source of MissingGreenlet error
        assert len(post.tags) == 2
        tag_names = [t.name for t in post.tags]
        assert "TestTag1" in tag_names
        assert "TestTag2" in tag_names
        
        print(f"\nSuccessfully created post {post.id} with tags: {tag_names}")
        
    except Exception as e:
        print(f"\nTest Failed with error: {e}")
        raise e

