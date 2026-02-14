import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from src.database.session import SessionLocal
from src.apps.posts.service import get_bookmarked_posts, get_liked_posts
from src.apps.users.models import User
from sqlalchemy import select

async def test_lists():
    async with SessionLocal() as db:
        print("Getting a user...")
        user = (await db.execute(select(User))).scalars().first()
        
        if not user:
            print("No user found.")
            return

        print(f"Testing for User: {user.id}")

        print("--- Testing Bookmarked Posts ---")
        try:
            posts = await get_bookmarked_posts(db, user.id)
            print(f"Found {len(posts)} bookmarked posts.")
            for p in posts:
                print(f"Post: {p.id}")
                for img in p.images:
                    print(f"  Image: {img.id}")
                    # Trigger loading
                    print(f"    Exif: {img.exif}") 
                    print(f"    Recipe: {img.recipe}")
            print("Bookmarked posts test passed!")
        except Exception as e:
            print(f"Error getting bookmarked posts: {e}")
            import traceback
            traceback.print_exc()

        print("\n--- Testing Liked Posts ---")
        try:
            posts = await get_liked_posts(db, user.id)
            print(f"Found {len(posts)} liked posts.")
            for p in posts:
                print(f"Post: {p.id}")
                for img in p.images:
                    print(f"  Image: {img.id}")
                    # Trigger loading
                    print(f"    Exif: {img.exif}")
                    print(f"    Recipe: {img.recipe}")
            print("Liked posts test passed!")
        except Exception as e:
            print(f"Error getting liked posts: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_lists())
