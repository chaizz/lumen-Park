from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_db
from src.apps.tags import service, schemas
from src.core import deps

router = APIRouter()

@router.get("/", response_model=List[schemas.TagResponse])
async def read_tags(
    skip: int = 0,
    limit: int = 100,
    type: Optional[str] = Query(None, description="Filter by tag type (lighting, subject, location)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all tags, ordered by popularity.
    """
    tags = await service.get_tags(db, skip=skip, limit=limit, type=type)
    return tags

@router.post("/", response_model=schemas.TagResponse)
async def create_tag(
    tag_in: schemas.TagCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(deps.get_current_user) # Only logged in users can create tags directly
):
    """
    Create a new tag manually.
    """
    return await service.create_tag(db, tag_in)
