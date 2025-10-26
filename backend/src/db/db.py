from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from src.config import Config
from src.db.base_model import BaseModel

async_engine = AsyncEngine(create_engine(url=Config.DATABASE_URL, echo=True))

Session = sessionmaker(bind=async_engine, class_=AsyncSession)

async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with Session() as session:
        yield session

@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    async with Session() as session:
        yield session