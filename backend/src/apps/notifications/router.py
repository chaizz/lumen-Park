import asyncio
import json
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.apps.notifications import schemas, service
from src.apps.notifications.service import manager
from src.apps.users.models import User
from src.core import deps
from src.database.session import get_db

router = APIRouter()

@router.get("/", response_model=List[schemas.NotificationResponse])
async def read_notifications(
    skip: int = 0,
    limit: int = 20,
    type: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user's notifications.
    """
    return await service.get_notifications(
        db, user_id=current_user.id, skip=skip, limit=limit, type=type
    )

@router.get("/unread-count", response_model=schemas.UnreadCount)
async def read_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    count = await service.get_unread_count(db, user_id=current_user.id)
    return {"count": count}

@router.post("/{id}/read", response_model=schemas.NotificationResponse)
async def mark_as_read(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    notification = await service.mark_as_read(db, notification_id=id, user_id=current_user.id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification

@router.post("/read-all")
async def mark_all_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    await service.mark_all_as_read(db, user_id=current_user.id)
    return {"message": "All marked as read"}

@router.get("/stream")
async def stream_notifications(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    SSE Endpoint.
    """
    # Authenticate manually since EventSource doesn't support headers
    user = await deps.get_current_user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    async def event_generator():
        queue = await manager.connect(user.id)
        try:
            while True:
                # Wait for messages
                # Add timeout to send keep-alive
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(data)}\n\n"
                except asyncio.TimeoutError:
                    # Send comment as keep-alive to prevent connection close
                    yield ": keep-alive\n\n"
        except asyncio.CancelledError:
            manager.disconnect(user.id, queue)
            print(f"Stream cancelled for user {user.id}")

    return StreamingResponse(event_generator(), media_type="text/event-stream")
