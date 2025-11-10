import json
import asyncio
from datetime import datetime

from code_graph_rag.codebase_rag.config import settings
from code_graph_rag.codebase_rag.graph_updater import MemgraphIngestor
from code_graph_rag.codebase_rag.services.llm import create_rag_orchestrator, CypherGenerator
from code_graph_rag.codebase_rag.tools.codebase_query import create_query_tool

async def agent_query_and_save(prompts: list[str], out_path: str):
    records = []
    with MemgraphIngestor(settings.MEMGRAPH_HOST, settings.MEMGRAPH_PORT, 1000) as ing:
        cy = CypherGenerator()

        last = {"nl": None, "cypher": None, "rows": None}
        tool = create_query_tool(ing, cy, console=None)

        orig = tool.function
        async def wrapped(nl_query: str):
            res = await orig(nl_query)  # GraphData(query_used, results, summary)
            last.update({"nl": nl_query, "cypher": res.query_used, "rows": res.results})
            return res
        tool.function = wrapped

        agent = create_rag_orchestrator([tool])

        for p in prompts:
            await agent.run("List state transitions for OnceCell")
            if last["nl"] is None:  # fallback if the agent didn’t call the tool
                data = await tool.function(p)
                last.update({"nl": p, "cypher": data.query_used, "rows": data.results})
            records.append({
                "natural_language": last["nl"],
                "cypher": last["cypher"],
                "row_count": len(last["rows"] or []),
                "rows": last["rows"] or [],
                "timestamp": datetime.utcnow().isoformat(),
            })
            last.update({"nl": None, "cypher": None, "rows": None})

    with open(out_path, "w") as f:
        json.dump(records, f, indent=2)

if __name__ == "__main__":
    prompts = [
        "List state transitions for OnceCell",
    ]
    asyncio.run(agent_query_and_save(prompts, "graph_agent_results.json"))