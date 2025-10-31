from uuid import UUID
import json
from langchain_core.messages import SystemMessage, HumanMessage
import logging

from src.rag.agent import Agent
from src.rag.retriever import Retriever
from src.rag.resource_pool import ResourcePool


logger = logging.getLogger(__name__)

class RAGService():
    " Class for all RAG/chat endpoint services "

    def __init__(self):
        self.agent = Agent()

    async def invoke_new_chat(self, user_uid: str, query: str, to_cache=False):
        """
        Creates a new message history and agent response given a user (user ID) and initial query message.
        """
        user_data = await Retriever.get_user_data(user_uid)
        user_data_str = json.dumps(user_data, indent=2)

        # note: user data is seeded into the conversation to provide user context to all LLM invocations using the state
        state = await self.agent.graph.ainvoke({"messages": [SystemMessage(self.agent.SYSTEM_PROMPT)] + [HumanMessage(user_data_str)] + [HumanMessage(query)]})

        # TBD: Caching
        if to_cache:
            pass

        final_msg = state["messages"][-1]

        if final_msg.type != "ai":
            logger.warning(f"Last message is not an AIMessage. \n Type: {final_msg.type} \n Content: {final_msg.content}")

        return final_msg
    
    async def generate_research(self, query: str):
        research_queries, embedding_queries = await self.agent.gen_retrieval_queries(query)
        chunks = Retriever.retrieve_embedded_chunks(embedding_queries)
        # papers = Retriever.retrieve_exa_papers(research_queries)
        import code; code.interact(local=locals())
        ts_str = ""
        for i, chunk in enumerate(chunks['transcript_chunks']):
            ts_str += f"<SUMMARY {i+1}> \n Title: {chunk['title']} \n Summary: {chunk['chunk']} \n\n"
        # txtbk_str = f"Textbook Chunks: \n {json.dumps(chunks['txtbk_chunks'])}"
        # paper_str = f"Research Paper Summaries: \n {json.dumps(papers)}"
        prompt = f"""
        Given the following user query, generate an answer to the user query using only the information from each of the retrieved 
        fitness science video transcript summaries.
        Each video summary in the list MUST be assessed independently, NO information from any of the other retrieved summaries 
        may be used to generate the answer for a respective video.
        Do not interject your own opinion. 
        Reason and assess the video summary to understand what the actual recommendation made is (if there exists information pertaining 
        to the user query in the summary). If no relevant information exists, indicate as such. 
        Always refer to the summary as a "video".

        Output your answer in a list delimited by a newline character.

        EXAMPLE:
        1.
        <ANSWER FROM SUMMARY 1>
        2.
        <ANSWER FROM SUMMARY 2>
        ...

        Query: {query}

        Summaries:
        {ts_str}
        """
        res = await ResourcePool.llm_chat_model.ainvoke(prompt)
        
        return res, prompt, embedding_queries, chunks