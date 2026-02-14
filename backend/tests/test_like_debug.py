
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from src.database.session import SessionLocal
from src.apps.interactions.service import like_post
from src.apps.posts.models import Post
from src.apps.users.models import User
from sqlalchemy import select

async def test_like():
    async with SessionLocal() as db:
        print("Getting a user and post...")
        user = (await db.execute(select(User))).scalars().first()
        post = (await db.execute(select(Post))).scalars().first()
        
        if not user or not post:
            print("No user or post found.")
            return

        print(f"User: {user.id}, Post: {post.id}")
        print(f"Initial Likes: {post.likes_count}")

        # Test Like
        print("Liking post...")
        try:
            is_liked = await like_post(db, post.id, user.id)
            print(f"Liked? {is_liked}")
            
            # Check count
            await db.refresh(post)
            print(f"New Likes: {post.likes_count}")
            
            # Toggle (Unlike)
            print("Unliking post...")
            is_liked = await like_post(db, post.id, user.id)
            print(f"Liked? {is_liked}")
            
            await db.refresh(post)
            print(f"Final Likes: {post.likes_count}")
            
        except Exception as e:
            print(f"Error liking post: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_like())
