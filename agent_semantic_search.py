from typing import Annotated
from typing_extensions import TypedDict
import asyncio

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.graph.message import add_messages
import os
from langchain.chat_models import init_chat_model
from datetime import datetime
from pathlib import Path 


from tools.semantic_search_tool import semantic_search_tool

class State(TypedDict): 
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

api_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = api_key

llm = init_chat_model("gpt-4o")

async def index(state: MessagesState): 
    """
    call octocode index
    """
    searc 

async def find_invariants(state: MessagesState): 
    """
    Example node: call semantic_search, then ask LLM to turn results into a typestate table.
    """
    q = "enum"
    repo_path = "/Users/sidneyrichardson/senior_thesis-1/code_examples/once_cell"
    search = await semantic_search_tool._arun(query=q, mode="all", path=repo_path)
    print(search)

    return

graph = StateGraph(State)
graph.add_node("find_invariants", find_invariants)
graph.add_edge(START, "find_invariants")
graph.add_edge("find_invariants", END)
app = graph.compile()

async def main(): 
    state = {"messages": [HumanMessage(content="/Users/sidneyrichardson/senior_thesis-1")]}
    async for s in app.astream(state, stream_mode="values"): 
        print(s)

if __name__ == "__main__":
    asyncio.run(main())
