
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from src.database.session import SessionLocal
from src.apps.interactions.service import get_comments_by_post, create_comment
from src.apps.interactions.schemas import CommentCreate
from src.apps.posts.models import Post
from src.apps.users.models import User
from sqlalchemy import select

async def test_comments():
    async with SessionLocal() as db:
        print("Getting a user and post...")
        user = (await db.execute(select(User))).scalars().first()
        post = (await db.execute(select(Post))).scalars().first()
        
        if not user or not post:
            print("No user or post found. Run seeding first.")
            return

        print(f"User: {user.id}, Post: {post.id}")

        # Test Create Comment
        print("Creating comment...")
        comment_in = CommentCreate(post_id=post.id, content="Test comment")
        try:
            comment = await create_comment(db, comment_in, user.id)
            print(f"Comment created: {comment.id}")
            print(f"Comment User: {comment.user.username}") # Check lazy load
            print(f"Comment Replies: {comment.replies}")     # Check lazy load
            print(f"Comment Likes: {comment.likes}")         # Check lazy load
        except Exception as e:
            print(f"Error creating comment: {e}")
            import traceback
            traceback.print_exc()

        # Test Get Comments
        print("Fetching comments...")
        try:
            comments = await get_comments_by_post(db, post.id, user.id)
            print(f"Fetched {len(comments)} comments.")
            for c in comments:
                print(f"Comment {c.id}: Likes={c.likes_count}, Liked={c.is_liked}")
                for r in c.replies:
                    print(f"  Reply {r.id}: Likes={r.likes_count}, Liked={r.is_liked}")
        except Exception as e:
            print(f"Error fetching comments: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_comments())
