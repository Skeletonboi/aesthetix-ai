from unittest import result
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import json
import httpx

from src.rag.models import ResearchResult
from src.db.redis_cache import cache_research_response, get_cached_research_response
from src.config import Config
from src.rag.schemas import RAGRequest

class ResearchService:
    async def get_all_user_research_history(self, user_uid: UUID, session: AsyncSession, limit=50):
        stmnt = select(
            ResearchResult.result_id,
            ResearchResult.user_query,
            ResearchResult.created_at
            )\
            .where(ResearchResult.user_uid == user_uid)\
            .order_by(ResearchResult.created_at.desc())\
            .limit(limit)
        res = await session.execute(stmnt)

        return res.all()

    async def get_research_by_result_id(self, result_id: UUID, session: AsyncSession):
        # Ping cache first
        cache_res = get_cached_research_response(str(result_id))
        if cache_res:
            return json.loads(cache_res)
        
        stmnt = select(ResearchResult).where(ResearchResult.result_id == result_id)
        res = await session.execute(stmnt)

        return res.scalars().first()
    
    async def generate_new_research(self, rag_request: RAGRequest):
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{Config.ML_SERVICE_ENDPOINT}/_generate_research",
                json=rag_request.model_dump(),
                timeout=120.0
            )
        return res.json()
