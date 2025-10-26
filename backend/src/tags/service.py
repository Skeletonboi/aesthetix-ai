from fastapi import status
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from src.tags.models import Tag
from src.tags.schemas import TagCreate
from uuid import UUID
from typing import List


class TagService:
    async def get_all_tags(self, session: AsyncSession):
        statement = select(Tag).order_by(Tag.tag_name.desc())
        res = await session.execute(statement)

        return res.scalars().all()

    async def get_tag_by_id(self, tag_id: UUID, session: AsyncSession):
        statement = select(Tag).where(Tag.tid == tag_id)
        res = await session.execute(statement)

        return res.scalars().first()

    async def get_tag_by_slug(self, tag_slug: str, session: AsyncSession):
        statement = select(Tag).where(Tag.tag_name == tag_slug)
        res = await session.execute(statement)

        return res.scalars().first()

    async def create_tag(self, tag_data: TagCreate, session: AsyncSession):
        tag_dict = tag_data.model_dump()
        new_tag = Tag(**tag_dict)

        session.add(new_tag)
        await session.commit()
        await session.refresh(new_tag)

        return new_tag
    
    async def update_tag(self, tag_id: UUID, tag_data: TagCreate, session: AsyncSession):
        tag = await self.get_tag_by_id(tag_id, session)

        tag_dict = tag_data.model_dump()
        for k, v in tag_dict.items():
            setattr(tag, k, v)
        
        await session.commit()
        await session.refresh(tag)

        return tag

    async def delete_tag(self, tag_id: UUID, session: AsyncSession):
        statement = select(Tag).options(selectinload(Tag.exercises))\
        .where(Tag.tid == tag_id)
        res = await session.execute(statement)
        tag = res.scalar_one_or_none()
        
        if not tag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                    detail="Tag not found.")
    
        tag.exercises.clear()
        await session.flush()

        await session.delete(tag)
        await session.commit()
        return
        # statement = delete(Tag).where(Tag.tid == tag_id)
        # await session.execute(statement)
        # await session.commit()
        # return

    @classmethod
    async def get_tags_from_slugs(cls, tag_slugs: List[str], session: AsyncSession) -> List[Tag]:
        tag_service = cls()
        tags = []
        for tag_slug in tag_slugs:
            tag = await tag_service.get_tag_by_slug(tag_slug, session)

            if not tag:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                                    detail="Tag does not exist.")
            tags.append(tag)
        return tags
        