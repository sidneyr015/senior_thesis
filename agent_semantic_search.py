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
import re 


from tools.semantic_search_tool import semantic_search_tool
from tools.code_snippet_tool import get_code_snippet


class State(TypedDict): 
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

api_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = api_key

llm = init_chat_model("gpt-4o")

async def find_invariants(state: MessagesState): 
    """
    Example node: call semantic_search, then ask LLM to turn results into a typestate table.
    """
    q = "enum"
    repo_path = "/Users/sidneyrichardson/senior_thesis-1/code_examples/once_cell"
    search = await semantic_search_tool._arun(query=q, mode="all", path=repo_path)
    print("search!")
    entries = parse(search["content"][0]["text"])
    # for entry in entries: 
    #     print(entry)
    return {"entries": entries}

async def decide_snippets(state): 
    entries = state["entries"]
    prompt = """"
            You are an expert Rust engineer and program analysis researcher.
            Your goal is to extract typestate invariants from Rust code, including implicit and explicit rules enforced by the type system, ownership, or lifetimes.

            Context:

            Rust's affine type system enforces single ownership and prevents data races and invalid access.

            Many invariants in Rust are implicit — enforced by generics, lifetimes, and typestate encodings (e.g. File<Open>, Socket<Connected>).

            These invariants ensure temporal order (operations occur legally) and state consistency (resources are only used in valid states).

            Your task:
            Given the Rust code snippet below, identify and fill out a structured table describing the typestate system and invariants it encodes."
            """"

graph = StateGraph(State)
graph.add_node("find_invariants", find_invariants)
graph.add_edge(START, "find_invariants")
graph.add_edge("find_invariants", END)
app = graph.compile()

def parse(text): 
    # Split into individual matches
    chunks = text.split("\n\n\n")  # Triple newline between entries
    parsed = []
    for chunk in chunks:
        print(chunk + "\n")
        lines = [l.strip() for l in chunk.splitlines() if l.strip()]
        if lines and lines[0].startswith(tuple(str(i) + "." for i in range(1, 100))):
            parsed.append("\n".join(lines))
    return chunks

async def main(): 
    state = {"messages": [HumanMessage(content="/Users/sidneyrichardson/senior_thesis-1")]}
    async for s in app.astream(state, stream_mode="values"): 
        print(s)

if __name__ == "__main__":
    asyncio.run(main())
