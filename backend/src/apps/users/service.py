from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from src.apps.users.models import User
from src.apps.users.schemas import UserCreate, UserUpdate
from src.apps.interactions.models import Follow
from src.apps.posts.models import Post
from src.core.security import get_password_hash

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalars().first()

async def get_user(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()

async def create_user(db: AsyncSession, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        avatar=user.avatar,
        bio=user.bio
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_user_stats(db: AsyncSession, user_id: str) -> dict:
    """
    Get user statistics:
    - followers_count
    - following_count
    - likes_count (received on all posts)
    """
    # 1. Followers
    followers_query = select(func.count(Follow.follower_id)).where(Follow.followed_id == user_id)
    followers_result = await db.execute(followers_query)
    followers_count = followers_result.scalar_one() or 0
    
    # 2. Following
    following_query = select(func.count(Follow.followed_id)).where(Follow.follower_id == user_id)
    following_result = await db.execute(following_query)
    following_count = following_result.scalar_one() or 0
    
    # 3. Likes Received
    likes_query = select(func.sum(Post.likes_count)).where(Post.user_id == user_id)
    likes_result = await db.execute(likes_query)
    likes_count = likes_result.scalar_one() or 0
    
    return {
        "followers_count": followers_count,
        "following_count": following_count,
        "likes_count": int(likes_count) if likes_count else 0
    }

async def update_user(db: AsyncSession, db_user: User, user_in: UserUpdate) -> User:
    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        hashed_password = get_password_hash(update_data["password"])
        update_data["hashed_password"] = hashed_password
        del update_data["password"]
        
    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
