import argparse
from typing import Annotated
from typing_extensions import TypedDict
import asyncio
import subprocess
import sys

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

from tools.semantic_search_tool import semantic_search_tool
from tools.code_snippet_tool import get_code_snippet

improvements_note = """"
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

async def find_invariants(state, repo_path): 
    print("finding invariants")
    q = "enum"
    search = await semantic_search_tool._arun(query=q, mode="all", path=repo_path)
    print("search!")
    entries = parse(search["content"][0]["text"])
    for entry in entries: 
        print(entry)
    return {"entries": entries}

async def fetch_snippets(state, repo_path, output_path): 
    print("Running fetch_snippets and extracting type states")
    entries = state["entries"]
    prompt = prompt_typestate_extraction
    results = []
    total_tokens = 0

    for entry in entries: 
        expanded_start_line, code_snippet = get_code_snippet(os.path.join(repo_path, entry["file"]), entry["start_line"], entry["end_line"])
        response = llm.invoke([
            HumanMessage(content=prompt + "\n\n Please find type_state invariants for this code snippet" + code_snippet)
        ])

        if hasattr(response, 'response_metadata'):
            usage = response.response_metadata.get('token_usage', {})
            total_tokens += usage.get('total_tokens', 0)
                  
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
    
    # Write output ONCE
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
    
    return {"entries": results, "output_path": output_path}

def fix_hallucinations(input_path: str, repo_path: str, output_path: str) -> None:
    print("Fixing hallucinations") 
    with open(input_path, "r") as f:
        ts = json.load(f)

    prompt = prompt_clean_up
    results = []
    total_tokens = 0

    for entry in ts.get("results", []):
        expanded_start_line, code_snippet = get_code_snippet(os.path.join(repo_path, entry["file"]), int(entry["line_range"]["start"]), int(entry["line_range"]["end"]))

        qualified_name = ""
        try: 
            qualified_name = (entry.get("typestate_table", [])[0].get("qualified_name", "N/A"))
        except:
            continue
        
        response = llm.invoke([
            HumanMessage(content=prompt + "Code snippet: \n" + code_snippet + "Entry: \n" + json.dumps(entry) + "Qualified Name: \n" + qualified_name + "\n")
        ])

        if hasattr(response, 'response_metadata'):
            usage = response.response_metadata.get('token_usage', {})
            total_tokens += usage.get('total_tokens', 0)
                  
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
    
    # Write to same output file
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

def generate_graph(repo_path, graph_output_path, env_path="code_graph_rag/.env"):
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY", "")
    env_content = f"""ORCHESTRATOR_PROVIDER=openai
ORCHESTRATOR_MODEL=gpt-4o
ORCHESTRATOR_API_KEY={api_key}

CYPHER_PROVIDER=openai
CYPHER_MODEL=gpt-4o-mini
CYPHER_API_KEY={api_key}
"""
    os.makedirs(os.path.dirname(env_path), exist_ok=True)
    with open(env_path, "w") as f:
        f.write(env_content)

    # Set PYTHONPATH to include code_graph_rag so codebase_rag is importable
    env = os.environ.copy()
    code_graph_rag_path = os.path.abspath("code_graph_rag")
    env["PYTHONPATH"] = (
        code_graph_rag_path if "PYTHONPATH" not in env
        else f"{code_graph_rag_path}:{env['PYTHONPATH']}"
    )

    # Use absolute path for graph output
    abs_graph_path = os.path.abspath(graph_output_path)  # ADD this line

    # Run the graph generation command
    cmd = [
        sys.executable, "-m", "codebase_rag.main", "start",
        "--repo-path", repo_path,
        "--update-graph",
        "--clean",
        "-o", abs_graph_path  # CHANGE: use absolute path
    ]
    subprocess.run(cmd, cwd=code_graph_rag_path, env=env, check=True)

def find_qualified_names(output_name: str, graph_path: str) -> None:  # ADD graph_path parameter
    with open(output_name, "r") as f:
        ts = json.load(f)

    with open(graph_path) as f:  # CHANGE from hardcoded "my_graph.json"
        graph_data = json.load(f)

    line_index = {}

    for node in graph_data["nodes"]:
        props = node["properties"]
        if "start_line" in props and "end_line" in props:
            for ln in range(props["start_line"] - 1, props["end_line"] + 1):
                line_index[ln] = node

    for result in ts.get("results", []):
        line_start = result["line_range"]["start"]
        node = line_index.get(line_start)
        if node:
            qname = node["properties"].get("qualified_name")
            for entry in result.get("typestate_table", []):
                entry["qualified_name"] = qname

    with open(output_name, "w") as f:
        json.dump(ts, f, indent=2)

    print("Entity names updated using graph qualified names.")

    return output_name

def parse(text): 
    chunks = re.split(r"\n{2,}", text)
    entries = []

    for chunk in chunks:
        lines = [l.strip() for l in chunk.splitlines() if l.strip()]
        if not lines:
            continue

        file_match = re.search(r"(\d+)\.\s+([^\s]+\.rs)", chunk)
        sim_match = re.search(r"Similarity\s+([0-9.]+)", chunk)
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

async def main(repo_path, graph_path="./my_graph.json"):  # ADD graph_path parameter
    # Create output file once at the start
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    results_dir = Path("results") / timestamp
    results_dir.mkdir(parents=True, exist_ok=True)
    output_path = results_dir / "personal_once_cell.json"
    
    state = {"messages": [HumanMessage(content=repo_path)]}
    entries_state = await find_invariants(state, repo_path)
    await fetch_snippets(entries_state, repo_path, output_path)
    find_qualified_names(output_path, graph_path)  
    fix_hallucinations(output_path, repo_path, output_path)

    print(f"Results written to: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Semantic Search Haluc Agent")
    parser.add_argument("repo_path", help="Path to the repository directory")
    parser.add_argument("--fix", help="Path to the output JSON to fix hallucinations", default=None)
    args = parser.parse_args()
    
    graph_output_path = "./my_graph.json"  # ADD this line
    generate_graph(args.repo_path, graph_output_path)
    asyncio.run(main(args.repo_path, graph_output_path))  # CHANGE: pass graph_output_path