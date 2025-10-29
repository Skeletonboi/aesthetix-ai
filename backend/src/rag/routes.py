from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
import httpx
from uuid import UUID

# from sqlalchemy.ext.asyncio import AsyncSession
# from src.db.db import get_session
from src.rag.schemas import RAGRequest, RAGSingleResponse
from src.auth.dependencies import AccessTokenBearer
from src.config import Config

rag_router = APIRouter()
access_token_bearer = AccessTokenBearer()

@rag_router.post("/full_single_response", response_model=RAGSingleResponse)
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