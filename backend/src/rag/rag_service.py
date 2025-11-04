import uuid
import json
from langchain_core.messages import SystemMessage, HumanMessage
import logging
import re

from src.rag.agent import Agent
from src.rag.retriever import Retriever
from src.rag.resource_pool import ResourcePool
from src.rag.schemas import ResearchResultFull
from datetime import datetime, timezone

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
    
    async def generate_research(self, query: str) -> ResearchResultFull:
        research_queries, embedding_queries = await self.agent.gen_retrieval_queries(query)
        chunks = Retriever.retrieve_embedded_chunks(embedding_queries)
        # papers = Retriever.retrieve_exa_papers(research_queries)

        ts_str = ""
        for i, chunk in enumerate(chunks['transcript_chunks']):
            ts_str += f"<SUMMARY {i+1}> \n Title: {chunk['title']} \n Summary: {chunk['chunk']} \n\n"
        # txtbk_str = f"Textbook Chunks: \n {json.dumps(chunks['txtbk_chunks'])}"
        # paper_str = f"Research Paper Summaries: \n {json.dumps(papers)}"
        prompt = f"""
        Given the following user query, generate an answer to the user query using only the information from each of the retrieved 
        fitness science video transcript summaries. One answer per summary using only the information from each summary.
        Then at the end, generate a <FINAL ANSWER> output that synthesizes a correct 
        answer given ALL of the summaries and the insights extracted from them.

        Each video summary in the list MUST be assessed independently, NO information from any of the other retrieved summaries 
        may be used to generate the answer for a respective video.
        Do not interject your own opinion. 
        Reason and assess the video summary to understand what the actual recommendation made is (if there exists information pertaining 
        to the user query in the summary). If no relevant information exists, indicate as such. 
        Always refer to the summary as a "video".

        Output your answer in the strict format below:

        <SUMMARY 1>
        ... answer from summary 1 ...
        <SUMMARY 2>
        ... answer from summary 2 ...
        ...
        <FINAL ANSWER>
        ... your final answer ...

        Here are the provided user query and summaries:

        Query: {query}

        Summaries:
        {ts_str}
        """
        res = await ResourcePool.llm_chat_model.ainvoke(prompt)
        summaries_pattern = r'<SUMMARY\s+\d+>\s*(.*?)(?=(?:<SUMMARY\s+\d+>|<FINAL ANSWER>|$))'
        llm_chunk_responses = [s.strip() for s in re.findall(summaries_pattern, res.content, re.DOTALL)]

        final_answer_match = re.search(r'<FINAL ANSWER>\s*(.*)', res.content, re.DOTALL)
        llm_final_response = final_answer_match.group(1).strip() if final_answer_match else None

        research_obj = ResearchResultFull(
            result_id = str(uuid.uuid4()),
            user_uid = None,
            user_query = query,
            created_at = None,
            research_queries = research_queries,
            embedding_queries = embedding_queries,
            transcript_chunks = chunks['transcript_chunks'],
            txtbk_chunks = chunks['txtbk_chunks'],
            research_papers=None,
            llm_chunk_response=llm_chunk_responses,
            llm_final_response=llm_final_response
        )

        return research_obj