"""
AI Client Configuration
========================

Functions for creating and configuring AI agent clients.

Uses GLM 4.7 (via OpenAI-compatible API) as the primary AI provider.

All AI interactions should use `create_client()` to ensure consistent authentication
and proper tool/MCP configuration. For simple message calls without full agent sessions,
use `create_simple_client()` from `core.simple_client`.

The client factory uses AGENT_CONFIGS from agents/tools_pkg/models.py as the
single source of truth for phase-aware tool and MCP server configuration.

Environment Variables:
    ZHIPUAI_API_KEY: Required - GLM API key
    GLM_BASE_URL: Optional - Custom GLM endpoint
    GLM_MODEL: Optional - Default model (defaults to glm-4.7)
"""

import json
import os
from pathlib import Path

from agents.tools_pkg import (
    CONTEXT7_TOOLS,
    ELECTRON_TOOLS,
    GRAPHITI_MCP_TOOLS,
    LINEAR_TOOLS,
    PUPPETEER_TOOLS,
    create_auto_claude_mcp_server,
    get_allowed_tools,
    get_required_mcp_servers,
    is_tools_available,
)

# Import GLM client
from core.glm_client import GLMAgentClient
from core.glm_options import GLMAgentOptions

from linear_updater import is_linear_enabled
from prompts_pkg.project_context import detect_project_capabilities, load_project_index
from security import bash_security_hook


def get_electron_debug_port() -> int:
    """Get the Electron debugging port from environment."""
    return int(os.environ.get("ELECTRON_DEBUG_PORT", "9222"))


def is_graphiti_mcp_enabled() -> bool:
    """
    Check if Graphiti MCP server integration is enabled.

    Requires GRAPHITI_MCP_URL to be set (e.g., http://localhost:8000/mcp/)
    This is separate from GRAPHITI_ENABLED which controls the Python library integration.
    """
    return bool(os.environ.get("GRAPHITI_MCP_URL"))


def get_graphiti_mcp_url() -> str:
    """Get the Graphiti MCP server URL."""
    return os.environ.get("GRAPHITI_MCP_URL", "http://localhost:8000/mcp/")


def is_electron_mcp_enabled() -> bool:
    """
    Check if Electron MCP server integration is enabled.

    Requires ELECTRON_MCP_ENABLED to be set to 'true'.
    When enabled, QA agents can use Puppeteer MCP tools to connect to Electron apps
    via Chrome DevTools Protocol on the configured debug port.
    """
    return os.environ.get("ELECTRON_MCP_ENABLED", "").lower() == "true"


def get_electron_debug_port() -> int:
    """Get the Electron remote debugging port (default: 9222)."""
    return int(os.environ.get("ELECTRON_DEBUG_PORT", "9222"))


def should_use_claude_md() -> bool:
    """Check if CLAUDE.md instructions should be included in system prompt."""
    return os.environ.get("USE_CLAUDE_MD", "").lower() == "true"


def load_claude_md(project_dir: Path) -> str | None:
    """
    Load CLAUDE.md content from project root if it exists.

    Args:
        project_dir: Root directory of the project

    Returns:
        Content of CLAUDE.md if found, None otherwise
    """
    claude_md_path = project_dir / "CLAUDE.md"
    if claude_md_path.exists():
        try:
            return claude_md_path.read_text(encoding="utf-8")
        except Exception:
            return None
    return None


def create_client(
    project_dir: Path,
    spec_dir: Path,
    model: str,
    agent_type: str = "coder",
    max_thinking_tokens: int | None = None,
    output_format: dict | None = None,
) -> GLMAgentClient:
    """
    Create a GLM AI agent client with multi-layered security.

    Uses AGENT_CONFIGS for phase-aware tool and MCP server configuration.
    Only starts MCP servers that the agent actually needs, reducing context
    window bloat and startup latency.

    Args:
        project_dir: Root directory for the project (working directory)
        spec_dir: Directory containing the spec (for settings file)
        model: Model identifier (e.g., "glm-4.7", "glm-4.5-air")
        agent_type: Agent type identifier from AGENT_CONFIGS
                   (e.g., 'coder', 'planner', 'qa_reviewer', 'spec_gatherer')
        max_thinking_tokens: Token budget for extended thinking (None = disabled)
                            - ultrathink: 16000 (spec creation)
                            - high: 10000 (QA review)
                            - medium: 5000 (planning, validation)
                            - None: disabled (coding)
        output_format: Optional structured output format for validated JSON responses.
                      Use {"type": "json_schema", "schema": Model.model_json_schema()}

    Returns:
        Configured GLMAgentClient

    Raises:
        ValueError: If agent_type is not found in AGENT_CONFIGS or API key missing
        RuntimeError: If openai package is not available

    Security layers (defense in depth):
    1. Permissions - File operations restricted to project_dir only
    2. Security hooks - Bash commands validated against an allowlist
       (see security.py for ALLOWED_COMMANDS)
    3. Tool filtering - Each agent type only sees relevant tools (prevents misuse)
    """
    # Check API key
    if not os.environ.get("ZHIPUAI_API_KEY"):
        raise ValueError(
            "ZHIPUAI_API_KEY environment variable required.\n"
            "Get your key from: https://open.bigmodel.cn/"
        )
    
    # Load project capabilities
    project_index = load_project_index(project_dir)
    project_capabilities = detect_project_capabilities(project_index)
    
    # Check if Linear integration is enabled
    linear_enabled = is_linear_enabled()
    linear_api_key = os.environ.get("LINEAR_API_KEY", "")
    
    # Check if custom auto-claude tools are available
    auto_claude_tools_enabled = is_tools_available()
    
    # Get allowed tools using phase-aware configuration
    allowed_tools_list = get_allowed_tools(
        agent_type,
        project_capabilities,
        linear_enabled,
    )
    
    # Get required MCP servers for this agent type
    required_servers = get_required_mcp_servers(
        agent_type,
        project_capabilities,
        linear_enabled,
    )
    
    # Build MCP server configurations
    mcp_servers = {}
    
    if "context7" in required_servers:
        mcp_servers["context7"] = {
            "command": "npx",
            "args": ["-y", "@upstash/context7-mcp"],
        }
    
    if "electron" in required_servers:
        mcp_servers["electron"] = {
            "command": "npm",
            "args": ["exec", "electron-mcp-server"],
        }
    
    if "puppeteer" in required_servers:
        mcp_servers["puppeteer"] = {
            "command": "npx",
            "args": ["puppeteer-mcp-server"],
        }
    
    if "linear" in required_servers:
        mcp_servers["linear"] = {
            "type": "http",
            "url": "https://mcp.linear.app/mcp",
            "headers": {"Authorization": f"Bearer {linear_api_key}"},
        }
    
    # Graphiti MCP server for knowledge graph memory
    graphiti_mcp_enabled = "graphiti" in required_servers
    if graphiti_mcp_enabled:
        graphiti_url = os.environ.get("GRAPHITI_MCP_URL", "http://localhost:8000")
        mcp_servers["graphiti-memory"] = {
            "type": "http",
            "url": graphiti_url,
        }
    
    # Build system prompt
    base_prompt = (
        f"You are an expert full-stack developer building production-quality software. "
        f"Your working directory is: {project_dir.resolve()}\n"
        f"Your filesystem access is RESTRICTED to this directory only. "
        f"Use relative paths (starting with ./) for all file operations. "
        f"Never use absolute paths or try to access files outside your working directory.\n\n"
        f"IMPORTANT TOOL USAGE RULES:\n"
        f"- Use the Write tool to create or update files (NOT bash commands like cat > file)\n"
        f"- Use the Edit tool to modify existing files (NOT sed or other bash text tools)\n"
        f"- Use the Read tool to read file contents (NOT cat or head)\n"
        f"- Use Bash tool ONLY for: running tests, building projects, starting servers, or system commands\n"
        f"- NEVER use bash heredocs (<<EOF) or redirection (>) for file writes - use Write tool\n\n"
        f"You follow existing code patterns, write clean maintainable code, and verify "
        f"your work through thorough testing. You communicate progress through Git commits "
        f"and build-progress.txt updates."
    )
    
    # Include CLAUDE.md if enabled (project instructions work for any AI)
    if should_use_claude_md():
        claude_md_content = load_claude_md(project_dir)
        if claude_md_content:
            base_prompt = f"{base_prompt}\n\n# Project Instructions (from CLAUDE.md)\n\n{claude_md_content}"
            print("   - Project instructions: included from CLAUDE.md")
    
    # Display configuration
    print(f"AI Provider: GLM ({model})")
    print(f"Security settings:")
    print(f"   - Filesystem restricted to: {project_dir.resolve()}")
    print(f"   - Bash commands restricted to allowlist")
    if max_thinking_tokens:
        print(f"   - Extended thinking: {max_thinking_tokens:,} tokens")
    else:
        print("   - Extended thinking: disabled")
    print(f"   - Tools: {len(allowed_tools_list)} allowed")
    
    # Show MCP servers
    if mcp_servers:
        mcp_list = list(mcp_servers.keys())
        print(f"   - MCP servers: {', '.join(mcp_list)}")
    else:
        print("   - MCP servers: none (minimal configuration)")
    
    # Show detected project capabilities for QA agents
    if agent_type in ("qa_reviewer", "qa_fixer") and any(project_capabilities.values()):
        caps = [
            k.replace("is_", "").replace("has_", "")
            for k, v in project_capabilities.items()
            if v
        ]
        print(f"   - Project capabilities: {', '.join(caps)}")
    print()
    
    # Create GLM options
    options = GLMAgentOptions(
        model=model,
        system_prompt=base_prompt,
        allowed_tools=allowed_tools_list,
        mcp_servers=mcp_servers,
        max_turns=1000,
        cwd=str(project_dir.resolve()),
        max_thinking_tokens=max_thinking_tokens,
        output_format=output_format,
    )
    
    return GLMAgentClient(options=options)
