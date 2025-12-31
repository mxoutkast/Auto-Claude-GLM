"""
Tool Decorators
===============

GLM-compatible tool decorator that works without Claude SDK.
Provides a simple way to define tools with metadata.
"""

from functools import wraps
from typing import Any, Callable, Dict


def tool(name: str, description: str, parameters: Dict[str, type]) -> Callable:
    """
    Decorator to define a tool function with metadata.
    
    Compatible replacement for claude_agent_sdk.tool decorator.
    
    Args:
        name: Tool name (used for identification)
        description: Human-readable description of what the tool does
        parameters: Dict mapping parameter names to their types
        
    Returns:
        Decorated function with attached metadata
        
    Example:
        @tool(
            "update_status",
            "Updates a task status",
            {"task_id": str, "status": str}
        )
        async def update_status(args: dict) -> dict:
            # Implementation
            return {"content": [{"type": "text", "text": "Done"}]}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        # Attach metadata to the function
        wrapper._tool_name = name
        wrapper._tool_description = description
        wrapper._tool_parameters = parameters
        wrapper._is_tool = True
        
        return wrapper
    
    return decorator


def get_tool_metadata(func: Callable) -> Dict[str, Any]:
    """
    Extract tool metadata from a decorated function.
    
    Args:
        func: A tool-decorated function
        
    Returns:
        Dict with name, description, and parameters
        
    Raises:
        ValueError: If function is not a tool
    """
    if not getattr(func, "_is_tool", False):
        raise ValueError(f"Function {func.__name__} is not a decorated tool")
    
    return {
        "name": func._tool_name,
        "description": func._tool_description,
        "parameters": func._tool_parameters,
    }


def is_tool(func: Callable) -> bool:
    """Check if a function is a decorated tool."""
    return getattr(func, "_is_tool", False)
