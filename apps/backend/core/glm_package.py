"""
GLM Core Package
================

GLM Agent Client implementation for Auto-Claude framework.

This package provides GLM 4.7 integration as a drop-in replacement
for Claude Agent SDK, maintaining interface compatibility while using
Zhipu AI's GLM models.

Components:
-----------
- GLMAgentClient: Main client class (mimics ClaudeSDKClient)
- GLMAgentOptions: Configuration options (mimics ClaudeAgentOptions)
- Message converters: Claude SDK-compatible message formats

Usage:
------
    from core.glm_client import GLMAgentClient
    from core.glm_options import GLMAgentOptions
    
    options = GLMAgentOptions(
        model="glm-4-plus",
        system_prompt="You are a helpful assistant",
        allowed_tools=["Read", "Write", "Bash"],
        cwd="/path/to/project"
    )
    
    async with GLMAgentClient(options=options) as client:
        await client.query("Read the README.md file")
        async for message in client.receive_response():
            print(message)

Environment Variables:
---------------------
- ZHIPUAI_API_KEY: Required API key from https://open.bigmodel.cn/
- GLM_BASE_URL: Optional custom endpoint (default: official endpoint)
- AI_PROVIDER: Set to "glm" to use GLM instead of Claude

Models:
-------
- glm-4-plus: Most capable, best for complex tasks
- glm-4-air: Faster, lighter version
- glm-4-flash: Fastest, for simple tasks
- glm-4-long: Extended context window

See: https://open.bigmodel.cn/dev/api/normal-model/glm-4
"""

from .glm_client import GLMAgentClient
from .glm_converters import (
    AssistantMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)
from .glm_options import GLMAgentOptions

__all__ = [
    "GLMAgentClient",
    "GLMAgentOptions",
    "AssistantMessage",
    "UserMessage",
    "TextBlock",
    "ToolUseBlock",
    "ToolResultBlock",
]
