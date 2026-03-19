import re
import json
from typing import List
from langchain_core.tools import StructuredTool
from langgraph.graph import MessagesState, StateGraph, END
from langgraph.prebuilt import ToolNode, InjectedState, tools_condition
from typing import Annotated

from src.rag.retriever import Retriever
from src.rag.resource_pool import ResourcePool

class Agent():
    """ 
    Class for all LLM invoking methods and LangGraph/LangChain graph methods.
    Note: This class must be instantiated before being used!
    """

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
    CHAT_HISTORY_MAX = 10   

    def __init__(self):
        self.graph_builder = StateGraph(MessagesState)
        self.graph = self.build_graph()

    # Tool function (binded at initialization)
    async def retrieve_context(self, state: Annotated[MessagesState, InjectedState]):
        """
        Retrieves extra fitness-science information related to the user's query - from textbooks, research papers, and fitness-science youtube video transcript summaries. 
        """
        
        # Retrieve context
        print("Generating research queries PENGU")
        context_str = "\n".join([f"{msg.type}: {msg.content}" for msg in state['messages'][-self.CHAT_HISTORY_MAX:]])

        research_queries, embedding_queries = await self.gen_retrieval_queries(context_str)
        print(f"Research Queries: {research_queries} \n Embedding queries: {embedding_queries}")
        print("Retrieving embedded chunks PENGU")
        chunks = Retriever.retrieve_embedded_chunks(embedding_queries)
        print("Retrieving research papers PENGU")
        papers = Retriever.retrieve_exa_papers(research_queries)
        
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
        """ Builds LangGraph graph by constructing tool nodes and edge relationships """
        
        retrieval_tool = StructuredTool.from_function(
            coroutine=self.retrieve_context,
            name="retrieve_context",
            description="Retrieves extra fitness-science information related to the user's query - from textbooks, research papers, and fitness-science youtube video transcript summaries."
        )
        tools = ToolNode([retrieval_tool])

        self.graph_builder.add_node(self.respond_or_retrieve)
        self.graph_builder.add_node(tools)
        
        self.graph_builder.set_entry_point("respond_or_retrieve")
        self.graph_builder.add_conditional_edges(
            "respond_or_retrieve",
            tools_condition,
            {END: END, "tools": "tools"}
        )

        self.graph_builder.add_edge("tools", "respond_or_retrieve")

        return self.graph_builder.compile()

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