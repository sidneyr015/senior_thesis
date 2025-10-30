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
    request = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "tools/call",
        "params": { "name": "semantic_search",
                    "arguments": {
                        "query": "state_transistions",
                        "mode": "code",
                        "threshold": 0.1,
                        "detail_level": "partial",
                        "max_results": 20
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

def parse(text): 
    # Split into individual matches
    print(text)
    chunks = text.split("\n\n\n")  # Triple newline between entries
    parsed = []
    for chunk in chunks:
        print(chunk + '\n')
        lines = [l.strip() for l in chunk.splitlines() if l.strip()]
        if lines and lines[0].startswith(tuple(str(i) + "." for i in range(1, 100))):
            parsed.append("\n".join(lines))

    entries = []
    for chunk in parsed:
        match = re.search(r"(\d+)\.\s+(.+)\n\s+\|\s+Similarity\s+([0-9.]+)", chunk)
        if match:
            index, file, similarity = match.groups()
            code = chunk.split("\n", 3)[-1]
            entries.append({
                "index": int(index),
                "file": file.strip(),
                "similarity": float(similarity),
                "code": code.strip()
            })
    return entries

async def main():
    result = await call_mcp_tool("enum", path="/Users/sidneyrichardson/senior_thesis-1/code_examples/once_cell")
    entries = parse(result["result"]["content"][0]["text"])

    for entry in entries: 
        print(entry)


if __name__ == "__main__":
    asyncio.run(main())



