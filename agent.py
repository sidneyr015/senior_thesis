from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.graph.message import add_messages 
import os
from langchain.chat_models import init_chat_model
from datetime import datetime
from pathlib import Path 

class State(TypedDict): 
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

api_key = os.getenv("API_KEY")
os.environ["OPENAI_API_KEY"] = api_key

llm = init_chat_model("gpt-4o")

generate_table_system_prompt = """
You are an expert on Rust typestate design patterns. 
Analyze the following Rust source file and extract *typestate-related invariants*.

For each type, produce one row per distinct typestate.
Each row should represent a single state in the typestate machine.

Your output must be a markdown table with the following columns:

Entity — the type name, including any generic parameters.
State Dimensions — the type parameters or const generics that encode state.
Valid States — the concrete state represented by the current type.
Invariants — list 2–4 concise bullet points describing conditions guaranteed in this state.
Transitions — methods that change state, written as `fn_name(Self) -> NextState`.

**Formatting requirements:**
- Use one table row per unique typestate variant.
- Be precise about what operations are valid and what resources are available.
Output the results in a markdown table.
"""

def find_invariants(state: MessagesState): 
    system_message = {
        "role": "system", 
        "content": generate_table_system_prompt,
    }
    response = llm.invoke([system_message] + state["messages"])

    return {"messages": response}

graph_builder.add_node("find_invariants", find_invariants)

graph_builder.add_edge(START, "find_invariants")
graph_builder.add_edge("find_invariants", END)

graph = graph_builder.compile()

question = "Find the typestate invariants within this code."

final_output = None

timestamp = datetime.now().strftime("%Y-%m-%d/%H/%M")
results_dir = f"results/{timestamp}"
os.makedirs(results_dir, exist_ok=True)

rust_files = ["code_examples/http_response/http_response.rs"]

for file_path in rust_files: 
    with open(file_path, "r") as f: 
        rust_code = f.read()

        state = {
            "messages": [
                {"role": "user", "content": f"{question}\n\n{rust_code}"} 
            ]
        }

        for step in graph.stream(
            state,
            stream_mode="values"
        ):
            final_output = step["messages"][-1]
            step["messages"][-1].pretty_print()

        if final_output: 
            print(final_output.content)
            output_name = Path(file_path).stem + ".md"
            output_path = os.path.join(results_dir, output_name)
            with open(output_path, "w") as f: 
                f.write(final_output.content)
            