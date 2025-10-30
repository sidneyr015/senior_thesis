from typing import Optional, Dict, Any, ClassVar
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool 
from tools.mcp_tool import MCPClient, mcp_client 

class SemanticSearchInput(BaseModel):
    query: str = Field(..., description="What to search for")
    mode: str = Field("all", description="Search mode (eg 'all', 'code', 'doc')")
    path: str = Field(..., description="Project root folder for octocode MCP")

class SemanticSearchTool(BaseTool): 
    name: ClassVar[str]="semantic_search"
    description: ClassVar[str]="Run Octocode MCP semantic search over a repository"
    args_schema: ClassVar[str]= SemanticSearchInput

    def __init__(self): 
        super().__init__()
    
    async def _arun(self, query: str, mode: str, path: str) -> Dict[str, Any]: 
        async with mcp_client(path) as client: 
            result = await client.call_tool( 
                "semantic_search", 
                {"query": query, "mode": mode, "threshold": 0.1}
            )
        return result
    
    def _run(self, *args, **kwargs): 
        raise NotImplementedError("Use async in Langgraph.")

semantic_search_tool = SemanticSearchTool()
