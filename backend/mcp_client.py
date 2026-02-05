"""MCP Client for backend integration with browser server."""

import asyncio
import json
from typing import Dict, Any, List
from pathlib import Path
import subprocess
import sys

class MCPClient:
    """Client to connect to MCP servers."""

    def __init__(self, server_script: str):
        self.server_script = server_script
        self.process: subprocess.Popen | None = None
        self.stdin = None
        self.stdout = None

    async def start_server(self):
        """Start MCP server process."""
        self.process = await asyncio.create_subprocess_exec(
            sys.executable, self.server_script,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        self.stdin = self.process.stdin
        self.stdout = self.process.stdout

    async def stop_server(self):
        """Stop MCP server."""
        if self.process:
            self.process.terminate()
            await self.process.wait()

    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send JSON-RPC request to server."""
        if not self.stdin or not self.stdout:
            raise RuntimeError("Server not started")

        # Write request
        request_json = json.dumps(request) + "\n"
        self.stdin.write(request_json.encode())
        await self.stdin.drain()

        # Read response
        response_line = await self.stdout.readline()
        response = json.loads(response_line.decode().strip())

        return response

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from server."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }

        response = await self.send_request(request)
        return response.get("result", {}).get("tools", [])

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool on the server."""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        response = await self.send_request(request)
        content = response.get("result", {}).get("content", [])

        # Extract text from content
        text_parts = [item.get("text", "") for item in content if item.get("type") == "text"]
        return " ".join(text_parts)

# Global client instance
_mcp_client: MCPClient | None = None

async def get_mcp_client() -> MCPClient:
    """Get or create MCP client."""
    global _mcp_client

    if _mcp_client is None:
        # Path to browser server
        server_path = Path(__file__).parent / "browser_server.py"
        _mcp_client = MCPClient(str(server_path))
        await _mcp_client.start_server()

    return _mcp_client

async def perform_roaming_action(action: str, **kwargs) -> str:
    """Perform a roaming action via MCP."""
    client = await get_mcp_client()

    # Map action to tool name
    tool_mapping = {
        "create_twitter_account": "create_twitter_account",
        "scroll_twitter": "scroll_twitter_feed",
        "click_tweet": "click_tweet",
        "type_tweet": "type_tweet_text"
    }

    if action not in tool_mapping:
        return f"Unknown roaming action: {action}"

    tool_name = tool_mapping[action]

    try:
        result = await client.call_tool(tool_name, kwargs)
        return result
    except Exception as e:
        # Log detailed error server-side, but return a generic message to the caller
        print(f"Roaming action '{action}' failed with error: {e}", file=sys.stderr)
        return "Roaming action failed due to an internal error."