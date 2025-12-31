"""
GLM MCP Client Implementation
==============================

Enables GLM to use MCP (Model Context Protocol) servers for external integrations
like Context7, Linear, Electron, and Graphiti.

MCP servers are spawned as subprocesses and communicate via stdio or HTTP.
This module handles:
- Spawning MCP server processes
- Discovering available tools from servers
- Routing tool calls to the correct server
- Parsing tool responses
"""

import asyncio
import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class MCPServer:
    """Configuration for an MCP server."""
    name: str
    server_type: str = "stdio"  # "stdio" or "http"
    command: str | None = None
    args: list[str] = field(default_factory=list)
    url: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    env: dict[str, str] = field(default_factory=dict)
    
    # Runtime state
    process: subprocess.Popen | None = None
    tools: list[dict] = field(default_factory=list)


class MCPManager:
    """
    Manages MCP server lifecycle and tool routing for GLM.
    
    Example:
        >>> manager = MCPManager()
        >>> await manager.add_server("context7", {
        ...     "command": "npx",
        ...     "args": ["-y", "@upstash/context7-mcp"]
        ... })
        >>> await manager.start_all()
        >>> tools = manager.get_all_tools()
        >>> result = await manager.execute_tool("mcp__context7__get-library-docs", {...})
        >>> await manager.stop_all()
    """
    
    def __init__(self):
        self.servers: dict[str, MCPServer] = {}
        self._http_client: httpx.AsyncClient | None = None
    
    async def __aenter__(self):
        self._http_client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop_all()
        if self._http_client:
            await self._http_client.aclose()
    
    def add_server(self, name: str, config: dict) -> None:
        """
        Add an MCP server configuration.
        
        Args:
            name: Server identifier (e.g., "context7", "linear")
            config: Server configuration dict with keys:
                - type: "http" or "stdio" (default: "stdio")
                - command: Command to run (for stdio)
                - args: Command arguments (for stdio)
                - url: URL for HTTP servers
                - headers: HTTP headers (for http)
        """
        server = MCPServer(
            name=name,
            server_type=config.get("type", "stdio"),
            command=config.get("command"),
            args=config.get("args", []),
            url=config.get("url"),
            headers=config.get("headers", {}),
            env=config.get("env", {}),
        )
        self.servers[name] = server
        logger.info(f"Added MCP server: {name} ({server.server_type})")
    
    async def start_all(self) -> None:
        """Start all configured MCP servers and discover their tools."""
        for name, server in self.servers.items():
            try:
                if server.server_type == "stdio":
                    await self._start_stdio_server(server)
                elif server.server_type == "http":
                    await self._discover_http_tools(server)
                logger.info(f"Started MCP server: {name} with {len(server.tools)} tools")
            except Exception as e:
                logger.error(f"Failed to start MCP server {name}: {e}")
    
    async def stop_all(self) -> None:
        """Stop all running MCP server processes."""
        for name, server in self.servers.items():
            if server.process:
                try:
                    server.process.terminate()
                    server.process.wait(timeout=5)
                except Exception as e:
                    logger.warning(f"Error stopping server {name}: {e}")
                finally:
                    server.process = None
    
    async def _start_stdio_server(self, server: MCPServer) -> None:
        """Start a stdio-based MCP server."""
        if not server.command:
            raise ValueError(f"No command specified for server {server.name}")
        
        # Build environment
        env = os.environ.copy()
        env.update(server.env)
        
        # Start process
        try:
            server.process = subprocess.Popen(
                [server.command] + server.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
            )
            
            # Give server time to initialize
            await asyncio.sleep(1.0)
            
            # Request tool list via JSON-RPC
            await self._discover_stdio_tools(server)
            
        except FileNotFoundError:
            logger.error(f"Command not found: {server.command}")
            logger.warning(f"MCP server {server.name} will be skipped")
            # Don't raise - make MCP servers optional
        except Exception as e:
            logger.error(f"Failed to start MCP server {server.name}: {e}")
            logger.warning(f"MCP server {server.name} will be skipped")
            # Don't raise - make MCP servers optional
    
    async def _discover_stdio_tools(self, server: MCPServer) -> None:
        """Discover tools from a stdio MCP server."""
        if not server.process or not server.process.stdin or not server.process.stdout:
            return
        
        # Send tools/list request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        try:
            server.process.stdin.write(json.dumps(request) + "\n")
            server.process.stdin.flush()
            
            # Read response (with timeout)
            response_line = server.process.stdout.readline()
            if response_line:
                response = json.loads(response_line)
                if "result" in response and "tools" in response["result"]:
                    server.tools = response["result"]["tools"]
        except Exception as e:
            logger.warning(f"Could not discover tools for {server.name}: {e}")
            # Use empty tools list - server may not support discovery
            server.tools = []
    
    async def _discover_http_tools(self, server: MCPServer) -> None:
        """Discover tools from an HTTP MCP server."""
        if not server.url or not self._http_client:
            return
        
        try:
            response = await self._http_client.post(
                server.url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                    "params": {}
                },
                headers=server.headers,
            )
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data and "tools" in data["result"]:
                    server.tools = data["result"]["tools"]
        except Exception as e:
            logger.warning(f"Could not discover tools for {server.name}: {e}")
            server.tools = []
    
    def get_all_tools(self) -> list[dict]:
        """
        Get all tools from all servers in GLM function format.
        
        Returns:
            List of tool definitions for GLM function calling
        """
        tools = []
        for server_name, server in self.servers.items():
            for tool in server.tools:
                # Convert MCP tool to GLM function format
                tool_name = f"mcp__{server_name}__{tool.get('name', 'unknown')}"
                glm_tool = {
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": tool.get("description", ""),
                        "parameters": tool.get("inputSchema", {"type": "object", "properties": {}})
                    }
                }
                tools.append(glm_tool)
        return tools
    
    def get_tool_names(self) -> list[str]:
        """Get list of all available MCP tool names."""
        names = []
        for server_name, server in self.servers.items():
            for tool in server.tools:
                names.append(f"mcp__{server_name}__{tool.get('name', 'unknown')}")
        return names
    
    async def execute_tool(self, tool_name: str, arguments: dict) -> str:
        """
        Execute an MCP tool and return the result.
        
        Args:
            tool_name: Full tool name (e.g., "mcp__context7__get-library-docs")
            arguments: Tool arguments
        
        Returns:
            Tool execution result as string
        """
        # Parse tool name to find server
        parts = tool_name.split("__")
        if len(parts) < 3 or parts[0] != "mcp":
            raise ValueError(f"Invalid MCP tool name: {tool_name}")
        
        server_name = parts[1]
        actual_tool_name = "__".join(parts[2:])  # Handle tools with __ in name
        
        server = self.servers.get(server_name)
        if not server:
            raise ValueError(f"MCP server not found: {server_name}")
        
        if server.server_type == "stdio":
            return await self._execute_stdio_tool(server, actual_tool_name, arguments)
        elif server.server_type == "http":
            return await self._execute_http_tool(server, actual_tool_name, arguments)
        else:
            raise ValueError(f"Unknown server type: {server.server_type}")
    
    async def _execute_stdio_tool(self, server: MCPServer, tool_name: str, arguments: dict) -> str:
        """Execute a tool on a stdio MCP server."""
        if not server.process or not server.process.stdin or not server.process.stdout:
            return json.dumps({"error": f"Server {server.name} not running"})
        
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        try:
            server.process.stdin.write(json.dumps(request) + "\n")
            server.process.stdin.flush()
            
            response_line = server.process.stdout.readline()
            if response_line:
                response = json.loads(response_line)
                if "result" in response:
                    content = response["result"].get("content", [])
                    if content and isinstance(content, list):
                        return content[0].get("text", json.dumps(content))
                    return json.dumps(response["result"])
                elif "error" in response:
                    return json.dumps({"error": response["error"]})
            return json.dumps({"error": "No response from server"})
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    async def _execute_http_tool(self, server: MCPServer, tool_name: str, arguments: dict) -> str:
        """Execute a tool on an HTTP MCP server."""
        if not server.url or not self._http_client:
            return json.dumps({"error": f"Server {server.name} not configured"})
        
        try:
            response = await self._http_client.post(
                server.url,
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                },
                headers=server.headers,
            )
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    content = data["result"].get("content", [])
                    if content and isinstance(content, list):
                        return content[0].get("text", json.dumps(content))
                    return json.dumps(data["result"])
                elif "error" in data:
                    return json.dumps({"error": data["error"]})
            return json.dumps({"error": f"HTTP {response.status_code}"})
        except Exception as e:
            return json.dumps({"error": str(e)})


def create_mcp_manager(mcp_servers: dict) -> MCPManager:
    """
    Create an MCP manager with the given server configurations.
    
    Args:
        mcp_servers: Dict of server_name -> config
                    (same format as Claude SDK mcp_servers)
    
    Returns:
        Configured MCPManager instance
    """
    manager = MCPManager()
    for name, config in mcp_servers.items():
        manager.add_server(name, config)
    return manager
