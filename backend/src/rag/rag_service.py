from uuid import UUID
import json
from langchain_core.messages import SystemMessage, HumanMessage
import logging

from src.rag.agent import Agent
from src.rag.retriever import Retriever

agent = Agent()
logger = logging.getLogger(__name__)

class RAGService():
    " Class for all RAG/chat endpoint services "

    async def invoke_new_chat(user_uid: str, query: str):
        """
        Creates a new message history and agent response given a user (user ID) and initial query message.
        """
        user_data = await Retriever.get_user_data(user_uid)
        user_data_str = json.dumps(user_data, indent=2)

        state = await agent.graph.ainvoke({"messages": [SystemMessage(agent.SYSTEM_PROMPT)] + [HumanMessage(user_data_str)] + [HumanMessage(query)]})

        final_msg = state["messages"][-1]

        if final_msg.type != "ai":
            logger.warning(f"Last message is not an AIMessage. \n Type: {final_msg.type} \n Content: {final_msg.content}")

        return final_msg
    
        