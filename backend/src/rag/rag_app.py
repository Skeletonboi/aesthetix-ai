from fastapi import FastAPI, Depends, status

from src.auth.dependencies import AccessTokenBearer
from src.rag.schemas import RAGSingleResponse, RAGInternalRequest
from src.rag.rag_service import RAGService
from src.rag.resource_pool import ResourcePool

rag_app = FastAPI()
access_token_bearer = AccessTokenBearer()
rag_service = RAGService()

@rag_app.on_event("startup")
async def startup():
    ResourcePool.initialize()

@rag_app.post("/_full_single_response", response_model=RAGSingleResponse)
async def _full_single_response(
    rag_request: RAGInternalRequest,
    ):
    ai_msg = await rag_service.invoke_new_chat(
        rag_request.user_uid, 
        rag_request.msg
    )
    return RAGSingleResponse(ai_msg=ai_msg)

# @chat_app.post("/ ")