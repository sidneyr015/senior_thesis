from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool 
from mcp_tool import MCPClient, mcp_client 

class SemanticSearchInput(BaseModel):
    query: str = Field(..., description="What to search for")