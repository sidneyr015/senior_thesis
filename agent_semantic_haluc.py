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
from prompts.prompt_11_13 import prompt as prompt_typestate_extraction


from tools.semantic_search_tool import semantic_search_tool
from tools.code_snippet_tool import get_code_snippet

""""
Improvements for Semantic Search Haluc Agent:
- Fix entity name assignment to use "qualified_name" from graph nodes.
- Add better get_code_snippet handling for including comments. 
 
"""

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
    print("finding invariants")
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
    prompt = prompt_typestate_extraction
    results = []
    total_tokens = 0

    output_path = ""

    for entry in entries: 
        code_snippet = get_code_snippet("/Users/sidneyrichardson/senior_thesis-1/code_examples/personal_once_cell/" + entry["file"], entry["start_line"], entry["end_line"])
        response = llm.invoke([
            HumanMessage(content=prompt + "\n\n Please find type_state invariants for this code snippet" + code_snippet)
        ])

        if hasattr(response, 'response_metadata'):
            usage = response.response_metadata.get('token_usage', {})
            total_tokens += usage.get('total_tokens', 0)
            #print(f"Tokens used: {usage}")
                  
        raw = response.content
        match = re.search(r"```json\s*(\{.*\})\s*```", raw, re.DOTALL)
        if match:
            json_text = match.group(1)
        else:
            json_text = raw.strip()

        try: 
            if json_text: 
                data = json.loads(json_text)
                data["file"] = entry["file"]
                results.append(data)
        except:
            continue
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")  # use underscores, not slashes
        results_dir = Path("results") / timestamp
        results_dir.mkdir(parents=True, exist_ok=True)

        output_path = results_dir / "personal_once_cell.json"

        output = {
            "agent": "semantic_search_haluc_agent",
            "prompt": prompt,
            "results": results,
            "token_usage": total_tokens,
            "timestamp": datetime.utcnow().isoformat(),
        }

        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)
    
    fix_entity_name(output_path)

    return {"entries": results}

def fix_entity_name(output_name: str) -> None: 
    # Load typestate output
    with open(output_name, "r") as f:
        ts = json.load(f)
        
    # Load graph
    with open("code_examples/my_graph.json") as f: 
        graph_data = json.load(f)

    # Build fast lookup: start_line → node
    line_index = {}

    for node in graph_data["nodes"]:
        props = node["properties"]
        if "start_line" in props and "end_line" in props:
            for ln in range(props["start_line"] - 1, props["end_line"] + 1):
                line_index[ln] = node

    # For every result block in typestate output
    for result in ts.get("results", []):
        line_start = result["line_range"]["start"]

        # Get the matching node using start_line
        node = line_index.get(line_start)

        # If found, extract the qualified_name
        if node:
            qname = node["properties"].get("qualified_name")
            
            # Update all state rows inside the typestate_table
            for entry in result.get("typestate_table", []):
                entry["qualified_name"] = qname

    # Write back the modified file
    with open(output_name, "w") as f:
        json.dump(ts, f, indent=2)

    print("Entity names updated using graph qualified names.")

    return output_name

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
        continue

if __name__ == "__main__":
    asyncio.run(main())
