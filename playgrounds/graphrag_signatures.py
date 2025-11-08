import asyncio
import json
import uuid
import re 

async def call_mcp_tool(query, mode="all", path="/path/to/project"):
    # Start Octocode MCP server
    process = await asyncio.create_subprocess_exec(
        "octocode", "mcp", "--path", path,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Prepare JSON-RPC request
    # request = {
    #     "jsonrpc": "2.0",
    #     "id": str(uuid.uuid4()),
    #     "method": "tools/call",
    #     "params": { "name": "view_signatures",
    #                 "arguments": {
    #                     "files": ["src/imp_pl.rs"]
    #                 }
    #             }
    # }

    request = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "tools/call",
        "params": { "name": "graphrag",
                    "arguments": {
                        "files": ["src/imp_pl.rs"]
                    }
                }
    }

    # Send it 
    msg = json.dumps(request) + "\n" 
    process.stdin.write(msg.encode()) 
    await process.stdin.drain() 

    # Read response line 
    response_line = await process.stdout.readline() 
    response = json.loads(response_line.decode().strip()) 
    
    # Clean up 
    process.kill() 
    return response

async def main():
    result = await call_mcp_tool("enum", path="/Users/sidneyrichardson/senior_thesis-1/code_examples/once_cell")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())



