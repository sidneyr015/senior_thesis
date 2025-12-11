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
from prompts.clean_up_prompt import prompt as prompt_clean_up
from prompts.dedupe import PAIRWISE_PROMPT


from tools.semantic_search_tool import semantic_search_tool
from tools.code_snippet_tool import get_code_snippet

improvements_note = """"
Improvements for Semantic Search Haluc Agent:
- Fix entity name assignment to use "qualified_name" from graph nodes.
- Add better get_code_snippet handling for including comments. 
- Dehallucination 
- Combining duplicate entries and invariants 
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
    for entry in entries: 
        print(entry)
    return {"entries": entries}

async def fetch_snippets(state): 
    print("Running fetch_snippets, state keys:", list(state.keys()))
    entries = state["entries"]
    prompt = prompt_typestate_extraction
    results = []
    total_tokens = 0

    output_path = ""

    for entry in entries: 
        expanded_start_line, code_snippet = get_code_snippet("/Users/sidneyrichardson/senior_thesis-1/code_examples/personal_once_cell/" + entry["file"], entry["start_line"], entry["end_line"])
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
                data["expanded_start_line"] = expanded_start_line
                results.append(data)
        except:
            continue
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")  # use underscores, not slashes
        results_dir = Path("results") / timestamp
        results_dir.mkdir(parents=True, exist_ok=True)

        output_path = results_dir / "personal_once_cell.json"

        output = {
            "agent": "semantic_search_haluc_agent",
            "description": improvements_note,
            "prompt": prompt,
            "results": results,
            "token_usage": total_tokens,
            "timestamp": datetime.utcnow().isoformat(),
        }

        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)
    
    find_qualified_names(output_path)

    return {"entries": results}

def fix_hallucinations(output_path: str) -> None:
    with open(output_path, "r") as f:
        ts = json.load(f)

    prompt = prompt_clean_up
    results = []
    total_tokens = 0

    output_path = ""

    for entry in ts.get("results", []):
        expanded_start_line, code_snippet = get_code_snippet("/Users/sidneyrichardson/senior_thesis-1/code_examples/personal_once_cell/" + entry["file"], int(entry["line_range"]["start"]), int(entry["line_range"]["end"]))

        qualified_name = ""
        try: 
            qualified_name = (entry.get("typestate_table", [])[0].get("qualified_name", "N/A"))
        except:
            continue
        
        print(prompt + "Code snippet: \n" + code_snippet + " \n Entry: \n" + json.dumps(entry) + "\n Qualified Name: \n" + qualified_name + "\n")
        response = llm.invoke([
            HumanMessage(content=prompt + "Code snippet: \n" + code_snippet + "Entry: \n" + json.dumps(entry) + "Qualified Name: \n" + qualified_name + "\n")
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
                data["expanded_start_line"] = expanded_start_line
                results.append(data)
        except:
            continue
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M") 
        results_dir = Path("results") / timestamp
        results_dir.mkdir(parents=True, exist_ok=True)

        output_path = results_dir / "personal_once_cell.json"

        output = {
            "agent": "semantic_search_haluc_agent",
            "description": "hallucination attempted fix",
            "prompt": prompt,
            "results": results,
            "token_usage": total_tokens,
            "timestamp": datetime.utcnow().isoformat(),
        }

        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)
    
    return {"entries": results}



def find_qualified_names(output_name: str) -> None: 
    # Load typestate output
    with open(output_name, "r") as f:
        ts = json.load(f)
   
    for result in ts.get("results", []):
        continue

    
        
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


PAIRWISE_INVARIANT_PROMPT = """
Given two invariants:

A: {A}
B: {B}

Are they describing the same underlying constraint or condition, even if phrased differently?

Answer with exactly ONE WORD:
"SAME" or "DIFFERENT".
"""


def llm_equivalent(inv_a, inv_b):
    """Ask LLM if two invariants mean the same thing."""
    prompt = PAIRWISE_INVARIANT_PROMPT.format(A=inv_a, B=inv_b)
    resp = llm.invoke([HumanMessage(content=prompt)])
    return resp.content.strip().lower().startswith("same")


def normalize_entry(entry):
    """Ensure evidence_lines is list-of-lists aligned with invariants."""

    invs = entry.get("invariants", [])
    evs  = entry.get("evidence_lines", [])

    # Already paired → nothing to do
    if len(evs) > 0 and isinstance(evs[0], list):
        return entry

    # Convert [33,117] → [[33],[117]]
    new_evs = []
    for ev in evs:
        new_evs.append([ev])

    # Align lengths (rare, but safe)
    if len(new_evs) < len(invs):
        # pad evidence for missing invariants
        new_evs.extend([[] for _ in range(len(invs) - len(new_evs))])
    elif len(new_evs) > len(invs):
        # trim extra evidence
        new_evs = new_evs[:len(invs)]

    entry["evidence_lines"] = new_evs
    return entry


def merge_state(base, new):
    """
    Merge invariants and evidence from 'new' into 'base'.
    Only merges when LLM says an invariant matches semantically.
    Otherwise appends as new.
    """

    base_invs = base["invariants"]
    base_evs  = base["evidence_lines"]

    new_invs = new["invariants"]
    new_evs  = new["evidence_lines"]

    for inv, ev in zip(new_invs, new_evs):
        merged = False

        for i, base_inv in enumerate(base_invs):
            if llm_equivalent(inv, base_inv):
                # merge evidence for THIS invariant only
                base_evs[i].extend(ev)
                merged = True
                break

        if not merged:
            base_invs.append(inv)
            base_evs.append(ev)


def states_equivalent(a, b):
    """
    Two states are equivalent if:
    - entity matches
    - state name matches
    """

    return (
        a.get("entity") == b.get("entity") and
        a.get("state")  == b.get("state")
    )


def dedupe(path: str):
    """Load typestate data, dedupe using LLM invariant comparison, save results."""

    with open(path, "r") as f:
        data = json.load(f)

    # flatten all typestate_table entries
    all_entries = []
    for block in data.get("results", []):
        for entry in block.get("typestate_table", []):
            all_entries.append(normalize_entry(entry))

    canonical = []

    for entry in all_entries:
        match = None

        # Does this state match an existing canonical state? (same entity + state)
        for c in canonical:
            if states_equivalent(entry, c):
                match = c
                break

        if match:
            merge_state(match, entry)
        else:
            canonical.append(entry)

    # Save output
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    results_dir = Path("results") / timestamp
    results_dir.mkdir(parents=True, exist_ok=True)

    output_path = results_dir / "deduped_typestates.json"

    output = {
        "agent": "semantic_search_haluc_dedupe",
        "description": "deduplicated typestates",
        "results": canonical,
        "timestamp": datetime.utcnow().isoformat(),
    }

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    return canonical

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
    #asyncio.run(main())
    #asyncio.run(fix_hallucinations("results/2025-11-17_16-26/personal_once_cell.json"))
    asyncio.run(dedupe("results/2025-11-17_16-26/personal_once_cell.json"))
