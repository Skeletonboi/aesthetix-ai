import os
from pathlib import Path
from src.chat.chat_agent import ChatAgent
import asyncio
from langchain_core.messages import HumanMessage
from src.chat.resource_pool import ResourcePool
from langchain_core.messages import SystemMessage

# FOR DEV/TESTING PURPOSES ONLY - INTENDED CHATAGENT USAGE IS WITHIN FASTAPI ROUTES
VDB_PATH = os.path.join(Path(__file__).parents[1], "ingestion", "chroma_db")
USER_UID = "2e0ca5dd-1ab2-46b3-b96d-402b69946f90" 

async def main():
    ResourcePool.initialize()

    agent = ChatAgent(
        user_uid=USER_UID,
    )
    # r_queries, e_queries = await agent.gen_retrieval_queries([HumanMessage("What are the best exercises I should be doing for back thickness?")])
    # user_data = await agent.get_user_data()
    # embed_chunks = agent.retrieve_embedded_chunks(e_queries)
    # paper_sums = agent.retrieve_exa_papers(r_queries)

    agent.build_graph()
    # input_message = "What are the best exercises I should be doing for back thickness? Use tools."
    input_message = "What are the best exercises to grow my chest?"
    
    state = await agent.graph.ainvoke(
        {"messages": [{"role": "user", "content": input_message}]},
    )
    final_msg = state["messages"][-1]

    if final_msg.type != "ai":
        print("Last message in state is not AIMessage!")
    print(final_msg)
    import code; code.interact(local=locals())
    
    return 

if __name__ == "__main__":
    asyncio.run(main())
    