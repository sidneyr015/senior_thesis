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
import json


from tools.semantic_search_tool import semantic_search_tool
from tools.code_snippet_tool import get_code_snippet


class State(TypedDict): 
    messages: Annotated[list, add_messages]
    entries: list

api_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = api_key

llm = init_chat_model("gpt-4o")

async def find_invariants(state): 
    """
    Example node: call semantic_search, then ask LLM to turn results into a typestate table.
    """
    print("finding invaraits")
    q = "enum"
    repo_path = "/Users/sidneyrichardson/senior_thesis-1/code_examples/personal_once_cell"
    search = await semantic_search_tool._arun(query=q, mode="all", path=repo_path)
    print("search!")
    entries = parse(search["content"][0]["text"])
    # for entry in entries: 
    #     print(entry)
    return {"entries": entries}

async def fetch_snippets(state): 
    print("Running fetch_snippets, state keys:", list(state.keys()))
    entries = state["entries"]
    prompt = """"
        You analyze Rust code for typestate-based invariants.
        Focus only on compile-time rules involving ownership, generics, and state transitions.

        Identify:

        entity: the struct, enum, or module representing a stateful type

        state_dimensions: how its type encodes state (e.g. generic parameter, trait bound)

        valid_states: all compile-time states (e.g. Closed, Open)

        invariant: one condition that must always hold (temporal or consistency)

        transition: how one state moves to another (e.g. Closed → Open via open())

        evidence_lines: line numbers supporting this invariant

        Return only this JSON:

        {
        "file": "<file_path>",
        "line_range": {"start": <int>, "end": <int>},
        "typestate_table": [
            {
            "entity": "<name>",
            "state_dimensions": "<description>",
            "valid_states": ["<state1>", "<state2>"],
            "invariant": "<rule>",
            "transition": "<transition or '-'>",
            "evidence_lines": [<int>, ...]
            }
        ]
        }
        If none found, return an empty "typestate_table": [].
    """
    results = []
    for entry in entries: 
        code_snippet = get_code_snippet("/Users/sidneyrichardson/senior_thesis-1/code_examples/personal_once_cell/" + entry["file"], entry["start_line"], entry["end_line"])
        response = llm.invoke([
            HumanMessage(content=prompt + "\n\n Please find type_state invariants for this code snippet" + code_snippet)
        ])
        try:
            data = json.loads(response.content)
        except Exception:
            data = {"file": entry["file"], "typestate_table": []}
        results.append(data)
        print(response.content)
        print("\n\n")

    for result in results:
        print(result + "\n\n")
    return {"entries": results}


graph = StateGraph(State)
graph.add_node("find_invariants", find_invariants)
graph.add_node("fetch_snippets", fetch_snippets)
graph.add_edge(START, "find_invariants")
graph.add_edge("find_invariants", "fetch_snippets")
graph.add_edge("fetch_snippets", END)
app = graph.compile()

def parse(text): 
    # Split the search results into separate entries (works for double/triple newlines)
    chunks = re.split(r"\n{2,}", text)
    entries = []

    for chunk in chunks:
        lines = [l.strip() for l in chunk.splitlines() if l.strip()]
        if not lines:
            continue

        # Identify lines like "6. src/imp_pl.rs"
        file_match = re.search(r"(\d+)\.\s+([^\s]+\.rs)", chunk)
        sim_match = re.search(r"Similarity\s+([0-9.]+)", chunk)

        # Extract all numbered code lines (e.g., "45: pub(crate)...")
        line_numbers = [int(m) for m in re.findall(r"^(\d+):", chunk, re.MULTILINE)]

        if file_match and line_numbers:
            entry = {
                "index": int(file_match.group(1)),
                "file": file_match.group(2).strip(),
                "similarity": float(sim_match.group(1)) if sim_match else None,
                "start_line": min(line_numbers),
                "end_line": max(line_numbers),
                "code": "\n".join(chunk.split("\n")[3:]).strip()
            }
            entries.append(entry)
    return entries

async def main(): 
    state = {"messages": [HumanMessage(content="/Users/sidneyrichardson/senior_thesis-1")]}
    async for s in app.astream(state, stream_mode="values"): 
        print(s)

if __name__ == "__main__":
    asyncio.run(main())
