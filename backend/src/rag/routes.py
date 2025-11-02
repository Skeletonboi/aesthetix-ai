from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from uuid import UUID

# from sqlalchemy.ext.asyncio import AsyncSession
# from src.db.db import get_session
from src.rag.schemas import RAGRequest, RAGSingleResponse, ResearchResultFull, ResearchResultHistoryItem
from src.auth.dependencies import AccessTokenBearer
from src.config import Config
from src.rag.service import ResearchService
from src.db.db import get_session

rag_router = APIRouter()
access_token_bearer = AccessTokenBearer()
research_service = ResearchService()

@rag_router.post("/chat", response_model=RAGSingleResponse)
async def full_single_response(
    rag_request: RAGRequest,
    token_details: dict = Depends(access_token_bearer)
    ):
    user_uid = token_details["user"]["uid"]
    rag_json = rag_request.model_dump()
    rag_json["user_uid"] = user_uid
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{Config.ML_SERVICE_ENDPOINT}/_full_single_response",
            json=rag_json,
            timeout=120.0
        )

    return res.json()

@rag_router.get("/research/{result_id}", response_model=ResearchResultFull)
async def get_research_by_id(
    result_id: UUID,
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_bearer)
):
    res = await research_service.get_research_by_result_id(result_id, session)
    return res

@rag_router.get("/research/all", response_model=list[ResearchResultHistoryItem])
async def get_all_user_research_history(
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_bearer)
):
    user_uid = UUID(token_details['user']['uid'])
    res = await research_service.get_all_user_research_history(user_uid, session)

    return res

@rag_router.post("/research", response_model=ResearchResultFull)
async def generate_new_research(
    rag_request: RAGRequest,
    token_details: dict = Depends(access_token_bearer)
):
    res = await research_service.generate_new_research(rag_request)

    return res