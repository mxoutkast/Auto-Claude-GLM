"""
Tool Registry
=============

Central registry for creating and managing auto-claude custom tools.

Note: With GLM integration, MCP tools are handled directly by the 
glm_mcp.py module. This registry provides tool definitions that can
be exposed via a custom MCP server if needed.
"""

from pathlib import Path

from .tools import (
    create_memory_tools,
    create_progress_tools,
    create_qa_tools,
    create_subtask_tools,
)


def create_all_tools(spec_dir: Path, project_dir: Path) -> list:
    """
    Create all custom tools with the given spec and project directories.

    Args:
        spec_dir: Path to the spec directory
        project_dir: Path to the project root

    Returns:
        List of all tool functions
    """
    all_tools = []

    # Create tools by category
    all_tools.extend(create_subtask_tools(spec_dir, project_dir))
    all_tools.extend(create_progress_tools(spec_dir, project_dir))
    all_tools.extend(create_memory_tools(spec_dir, project_dir))
    all_tools.extend(create_qa_tools(spec_dir, project_dir))

    return all_tools


def create_auto_claude_mcp_server(spec_dir: Path, project_dir: Path):
    """
    Create an MCP server with auto-claude custom tools.

    Note: For GLM integration, custom tools are exposed via HTTP MCP server.
    This function returns None as the auto-claude MCP server setup is 
    handled differently with GLM.

    Args:
        spec_dir: Path to the spec directory
        project_dir: Path to the project root

    Returns:
        None (GLM uses different MCP integration)
    """
    # For GLM, we don't create an SDK-based MCP server
    # MCP tools are handled via glm_mcp.py
    return None


def is_tools_available() -> bool:
    """Check if custom tools functionality is available.
    
    Returns True since tools are always available with GLM.
    """
    return True
