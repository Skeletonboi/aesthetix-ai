from src.workout_logs.schemas import WorkoutLogResponse
from src.chat.resource_pool import ResourcePool
from src.db.db import get_session_context

import os
import re
from uuid import UUID
import json
from typing import List
from langchain_core.tools import StructuredTool
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import MessagesState, StateGraph, END
from langgraph.prebuilt import ToolNode, InjectedState, tools_condition
from typing import Annotated

class ChatAgent:

    SYSTEM_PROMPT = \
     """You are a 145 IQ fitness and exercise science expert. Your task is to answer the user's query using only information from the retrieved_context.
     Use retrieve_context tool when needed. Invoke the tool multiple times for multiple topic searches.
     Make sure to cite your sources for where each piece of advice came from in the retrieved_context.
     Do not offer any further services after your answer, immediately exit after concluding your answer.

    OUTPUT RULES - CRITICAL:
    - Provide direct, authoritative, specific answers using retrieved context. 
    - DO NOT be vague. DO NOT cast a wide net and give a wide range of numbers/answers.
    - DO NOT include meta-commentary like "Here is...", "Based on my research...", "The retrieved sources show..."
    - DO NOT acknowledge the retrieval process or explain your methodology
    - DO NOT inject your own assumptions or knowledge, use only information from the retrieved context.
    - Write as if you ARE the authoritative source, not a middleman
    - Start immediately with the substantive answer

    WRONG: "Based on the retrieved research, here's what I found about rep ranges..."
    RIGHT: "For maximum hypertrophy, research demonstrates optimal rep ranges of 6-12 repetitions per set..."

    WRONG: "Here is a concise answer to your question:"
    RIGHT: [just start with the actual answer]

    WRONG: "[actual answer] ... If you want I can create a 4 week program outline ..."
    RIGHT: "[actual answer with no further inquiry]"
    """

    def __init__(self, user_uid: UUID):        
        # Assign shared resources
        self.embedder = ResourcePool.embedder
        self.chroma_client = ResourcePool.chroma_client
        self.llm = ResourcePool.llm_chat_model
        self.exa = ResourcePool.exa_client
        self.user_service = ResourcePool.user_service
        # self.workout_logs_service = ResourcePool.workout_logs_service

        self.graph_builder = StateGraph(MessagesState)
        retrieval_tool = StructuredTool.from_function(
            coroutine=self.retrieve_context,
            name="retrieve_context",
            description="Retrieves extra fitness-science information related to the user's query - from textbooks, research papers, and fitness-science youtube video transcript summaries."
        )
        self.tools = ToolNode([retrieval_tool])
        
        self.user_uid = user_uid

    async def initialize_agent(self, state: MessagesState):
        self.user_data = await self.get_user_data()

        if not any(msg.type == "system" for msg in state["messages"]):
            return {"messages": [SystemMessage(self.SYSTEM_PROMPT)] + [HumanMessage(self.user_data)] + state["messages"]}
        else:
            return {}


    async def get_user_data(self):
            """ Collects and serializes user data and workout logs """
            
            async with get_session_context() as session:
                user_info = await self.user_service.get_user_by_id(self.user_uid, session)
                # user_logs = await self.workout_logs_service.get_logs_by_user(self.user_uid, session)
                # user_logs_json = []
                # for log in user_logs:
                #     user_logs_json.append(WorkoutLogResponse.model_validate(log).model_dump(mode='json'))

            user_data = {
                "username" : user_info.username,
                "full_name" : user_info.full_name,
                "age" : user_info.age,
                "height_raw" : user_info.height_raw,
                "height_unit" : user_info.height_unit.value if user_info.height_unit else None,
                # "user_workout_logs" : user_logs_json
            }
            return json.dumps(user_data, indent=2)

    def retrieve_embedded_chunks(self, queries: List[str], n_yt_res=10, n_txtbk_res=5) -> dict:
        # Chromadb retrieval
        collection_yt = self.chroma_client.get_collection(name="yt_transcripts", embedding_function=self.embedder)
        collection_txtbk = self.chroma_client.get_collection(name="txtbks", embedding_function=self.embedder)
        chunks = {'transcript_chunks': [], 'txtbk_chunks': []}
        for query in queries:
            yt_res = collection_yt.query(query_texts=[f"Instruct: Find relevant documents \n Query: {query}"], n_results=n_yt_res)
            chunks['transcript_chunks'].extend(
                [{'chunk': doc, 'title': metadata['title'], 'vid_id': metadata['vid_id']} 
                for doc, metadata in zip(yt_res['documents'][0], yt_res['metadatas'][0])]
                )
            txtbk_res = collection_txtbk.query(query_texts=[f"Instruct: Find relevant documents \n Query: {query}"], n_results=n_txtbk_res)
            chunks['txtbk_chunks'].extend(
                [{'chunk': doc, 'title': metadata['source_title'], 'header': metadata['Header_2']} 
                for doc, metadata in zip(txtbk_res['documents'][0], txtbk_res['metadatas'][0])]
                )

        return chunks
    
    def retrieve_exa_papers(self, queries: List[str], n_results=10):
        results = []
        for query in queries:
            response = self.exa.search_and_contents(
            query.strip(),
            type = "auto",
            category = "research paper",
            summary = True,
            num_results = n_results
            )
            results.extend([
                {
                    'title': paper.title,
                    'url': paper.url,
                    'published_date': paper.published_date,
                    'summary': paper.summary
                }
                for paper in response.results
            ])
        return results

    async def gen_retrieval_queries(self, messages, n_research_max=1, n_embed_max=1, chat_history_max=10):
        """
        Generates queries for research paper search engine querying and transcript summary embedding retrieval respectively
        """

        messages_str = "\n".join([f"{msg.type}: {msg.content}" for msg in messages[-chat_history_max:]])
        research_query_prompt = f"""You are a fitness-science research professional exercise physiology and personal training.  
        Your task: given the chat history and user biometric data below, produce up to {n_research_max} <RESEARCH QUERY> strings optimized to query a scientific paper search engine (Semantic Scholar) and up to {n_embed_max} <EMBEDDING QUERY> strings optimized for semantic vector retrieval from fitness textbooks and video-summary text.  

        OUTPUT RULES (strict):
        - Output ONLY lines that begin with <RESEARCH QUERY> or <EMBEDDING QUERY> followed by a single query string.
        - Produce at least one <RESEARCH QUERY> and one <EMBEDDING QUERY> (unless the corresponding max is 0).
        - Do not exceed {n_research_max} <RESEARCH QUERY> lines or {n_embed_max} <EMBEDDING QUERY> lines.
        - Embedding queries should read like natural language phrases in a textbook or transcript regarding the topic.

        GUIDANCE FOR QUERY CONTENT:
        - Research queries: derive specific muscles, exercises, demographics, or outcomes in scientific language. Utilize only scientifically relevant terms when referring to the physiological body part and phenomenon where applicable. Quotations for exact phrase matching if needed.
        - Embedding queries: create natural-language phrases likely to appear in textbooks or coaching/transcript summaries (exercise execution, coaching cues, technique, programming guidelines, physiological explanations). Avoid using the literal words "textbook" or "transcript" as they obviously won't show up within one.
        - Tailoring: if biometric/training details are given (age, sex, training history, goals), incorporate them into queries appropriately.

        EXPECTED FORMAT (for 2 per):
        <RESEARCH QUERY> research query 1
        <RESEARCH QUERY> research query 2
        <EMBEDDING QUERY> embedding query 1
        <EMBEDDING QUERY> embedding query 2

        User Data: \n {self.user_data}
        
        Messages: \n {messages_str}
        """

        response = await self.llm.ainvoke(research_query_prompt)
        research_queries = re.findall(r"<RESEARCH QUERY>\s*(.+)", response.content)
        embedding_queries = re.findall(r"<EMBEDDING QUERY>\s*(.+)", response.content)

        return [q.strip() for q in research_queries], [q.strip() for q in embedding_queries]

    async def retrieve_context(self, state: Annotated[MessagesState, InjectedState]):
        """
        Retrieves extra fitness-science information related to the user's query - from textbooks, research papers, and fitness-science youtube video transcript summaries. 
        """
        
        # Retrieve context
        print("Generating research queries PENGU")
        research_queries, embedding_queries = await self.gen_retrieval_queries(state['messages'])
        print(f"Research Queries: {research_queries} \n Embedding queries: {embedding_queries}")
        print("Retrieving embedded chunks PENGU")
        chunks = self.retrieve_embedded_chunks(embedding_queries)
        print("Retrieving research papers PENGU")
        papers = self.retrieve_exa_papers(research_queries)
        
        # Serialize to string
        ts_str = f"Transcript Chunks: \n {json.dumps(chunks['transcript_chunks'])}"
        txtbk_str = f"Textbook Chunks: \n {json.dumps(chunks['txtbk_chunks'])}"
        paper_str = f"Research Paper Summaries: \n {json.dumps(papers)}"
        return "\n\n".join([ts_str, txtbk_str, paper_str])

    async def respond_or_retrieve(self, state: MessagesState):
        """Generate tool call for retrieval of fitness-science information or respond directly"""

        llm_with_tools = self.llm.bind_tools([self.retrieve_context])
        response = await llm_with_tools.ainvoke(state["messages"])
        return {"messages": [response]}

    # async def generate(self, state: MessagesState):
    #     # recent_tool_messages = []
    #     # for message in reversed(state["messages"]):
    #     #     if message.type == "tool":
    #     #         recent_tool_messages.append(message)
    #     #     else:
    #     #         break
    #     # tool_messages = recent_tool_messages[::-1]
    #     # context = "\n\n".join(tool_msg.content for tool_msg in tool_messages)

    
    #     prompt = [SystemMessage(system_msg)] + state["messages"]
    #     response = await self.llm.ainvoke(prompt)
    #     return {'messages': [response]}
            
    def build_graph(self):
        self.graph_builder.add_node(self.initialize_agent)
        self.graph_builder.add_node(self.respond_or_retrieve)
        self.graph_builder.add_node(self.tools)
        
        self.graph_builder.set_entry_point("initialize_agent")
        self.graph_builder.add_conditional_edges(
            "respond_or_retrieve",
            tools_condition,
            {END: END, "tools": "tools"}
        )

        self.graph_builder.add_edge("initialize_agent", "respond_or_retrieve")
        self.graph_builder.add_edge("tools", "respond_or_retrieve")
        # self.graph_builder.add_edge("generate", END)

        self.graph = self.graph_builder.compile()

    def stream(self):
        # Not implemented yet
        yield
    
    
    # DEPRECATED OPENALEX SEARCH
    # def retrieve_openalex_papers(self, research_queries: List[str], top_k=5) -> List:
    #     def uninvert_abstract(inverted_abstract: dict):
    #         if not inverted_abstract:
    #             print('MISSING INVERTED ABSTRACT')
    #             return
    #         # Takes the abstract in inverted index form and returns the reassembled string
    #         length = max(max(positions) for positions in inverted_abstract.values()) + 1
    #         reconstruct_arr = [''] * length
    #         for word in inverted_abstract.keys():
    #             for pos in inverted_abstract[word]:
    #                 reconstruct_arr[pos] = word
    #         return ' '.join(reconstruct_arr)

    #     res = []
    #     for query in research_queries:
    #         url = f"https://api.openalex.org/works?search={query}"
    #         response = requests.get(url).json()
    #         inverted_abstracts = [work['abstract_inverted_index'] for work in response['results'][:top_k]]
    #         res.append({"query": query, "abstracts": [uninvert_abstract(abs) for abs in inverted_abstracts]})
    #     return res