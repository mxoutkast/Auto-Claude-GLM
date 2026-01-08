"""
GLM Agent Client
================

Primary AI client for Auto-Claude using GLM 4.7 API.

This client provides a full-featured agentic loop with:
- OpenAI-compatible API via GLM
- Tool calling with core tools + MCP servers
- Claude SDK-compatible message format
- Async context manager support
- Security hook integration

Key features:
- Supports all core tools (Read, Write, Edit, Glob, Grep, Bash, WebFetch, WebSearch)
- Supports MCP servers (Context7, Linear, Electron, Graphiti, auto-claude)
- Drop-in replacement for ClaudeSDKClient interface
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, AsyncIterator

from .glm_converters import (
    AssistantMessage,
    UserMessage,
    convert_glm_to_assistant_message,
    convert_tool_results_to_user_message,
    format_tool_results_for_glm,
)
from .glm_options import GLMAgentOptions

logger = logging.getLogger(__name__)

# Check if openai is available
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai package not available - install with: pip install openai")


class GLMAgentClient:
    """
    GLM-based agent client - the primary AI client for Auto-Claude.
    
    Uses OpenAI-compatible API to interact with GLM 4.7 models.
    Implements agentic loop: query -> tool use -> execute -> repeat.
    Supports both core tools and MCP servers.
    
    Example:
        >>> options = GLMAgentOptions(
        ...     model="glm-4.7",
        ...     system_prompt="You are a helpful assistant",
        ...     allowed_tools=["Read", "Write", "Bash"],
        ...     mcp_servers={"context7": {"command": "npx", "args": ["-y", "@upstash/context7-mcp"]}}
        ... )
        >>> client = GLMAgentClient(options=options)
        >>> async with client:
        ...     await client.query("Read the README.md file")
        ...     async for msg in client.receive_response():
        ...         print(msg)
    """
    
    def __init__(self, options: GLMAgentOptions):
        """
        Initialize GLM Agent Client.
        
        Args:
            options: Configuration options
            
        Raises:
            RuntimeError: If openai package is not installed
            ValueError: If ZHIPUAI_API_KEY is not set
        """
        if not OPENAI_AVAILABLE:
            raise RuntimeError(
                "openai package required for GLM client. "
                "Install with: pip install openai"
            )
        
        self.options = options
        self.messages: list[dict] = []
        self.current_query: str | None = None
        self.turn_count = 0
        self._mcp_manager = None
        
        # Initialize OpenAI client with GLM endpoint
        api_key = os.environ.get("ZHIPUAI_API_KEY")
        if not api_key:
            raise ValueError(
                "ZHIPUAI_API_KEY environment variable required. "
                "Get your key from: https://open.bigmodel.cn/"
            )
        
        base_url = os.environ.get(
            "GLM_BASE_URL",
            "https://api.z.ai/api/coding/paas/v4"
        )
        
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # Add system message if provided
        if options.system_prompt:
            self.messages.append({
                "role": "system",
                "content": options.system_prompt
            })
        
        # Build tool definitions from registry (core tools)
        from .glm_tools import get_tool_definitions
        self.tools = get_tool_definitions(options.allowed_tools)
        
        # Initialize MCP manager if servers configured
        if options.mcp_servers:
            from .glm_mcp import create_mcp_manager
            self._mcp_manager = create_mcp_manager(options.mcp_servers)
        
        # Load security settings if provided
        self.security_settings = self._load_security_settings()
        
        # Load security profile for bash validation
        self.security_profile = self._load_security_profile()
        
        logger.info(
            f"GLM Agent Client initialized: model={options.model}, "
            f"tools={len(self.tools)}, mcp_servers={len(options.mcp_servers)}, cwd={options.cwd}"
        )
    
    async def __aenter__(self):
        """Async context manager entry - starts MCP servers."""
        if self._mcp_manager:
            await self._mcp_manager.__aenter__()
            await self._mcp_manager.start_all()
            
            # Add MCP tools to our tool list
            mcp_tools = self._mcp_manager.get_all_tools()
            self.tools.extend(mcp_tools)
            logger.info(f"Added {len(mcp_tools)} MCP tools")
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - stops MCP servers."""
        if self._mcp_manager:
            await self._mcp_manager.__aexit__(exc_type, exc_val, exc_tb)
    
    async def query(self, message: str) -> None:
        """
        Send a query to the agent.
        
        Args:
            message: User message/prompt
        """
        self.current_query = message
        self.messages.append({
            "role": "user",
            "content": message
        })
        logger.debug(f"Query added: {len(message)} chars")
    
    async def receive_response(self) -> AsyncIterator[AssistantMessage | UserMessage]:
        """
        Receive agent response with agentic loop.
        
        Implements the tool-calling cycle:
        1. Call GLM API
        2. Yield AssistantMessage with text/tool_calls
        3. If tool_calls present:
           a. Execute tools
           b. Yield UserMessage with results
           c. Loop back to step 1
        4. Stop when no more tool calls
        
        Yields:
            AssistantMessage or UserMessage objects
        """
        if not self.current_query:
            logger.warning("receive_response called without query")
            return
        
        # Agentic loop
        while self.turn_count < self.options.max_turns:
            self.turn_count += 1
            
            # Call GLM API
            logger.debug(f"Turn {self.turn_count}: Calling GLM API...")
            response = await self._call_glm_api()
            
            # Convert to AssistantMessage format
            assistant_msg = convert_glm_to_assistant_message(response)
            
            # Yield the assistant message
            yield assistant_msg
            
            # Check finish reason
            finish_reason = response.choices[0].finish_reason
            logger.debug(f"Finish reason: {finish_reason}")
            
            if finish_reason == "tool_calls":
                # Execute tools and continue loop
                logger.debug("Tool calls detected, executing...")
                tool_results = await self._execute_tools(response)
                
                # Yield tool results as UserMessage
                user_msg = convert_tool_results_to_user_message(tool_results)
                yield user_msg
                
                # Add tool results to message history
                tool_messages = format_tool_results_for_glm(tool_results)
                self.messages.extend(tool_messages)
                
            elif finish_reason in ("stop", "length"):
                # Normal completion
                logger.debug("Conversation complete")
                break
            elif finish_reason == "sensitive":
                # Content filtered
                logger.warning("Response filtered by content policy")
                break
            else:
                # Unknown finish reason
                logger.warning(f"Unknown finish reason: {finish_reason}")
                break
        
        if self.turn_count >= self.options.max_turns:
            logger.warning(f"Max turns ({self.options.max_turns}) reached")
    
    async def _call_glm_api(self) -> Any:
        """
        Call GLM API with current message history.
        
        Returns:
            API response object
        """
        kwargs = {
            "model": self.options.get_glm_model(),
            "messages": self.messages,
            "temperature": self.options.get_temperature(),
            "top_p": self.options.get_top_p(),
        }
        
        # Note: The Z.AI OpenAI-compatible endpoint doesn't support 
        # GLM-specific parameters like thinking, clear_thinking, do_sample, top_k, or reasoning
        # These would need the native GLM API endpoint instead
        
        # Add tools if available
        if self.tools:
            kwargs["tools"] = self.tools
            kwargs["tool_choice"] = "auto"
        
        # Add structured output format if specified
        if self.options.output_format:
            # GLM supports JSON schema similar to OpenAI
            kwargs["response_format"] = self.options.output_format
        
        try:
            # Add 2-minute timeout to prevent indefinite hanging
            # This is especially important for merge operations where the prompt can be very large
            API_TIMEOUT_SECONDS = 120
            try:
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(**kwargs),
                    timeout=API_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                error_msg = f"GLM API call timed out after {API_TIMEOUT_SECONDS} seconds. The prompt may be too large or the server may be overloaded."
                logger.error(error_msg)
                print(f"[AI-MERGE] ❌ {error_msg}", flush=True)
                raise TimeoutError(error_msg)
            
            # Add assistant response to history
            choice = response.choices[0]
            msg_dict = {
                "role": "assistant",
                "content": choice.message.content or ""
            }
            
            # Add tool calls to message if present
            if hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
                msg_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in choice.message.tool_calls
                ]
            
            self.messages.append(msg_dict)
            
            return response
            
        except Exception as e:
            logger.error(f"GLM API call failed: {e}")
            raise
    
    async def _execute_tools(self, response: Any) -> list[dict]:
        """
        Execute tool calls from GLM response.
        
        Args:
            response: GLM API response with tool_calls
        
        Returns:
            List of tool results with format:
            [{"tool_call_id": str, "content": str, "is_error": bool}, ...]
        """
        results = []
        
        choice = response.choices[0]
        if not hasattr(choice.message, 'tool_calls'):
            return results
        
        for tool_call in choice.message.tool_calls:
            tool_name = tool_call.function.name
            tool_id = tool_call.id
            
            try:
                # Parse arguments
                args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse tool arguments: {e}")
                results.append({
                    "tool_call_id": tool_id,
                    "content": f"Error: Invalid JSON arguments - {e}",
                    "is_error": True
                })
                continue
            
            # Execute tool
            logger.debug(f"Executing tool: {tool_name}")
            try:
                result = await self._execute_single_tool(tool_name, args)
                results.append({
                    "tool_call_id": tool_id,
                    "content": json.dumps(result) if isinstance(result, dict) else str(result),
                    "is_error": False
                })
            except Exception as e:
                logger.error(f"Tool execution failed: {tool_name} - {e}")
                results.append({
                    "tool_call_id": tool_id,
                    "content": f"Error: {str(e)}",
                    "is_error": True
                })
        
        return results
    
    async def _execute_single_tool(self, tool_name: str, args: dict) -> Any:
        """
        Execute a single tool (core tool or MCP tool).
        
        Args:
            tool_name: Name of the tool
            args: Tool arguments
        
        Returns:
            Tool execution result
        
        Raises:
            ValueError: If tool is not found
        """
        # Check if this is an MCP tool
        if tool_name.startswith("mcp__") and self._mcp_manager:
            logger.debug(f"Executing MCP tool: {tool_name}")
            result = await self._mcp_manager.execute_tool(tool_name, args)
            logger.debug(f"MCP tool {tool_name} result: {str(result)[:200]}")
            return result
        
        # Otherwise, use core tool executor
        from .glm_tools import get_tool_executor
        
        # Get tool executor
        executor = get_tool_executor(tool_name)
        if not executor:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        # Add context arguments
        kwargs = {}
        if self.options.cwd:
            kwargs["cwd"] = Path(self.options.cwd)
        
        # For Bash, add security profile
        if tool_name == "Bash" and self.security_profile:
            kwargs["security_profile"] = self.security_profile
        
        # Execute tool
        logger.debug(f"Executing {tool_name} with args: {args}")
        result = await executor(args, **kwargs)
        logger.debug(f"Tool {tool_name} result: {str(result)[:200]}")
        
        return result
    
    def _build_tool_definitions(self) -> list[dict]:
        """
        Build GLM-compatible tool definitions from allowed_tools.
        
        Returns:
            List of tool definitions in GLM function calling format
        """
        # Tool definitions now handled by registry
        from .glm_tools import get_tool_definitions
        return get_tool_definitions(self.options.allowed_tools)
    
    def _load_security_profile(self) -> Any:
        """
        Load security profile for bash command validation.
        
        Returns:
            SecurityProfile instance or None
        """
        if not self.options.cwd:
            return None
        
        try:
            from security.profile import get_security_profile
            profile = get_security_profile(Path(self.options.cwd))
            logger.info("Loaded security profile for bash validation")
            return profile
        except ImportError:
            logger.warning("Security module not available")
            return None
        except Exception as e:
            logger.error(f"Failed to load security profile: {e}")
            return None
    
    def _load_security_settings(self) -> dict:
        """
        Load security settings from JSON file.
        
        Returns:
            Security settings dict or empty dict if not found
        """
        if not self.options.settings:
            return {}
        
        settings_path = Path(self.options.settings)
        if not settings_path.exists():
            logger.warning(f"Security settings file not found: {settings_path}")
            return {}
        
        try:
            with open(settings_path) as f:
                settings = json.load(f)
            logger.info(f"Loaded security settings from {settings_path}")
            return settings
        except Exception as e:
            logger.error(f"Failed to load security settings: {e}")
            return {}
