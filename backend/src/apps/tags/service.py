from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List, Optional

from src.apps.tags.models import Tag
from src.apps.tags.schemas import TagCreate, TagUpdate
from src.common.constants import TAG_TO_CATEGORY

async def get_tag_by_name(db: AsyncSession, name: str) -> Optional[Tag]:
    result = await db.execute(select(Tag).where(Tag.name == name))
    return result.scalars().first()

async def create_tag(db: AsyncSession, tag_in: TagCreate) -> Tag:
    # Check if tag already exists
    existing_tag = await get_tag_by_name(db, tag_in.name)
    if existing_tag:
        return existing_tag
    
    db_tag = Tag(**tag_in.model_dump())
    db.add(db_tag)
    await db.commit()
    await db.refresh(db_tag)
    return db_tag

async def get_tags(db: AsyncSession, skip: int = 0, limit: int = 100, type: Optional[str] = None) -> List[Tag]:
    query = select(Tag)
    if type:
        query = query.where(Tag.type == type)
    
    # Order by count desc (popular tags first)
    query = query.order_by(Tag.count.desc(), Tag.name)
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

async def increment_tag_count(db: AsyncSession, tag_id: str):
    tag = await db.get(Tag, tag_id)
    if tag:
        tag.count += 1
        await db.commit()

async def get_or_create_tags(db: AsyncSession, tag_names: List[str]) -> List[Tag]:
    """
    Given a list of tag names, return list of Tag objects.
    Create new ones if they don't exist.
    """
    tags = []
    for name in tag_names:
        name = name.strip()
        if not name: continue
        
        # Use centralized mapping for type inference
        tag_type = TAG_TO_CATEGORY.get(name, "other")

        tag_in = TagCreate(name=name, type=tag_type)
        tag = await create_tag(db, tag_in)
        tags.append(tag)
    return tags
