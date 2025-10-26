from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
import httpx
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from src.chat.schemas import ChatRequest, ChatSingleResponse
# from src.db.db import get_session
from src.auth.dependencies import AccessTokenBearer
from src.config import Config

chat_router = APIRouter()
access_token_bearer = AccessTokenBearer()

@chat_router.post("/full_single_response", response_model=ChatSingleResponse)
async def full_single_response(
    chat_request: ChatRequest,
    token_details: dict = Depends(access_token_bearer)
    ):
    user_uid = token_details["user"]["uid"]
    chat_json = chat_request.model_dump()
    chat_json["user_uid"] = user_uid
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{Config.ML_SERVICE_ENDPOINT}/_full_single_response",
            json=chat_json,
            timeout=120.0
        )

    return res.json()