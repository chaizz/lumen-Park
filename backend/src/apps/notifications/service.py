from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.apps.notifications.models import Notification

async def get_notifications(db: AsyncSession, user_id: str, skip: int = 0, limit: int = 50) -> list[Notification]:
    result = await db.execute(
        select(Notification)
        .filter(Notification.recipient_id == user_id)
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def mark_as_read(db: AsyncSession, notification_id: str, user_id: str) -> Notification | None:
    result = await db.execute(
        select(Notification).filter(Notification.id == notification_id, Notification.recipient_id == user_id)
    )
    notification = result.scalars().first()
    if notification:
        notification.is_read = True
        await db.commit()
        await db.refresh(notification)
    return notification
