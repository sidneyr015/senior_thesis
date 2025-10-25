import asyncio
import json
import uuid

async def call_mcp_tool(query, mode="all", path="/path/to/project"):
    # Start Octocode MCP server
    process = await asyncio.create_subprocess_exec(
        "octocode", "mcp", "--path", path,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Prepare JSON-RPC request
    request = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "tools/call",
        "params": { "name": "semantic_search",
                    "arguments": {
                        "query": "query",
                        "mode": mode
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
    result = await call_mcp_tool("chat", path="/Users/sidneyrichardson/senior_thesis-1")
    print(json.dumps(result, indent=2))

asyncio.run(main())



