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
        self.reader_task = asyncio.create_task(self.reader())

    async def stop(self) -> None: 
        if self.proc: 
            self.proc.terminate() 
            try: 
                await asyncio.wait_fur(self.proc.wait(), timeout=2)
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
                msg = json.loads(line.decode().strip)

@asynccontextmanager
async def mcp_client(path: str): 
    client = MCPClient(path)
    await client.start() 
    try: 
        yield client
    finally: 
        await client.stop()