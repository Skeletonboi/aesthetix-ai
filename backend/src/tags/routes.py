from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.dependencies import AccessTokenBearer, RoleChecker
from src.db.db import get_session
from src.tags.schemas import TagBase, TagCreate
from src.tags.service import TagService
from typing import List
from fastapi.exceptions import HTTPException
from uuid import UUID

tag_router = APIRouter()
tag_service = TagService()
access_token_bearer = AccessTokenBearer()
role_checker = RoleChecker(["user", "admin"])


@tag_router.get("/all", response_model=List[TagBase], dependencies=[Depends(role_checker)])
async def get_all_tags(
    session: AsyncSession = Depends(get_session)
):
    tags = await tag_service.get_all_tags(session)
    
    return tags


@tag_router.get("/{tag_id}", response_model=TagBase, dependencies=[Depends(role_checker)])
async def get_tag_by_id(
    tag_id: UUID, # auto type coercion
    session: AsyncSession = Depends(get_session)
):
    tag = await tag_service.get_tag_by_id(tag_id, session)

    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found.")
    
    return tag


@tag_router.post("/", status_code=status.HTTP_201_CREATED, response_model=TagBase, 
                 dependencies=[Depends(role_checker)])
async def create_tag(
    tag_data: TagCreate,
    session: AsyncSession = Depends(get_session)
):
    new_tag = await tag_service.create_tag(tag_data, session)

    return new_tag


@tag_router.patch("/{tag_id}", response_model=TagBase, dependencies=[Depends(role_checker)])
async def update_tag(
    tag_id: UUID,
    tag_data: TagCreate,
    session: AsyncSession = Depends(get_session)
):
    updated_tag = await tag_service.update_tag(tag_id, tag_data, session)

    return updated_tag


@tag_router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT, 
                   dependencies=[Depends(role_checker)])
async def delete_tag(
    tag_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    if not await tag_service.get_tag_by_id(tag_id, session):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempted to delete non-existing tag.")
    
    _ = await tag_service.delete_tag(tag_id, session)

    return