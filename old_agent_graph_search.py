from loguru import logger
from pydantic_ai import Agent, Tool
from pathlib import Path
import asyncio
from code_graph_rag.codebase_rag.config import settings
from code_graph_rag.codebase_rag.prompts import (
    CYPHER_SYSTEM_PROMPT,
    LOCAL_CYPHER_SYSTEM_PROMPT,
    RAG_ORCHESTRATOR_SYSTEM_PROMPT,
)
from code_graph_rag.codebase_rag.providers.base import get_provider


class LLMGenerationError(Exception):
    """Custom exception for LLM generation failures."""

    pass


def _clean_cypher_response(response_text: str) -> str:
    """Utility to clean up common LLM formatting artifacts from a Cypher query."""
    query = response_text.strip().replace("`", "")
    if query.startswith("cypher"):
        query = query[6:].strip()
    if not query.endswith(";"):
        query += ";"
    return query


class CypherGenerator:
    """Generates Cypher queries from natural language."""

    def __init__(self) -> None:
        try:
            # Get active cypher model configuration
            config = settings.active_cypher_config

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

            # Select system prompt based on provider
            system_prompt = (
                LOCAL_CYPHER_SYSTEM_PROMPT
                if config.provider == "ollama"
                else CYPHER_SYSTEM_PROMPT
            )

            self.agent = Agent(
                model=llm,
                system_prompt=system_prompt,
                output_type=str,
            )
        except Exception as e:
            raise LLMGenerationError(
                f"Failed to initialize CypherGenerator: {e}"
            ) from e

    async def generate(self, natural_language_query: str) -> str:
        logger.info(
            f"  [CypherGenerator] Generating query for: '{natural_language_query}'"
        )
        try:
            result = await self.agent.run(natural_language_query)
            if (
                not isinstance(result.output, str)
                or "MATCH" not in result.output.upper()
            ):
                raise LLMGenerationError(
                    f"LLM did not generate a valid query. Output: {result.output}"
                )

            query = _clean_cypher_response(result.output)
            logger.info(f"  [CypherGenerator] Generated Cypher: {query}")
            return query
        except Exception as e:
            logger.error(f"  [CypherGenerator] Error: {e}")
            raise LLMGenerationError(f"Cypher generation failed: {e}") from e


def create_rag_orchestrator(tools: list[Tool]) -> Agent:
    """Factory function to create the main RAG orchestrator agent."""
    try:
        # Get active orchestrator model configuration
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

        return Agent(
            model=llm,
            system_prompt=RAG_ORCHESTRATOR_SYSTEM_PROMPT,
            tools=tools,
        )
    except Exception as e:
        raise LLMGenerationError(f"Failed to initialize RAG Orchestrator: {e}") from e

from code_graph_rag.codebase_rag.graph_updater import MemgraphIngestor
from code_graph_rag.codebase_rag.services.llm import CypherGenerator
from code_graph_rag.codebase_rag.tools.code_retrieval import create_code_retrieval_tool
from code_graph_rag.codebase_rag.tools.codebase_query import create_query_tool
from code_graph_rag.codebase_rag.tools.file_reader import create_file_reader_tool
from code_graph_rag.codebase_rag.tools.directory_lister import create_directory_lister_tool
from code_graph_rag.codebase_rag.config import settings

from code_graph_rag.codebase_rag.graph_updater import GraphUpdater, MemgraphIngestor
from code_graph_rag.codebase_rag.parser_loader import load_parsers
from code_graph_rag.codebase_rag.services.llm import CypherGenerator 
from code_graph_rag.codebase_rag.tools.code_retrieval import CodeRetriever, create_code_retrieval_tool
from code_graph_rag.codebase_rag.tools.codebase_query import create_query_tool
from code_graph_rag.codebase_rag.tools.directory_lister import DirectoryLister, create_directory_lister_tool
from code_graph_rag.codebase_rag.tools.document_analyzer import DocumentAnalyzer, create_document_analyzer_tool
from code_graph_rag.codebase_rag.tools.file_editor import FileEditor, create_file_editor_tool
from code_graph_rag.codebase_rag.tools.file_reader import FileReader, create_file_reader_tool
from code_graph_rag.codebase_rag.tools.file_writer import FileWriter, create_file_writer_tool
from code_graph_rag.codebase_rag.tools.shell_command import ShellCommander, create_shell_command_tool
from code_graph_rag.codebase_rag.tools.semantic_search import create_semantic_search_tool, create_get_function_source_tool



async def init_graph_agent(repo_path: str):
    repo_to_update = Path(repo_path)
    ingestor = MemgraphIngestor(
        host=settings.MEMGRAPH_HOST,
        port=settings.MEMGRAPH_PORT,
        batch_size=settings.resolve_batch_size(None),
    )
    if True:
        ingestor.__enter__()
        ingestor.clean_database()
        ingestor.ensure_constraints()

        # Load parsers and queries
        parsers, queries = load_parsers()

        updater = GraphUpdater(ingestor, repo_to_update, parsers, queries)
        updater.run()

    cypher_gen = CypherGenerator()
    tools = [
        create_query_tool(ingestor, cypher_gen, console=None)
        #create_code_retrieval_tool(project_root=repo_path, ingestor=ingestor),
        #create_file_reader_tool(project_root=repo_path),
        #create_directory_lister_tool(project_root=repo_path),
    ]
    agent = create_rag_orchestrator(tools)
    return agent, ingestor

from code_graph_rag.codebase_rag.config import settings

async def find_invariants(state):
    repo = "/Users/sidneyrichardson/senior_thesis-1/code_examples/personal_once_cell"
    agent, ingestor = await init_graph_agent(repo)
    result = await agent.run("List state transitions for OnceCell", message_history=state["messages"])
    print("ALL MESSAGES:")
    print(result.all_messages)
    ingestor.__exit__(None, None, None)
    return {"entries": result.output}

if __name__ == "__main__":
    import asyncio
    async def _test():
        state = {"messages": []}
        out = await find_invariants(state)
    asyncio.run(_test())

# async def main():
#     repo_to_update = Path("/Users/sidneyrichardson/senior_thesis-1/code_examples/personal_once_cell")
#     ingestor = MemgraphIngestor(
#         host=settings.MEMGRAPH_HOST,
#         port=settings.MEMGRAPH_PORT,
#         batch_size=settings.resolve_batch_size(None),
#     )
#     if True:
#         ingestor.__enter__()
#         ingestor.clean_database()
#         ingestor.ensure_constraints()

#         # Load parsers and queries
#         parsers, queries = load_parsers()

#         updater = GraphUpdater(ingestor, repo_to_update, parsers, queries)
#         updater.run()
#     try:
#         cy = CypherGenerator()
#         tool = create_query_tool(ingestor, cy, console=None)
#         out = await tool.function("List state transitions for OnceCell")
#         # Exact DB rows:
#         print(out.results)        # list[dict]
#         print(out.query_used)     # Cypher used
#     finally:
#         ingestor.__exit__(None, None, None)

# if __name__ == "__main__":
#     asyncio.run(main())