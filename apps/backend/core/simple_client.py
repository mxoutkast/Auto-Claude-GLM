"""
Simple GLM Client Factory
=========================

Factory for creating minimal GLM clients for single-turn utility operations
like commit message generation, merge conflict resolution, and batch analysis.

These clients don't need full security configurations, MCP servers, or hooks.
Use `create_client()` from `core.client` for full agent sessions with security.

Example usage:
    from core.simple_client import create_simple_client

    # For commit message generation (text-only, no tools)
    client = create_simple_client(agent_type="commit_message")

    # For merge conflict resolution (text-only, no tools)
    client = create_simple_client(agent_type="merge_resolver")

    # For insights extraction (read tools only)
    client = create_simple_client(agent_type="insights", cwd=project_dir)
"""

import os
from pathlib import Path

from agents.tools_pkg import get_agent_config, get_default_thinking_level
from core.glm_client import GLMAgentClient
from core.glm_options import GLMAgentOptions
from phase_config import get_thinking_budget


def create_simple_client(
    agent_type: str = "merge_resolver",
    model: str = "glm-4.7",
    system_prompt: str | None = None,
    cwd: Path | None = None,
    max_turns: int = 1,
    max_thinking_tokens: int | None = None,
) -> GLMAgentClient:
    """Create a minimal GLM client for single-turn utility operations.
    
    This factory creates lightweight clients without MCP servers, security hooks,
    or full permission configurations. Use for text-only analysis tasks.

    Args:
        agent_type: Agent type from AGENT_CONFIGS. Determines available tools.
                   Common utility types:
                   - "merge_resolver" - Text-only merge conflict analysis
                   - "commit_message" - Text-only commit message generation
                   - "insights" - Read-only code insight extraction
                   - "batch_analysis" - Read-only batch issue analysis
                   - "batch_validation" - Read-only validation
        model: Model to use (e.g., "glm-4.7", "glm-4.5-air")
        system_prompt: Optional custom system prompt (for specialized tasks)
        cwd: Working directory for file operations (optional)
        max_turns: Maximum conversation turns (default: 1 for single-turn)
        max_thinking_tokens: Override thinking budget (None = use agent default from
                            AGENT_CONFIGS, converted using phase_config.THINKING_BUDGET_MAP)

    Returns:
        Configured GLMAgentClient

    Raises:
        ValueError: If agent_type is not found in AGENT_CONFIGS or API key missing
    """
    # Check API key
    if not os.environ.get("ZHIPUAI_API_KEY"):
        raise ValueError(
            "ZHIPUAI_API_KEY environment variable required for GLM provider.\n"
            "Get your key from: https://open.bigmodel.cn/"
        )
    
    # Get agent configuration (raises ValueError if unknown type)
    config = get_agent_config(agent_type)
    
    # Get tools from config (filter to core tools only)
    core_tools = ["Read", "Write", "Edit", "Glob", "Grep", "Bash", "WebFetch", "WebSearch"]
    allowed_tools = [t for t in config.get("tools", []) if t in core_tools]
    
    # Determine thinking budget using the single source of truth (phase_config.py)
    if max_thinking_tokens is None:
        thinking_level = get_default_thinking_level(agent_type)
        max_thinking_tokens = get_thinking_budget(thinking_level)
    
    options = GLMAgentOptions(
        model=model,
        system_prompt=system_prompt,
        allowed_tools=allowed_tools,
        max_turns=max_turns,
        cwd=str(cwd.resolve()) if cwd else None,
        max_thinking_tokens=max_thinking_tokens,
    )
    
    return GLMAgentClient(options=options)
