from fastapi import FastAPI, Depends, status
from uuid import UUID
import logging

from src.chat.schemas import ChatSingleResponse, ChatInternalRequest
from src.auth.dependencies import AccessTokenBearer
from src.chat.chat_agent import ChatAgent
from src.chat.resource_pool import ResourcePool

logger = logging.getLogger(__name__)

chat_app = FastAPI()
access_token_bearer = AccessTokenBearer()

@chat_app.on_event("startup")
async def startup():
    ResourcePool.initialize()

@chat_app.post("/_full_single_response", response_model=ChatSingleResponse)
async def _full_single_response(
    chat_request: ChatInternalRequest,
    ):
    agent = ChatAgent(chat_request.user_uid)
    agent.build_graph()

    state = await agent.graph.ainvoke(
        {"messages": [
            {
                "role": "user", 
                "content": chat_request.msg
            }
            ]
        },
    )
    final_msg = state["messages"][-1]

    if final_msg.type != "ai":
        logger.warning(f"Last message is not an AIMessage. \n Type: {final_msg.type} \n Content: {final_msg.content}")
    
    return ChatSingleResponse(ai_msg=final_msg.content)