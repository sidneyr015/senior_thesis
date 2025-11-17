import json
import asyncio
from datetime import datetime
import re
from pathlib import Path 

from code_graph_rag.codebase_rag.config import settings
from code_graph_rag.codebase_rag.graph_updater import MemgraphIngestor
from code_graph_rag.codebase_rag.services.llm import create_rag_orchestrator, CypherGenerator
from code_graph_rag.codebase_rag.tools.codebase_query import create_query_tool
from code_graph_rag.codebase_rag.providers.base import get_provider


async def get_relevant_nodes():
    results_array = []  # Create array to store results
    
    with MemgraphIngestor(settings.MEMGRAPH_HOST, settings.MEMGRAPH_PORT, 1000) as ing:
        cy = CypherGenerator()
        rag_orchestrator = create_rag_orchestrator([create_query_tool(ing, cy, console=None)])
        result = await rag_orchestrator.run("List state transitions for OnceCell")

        # Access all messages (includes tool calls and responses)
        for message in result.all_messages():
            if hasattr(message, 'parts'):
                for part in message.parts:
                    # Check if it's a ToolReturnPart
                    if hasattr(part, 'tool_name') and hasattr(part, 'content'):
                        graph_data = part.content
                        
                        # Add to results array
                        results_array.append({
                            "tool_name": part.tool_name,
                            "query_used": graph_data.query_used,
                            "results": graph_data.results,
                            "summary": graph_data.summary,
                            "row_count": len(graph_data.results),
                            "timestamp": datetime.utcnow().isoformat(),
                        })
    
    # Print summary
    print(f"\n\nCollected {len(results_array)} tool results")
    return results_array

async def get_code_snippets(qualified_names: list[str]):
    snippets_array = []  # Create array to store code snippets
    
    from code_graph_rag.codebase_rag.tools.code_retrieval import CodeRetriever
    from pathlib import Path

    project_root = Path("/Users/sidneyrichardson/senior_thesis-1/code_examples/personal_once_cell")
    
    with MemgraphIngestor(settings.MEMGRAPH_HOST, settings.MEMGRAPH_PORT, 1000) as ing:
        code_retriever = CodeRetriever(project_root, ing)
        
        for name in qualified_names:
            snippet = await code_retriever.find_code_snippet(name)
            print(snippet)
            snippets_array.append({
                "qualified_name": snippet.qualified_name,
                "file_path": snippet.file_path,
                "line_start": snippet.line_start,
                "line_end": snippet.line_end,
                "source_code": snippet.source_code,
                "found": snippet.found,
                "error_message": snippet.error_message,
            })
        
        print(f"\n\nCollected {len(snippets_array)} code snippets")
        return snippets_array

async def analyze_snippets(snippets: list[dict]):
    from pydantic_ai import Agent
    from prompts.basic_prompt import prompt
    
    config = settings.active_orchestrator_config

    # Create provider instance
    provider = get_provider(
        config.provider,
        api_key=config.api_key,
        endpoint=config.endpoint,
        project_id=config.project_id,
        region=config.region,
        provider_type=config.provider_type,
        thinking_budget=config.thinking_budget,
    )

    # Create model using provider
    llm = provider.create_model(config.model_id)

    agent = Agent(
        model=llm,
        system_prompt=prompt,
    )
    
    results = []
    for snippet in snippets:
        if snippet["found"]:
            result = await agent.run(f"File: {snippet['file_path']}\n\n{snippet['source_code']}")
            raw = result.output 
            match = re.search(r"```json\s*(\{.*\})\s*```", raw, re.DOTALL)
            if match:
                json_text = match.group(1)
            else:
                json_text = raw.strip()

            try: 
                if json_text: 
                    data = json.loads(json_text)
                    print("\nFinal Analysis Result:")
                    print(result)
                    print("\nRaw Agent Output:")
                    print(raw)
                    print("\nExtracted JSON Data:")
                    print(data)
                    results.append({"qualified_name": snippet, "analysis": data["typestate_table"]})
            except:
                continue
    
    print(results)
    return results

async def main():
    # Get relevant nodes from graph
    graph_results = await get_relevant_nodes()
    
    # Extract qualified names from all results
    qualified_names = []
    for result in graph_results:
        for row in result["results"]:
            if "qualified_name" in row:
                qualified_names.append(row["qualified_name"])
    
    print(f"\nFound {len(qualified_names)} qualified names: {qualified_names}")
    
    if qualified_names:
        snippets = await get_code_snippets(qualified_names)
        
        print("\n" + "="*50)
        print("Starting Typestate Analysis")
        print("="*50)
        analyses = await analyze_snippets(snippets)
        
        # Create timestamped results directory
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        results_dir = Path("results") / timestamp
        results_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = results_dir / "graph_agent_results.json"
        
        # Save with agent identifier
        output = {
            "agent": "graph_search_agent",
            "graph_results": graph_results,
            "code_snippets": snippets,
            "typestate_analyses": analyses,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)
        
        print(f"\n{'='*50}")
        print(f"Saved results to {output_path}")
        print(f"Total analyses: {len(analyses)}")

if __name__ == "__main__":
    asyncio.run(main())
