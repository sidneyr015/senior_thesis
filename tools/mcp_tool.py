import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

JSON = Dict[str, Any]

class MCPError(RuntimeError):
    pass

class MCPClient:
    def __init__(self, path: str, cmd: str = "octocode"): 
        self.path = path
        self.cmd = cmd
        self.proc: Optional[asyncio.subprocess.Process] = None 
        self._pending: Dict[str, asyncio.Future] = {} 
        self._reader_task: Optional[asyncio.Task] = None 

    async def start(self) -> None: 
        if self.proc: 
            return 
        self.proc = await asyncio.create_subprocess_exec(
            self.cmd, "mcp", "--path", self.path, 
            stdin=asyncio.subprocess.PIPE, 
            stdout=asyncio.subprocess.PIPE, 
            stderr=asyncio.subprocess.PIPE, 
        )
        self._reader_task = asyncio.create_task(self._reader())

    async def stop(self) -> None: 
        if self.proc: 
            self.proc.terminate() 
            try: 
                await asyncio.wait_for(self.proc.wait(), timeout=2)
            except asyncio.TimeoutError: 
                self.proc.kill()
            self.proc = None
        if self._reader_task: 
            self._reader_task.cancel() 

    async def _reader(self) -> None: 
        assert self.proc and self.proc.stdout
        while True: 
            line = await self.proc.stdout.readline() 
            if not line: 
                for fut in self._pending.values(): 
                    if not fut.done(): 
                        fut.set_exception(MCPError("MCP server closed"))
                self._pending.clear() 
                return 
            try: 
                msg = json.loads(line.decode().strip())
            except Exception: 
                continue 
        
            if "id" in msg and str(msg["id"]) in self._pending: 
                fut = self._pending.pop(str(msg["id"]))
                if not fut.done(): 
                    fut.set_result(msg)
    
    async def request(self, method: str, params: JSON) -> JSON: 
        if not self.proc or not self.proc.stdin: 
            raise MCPError("MCP not started")
        req_id = str(uuid.uuid4())
        req = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
        fut: asyncio.Future = asyncio.get_event_loop().create_future() 
        self._pending[req_id] = fut
        self.proc.stdin.write((json.dumps(req) + "\n").encode())
        await self.proc.stdin.drain()
        resp = await asyncio.wait_for(fut, timeout=60)
        if "error" in resp: 
            raise MCPError(json.dumps(resp["error"]))
        return resp["result"] if "result" in resp else resp

    async def call_tool(self, name: str, arguments: JSON) -> JSON: 
        return await self.request("tools/call", {"name": name, "arguments": arguments})

@asynccontextmanager
async def mcp_client(path: str): 
    client = MCPClient(path)
    await client.start() 
    try: 
        yield client
    finally: 
        await client.stop()

async def main():
    async with mcp_client("/Users/sidneyrichardson/senior_thesis-1") as client:
        resp = await client.call_tool("semantic_search", {"path": "", "query": "mcp_client", "threshold": 0.1})
        print(resp)

if __name__ == "__main__":
    asyncio.run(main())