from fastapi import FastAPI, Depends, Request, status
import logging

from src.auth.dependencies import AccessTokenBearer
from src.rag.schemas import RAGRequest, RAGSingleResponse, RAGInternalRequest, ResearchResultFull
from src.rag.rag_service import RAGService
from src.rag.resource_pool import ResourcePool
from src.rag.observability import new_request_id, stage_timer

rag_app = FastAPI()
access_token_bearer = AccessTokenBearer()
logger = logging.getLogger("uvicorn.error")

@rag_app.on_event("startup")
async def startup():
    """Initialize singleton resources on app startup"""
    ResourcePool.initialize()
    rag_app.state.rag_service = RAGService()

def get_rag_service(request: Request) -> RAGService:
    """Dependency injection for RAGService"""
    return request.app.state.rag_service

@rag_app.post("/_full_single_response", response_model=RAGSingleResponse)
async def _full_single_response(
    rag_request: RAGInternalRequest,
    rag_service: RAGService = Depends(get_rag_service)
    ):
    ai_msg = await rag_service.invoke_new_chat(
        rag_request.user_uid, 
        rag_request.msg
    )
    return RAGSingleResponse(ai_msg=ai_msg)

@rag_app.post("/_generate_research", response_model=ResearchResultFull)
async def _generate_research(
    request: Request,
    rag_request: RAGInternalRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    request_id = request.headers.get("x-request-id") or new_request_id()
    with stage_timer(logger, "ml_request_total", request_id):
        research_result = await rag_service.generate_research(
            rag_request.user_uid,
            rag_request.msg,
            rag_request.model_name,
            rag_request.reasoning_enabled,
            request_id=request_id,
        )
    return research_result

@rag_app.get("/_get_available_models", response_model=list[str])
async def _get_available_models(
):
    return ResourcePool.get_available_models()