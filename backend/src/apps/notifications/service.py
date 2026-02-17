import asyncio
from typing import Dict, List
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, update, and_
from src.apps.notifications.models import Notification, NotificationType
from src.apps.notifications.schemas import NotificationCreate, NotificationUpdate

# --- Connection Manager for SSE ---
class ConnectionManager:
    def __init__(self):
        # user_id -> List[Queue] (support multiple devices/tabs)
        self.active_connections: Dict[str, List[asyncio.Queue]] = {}

    async def connect(self, user_id: str) -> asyncio.Queue:
        queue = asyncio.Queue()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(queue)
        print(f"User {user_id} connected. Active connections: {len(self.active_connections.get(user_id, []))}")
        return queue

    def disconnect(self, user_id: str, queue: asyncio.Queue):
        if user_id in self.active_connections:
            if queue in self.active_connections[user_id]:
                self.active_connections[user_id].remove(queue)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        print(f"User {user_id} disconnected.")

    async def send_personal_message(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            for queue in self.active_connections[user_id]:
                await queue.put(message)
            print(f"Sent message to user {user_id}: {message}")

manager = ConnectionManager()

# --- Service Functions ---

from src.apps.users.models import User

# ... existing code ...

async def create_notification(db: AsyncSession, notification_in: NotificationCreate) -> Notification:
    # Business Logic: Avoid duplicate notifications for same action (e.g. repeated likes)
    # For LIKE type, check if unread notification exists
    if notification_in.type == NotificationType.LIKE:
        stmt = select(Notification).where(
            and_(
                Notification.recipient_id == notification_in.recipient_id,
                Notification.sender_id == notification_in.sender_id,
                Notification.type == NotificationType.LIKE,
                Notification.post_id == notification_in.post_id,
                Notification.is_read == False
            )
        )
        result = await db.execute(stmt)
        existing = result.scalars().first()
        if existing:
            # Update timestamp to bring it to top? Or just ignore.
            # Let's ignore to avoid spam.
            return existing

    db_notification = Notification(**notification_in.model_dump())
    db.add(db_notification)
    await db.commit()
    await db.refresh(db_notification)
    
    # Real-time Push via SSE
    # We need to construct the payload.
    # Ideally we should fetch sender info to display "Alice liked your post"
    sender_name = "Someone"
    sender_avatar = None
    
    if db_notification.sender_id:
        user_result = await db.execute(select(User).where(User.id == db_notification.sender_id))
        sender = user_result.scalars().first()
        if sender:
            sender_name = sender.username
            sender_avatar = sender.avatar

    # Get unread count to push
    unread_count = await get_unread_count(db, notification_in.recipient_id)
    
    push_payload = {
        "type": notification_in.type.value,
        "unread_count": unread_count,
        "data": {
            "id": db_notification.id,
            "sender": {
                "id": db_notification.sender_id,
                "username": sender_name,
                "avatar": sender_avatar
            },
            "content": db_notification.content
        }
    }
    
    await manager.send_personal_message(notification_in.recipient_id, push_payload)
    
    return db_notification

async def get_notifications(
    db: AsyncSession, 
    user_id: str, 
    skip: int = 0, 
    limit: int = 20,
    type: str = None
) -> List[Notification]:
    query = select(Notification).where(Notification.recipient_id == user_id)
    
    if type:
        query = query.where(Notification.type == type)
        
    query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
    
    # Eager load sender for UI display
    from sqlalchemy.orm import selectinload
    query = query.options(selectinload(Notification.sender))
    
    result = await db.execute(query)
    return result.scalars().all()

async def get_unread_count(db: AsyncSession, user_id: str) -> int:
    stmt = select(func.count()).select_from(Notification).where(
        and_(Notification.recipient_id == user_id, Notification.is_read == False)
    )
    result = await db.execute(stmt)
    return result.scalar() or 0

async def mark_as_read(db: AsyncSession, notification_id: str, user_id: str) -> Notification:
    stmt = update(Notification).where(
        and_(Notification.id == notification_id, Notification.recipient_id == user_id)
    ).values(is_read=True)
    await db.execute(stmt)
    await db.commit()
    
    # Fetch updated notification
    result = await db.execute(select(Notification).where(Notification.id == notification_id))
    return result.scalars().first()

async def mark_all_as_read(db: AsyncSession, user_id: str):
    stmt = update(Notification).where(
        and_(Notification.recipient_id == user_id, Notification.is_read == False)
    ).values(is_read=True)
    await db.execute(stmt)
    await db.commit()
