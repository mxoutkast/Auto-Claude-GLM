"""
Tool Registry for GLM Agent
============================

Central registry of tool definitions and executors.
Maps tool names to GLM function definitions and execution handlers.
"""

from pathlib import Path
from typing import Any, Callable

from .bash import execute_bash
from .filesystem import execute_edit, execute_glob, execute_grep, execute_read, execute_write
from .web import execute_web_fetch, execute_web_search


def get_tool_definitions(allowed_tools: list[str]) -> list[dict]:
    """
    Get GLM function calling definitions for allowed tools.
    
    Args:
        allowed_tools: List of tool names to include
    
    Returns:
        List of tool definitions in GLM format
    """
    # All available tool definitions
    ALL_TOOLS = {
        "Read": {
            "type": "function",
            "function": {
                "name": "Read",
                "description": "Read the complete contents of a file from the filesystem",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to read (relative or absolute)"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        },
        "Write": {
            "type": "function",
            "function": {
                "name": "Write",
                "description": "Write content to a file, creating it if it doesn't exist",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to write"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file"
                        }
                    },
                    "required": ["file_path", "content"]
                }
            }
        },
        "Edit": {
            "type": "function",
            "function": {
                "name": "Edit",
                "description": "Edit a file by replacing occurrences of old_string with new_string",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to edit"
                        },
                        "old_string": {
                            "type": "string",
                            "description": "String to replace (must match exactly)"
                        },
                        "new_string": {
                            "type": "string",
                            "description": "String to replace with"
                        }
                    },
                    "required": ["file_path", "old_string", "new_string"]
                }
            }
        },
        "Glob": {
            "type": "function",
            "function": {
                "name": "Glob",
                "description": "Find files matching a glob pattern (e.g., '**/*.py' for all Python files)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Glob pattern (supports ** for recursive search)"
                        }
                    },
                    "required": ["pattern"]
                }
            }
        },
        "Grep": {
            "type": "function",
            "function": {
                "name": "Grep",
                "description": "Search for a regex pattern in files matching a glob pattern",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Regular expression pattern to search for"
                        },
                        "file_pattern": {
                            "type": "string",
                            "description": "Glob pattern for files to search (default: **/*.py)"
                        },
                        "case_sensitive": {
                            "type": "boolean",
                            "description": "Whether search is case sensitive (default: true)"
                        }
                    },
                    "required": ["pattern"]
                }
            }
        },
        "Bash": {
            "type": "function",
            "function": {
                "name": "Bash",
                "description": "Execute a bash command in the working directory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "Bash command to execute"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Timeout in seconds (default: 300)"
                        }
                    },
                    "required": ["command"]
                }
            }
        },
        "WebFetch": {
            "type": "function",
            "function": {
                "name": "WebFetch",
                "description": "Fetch content from a URL",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to fetch"
                        }
                    },
                    "required": ["url"]
                }
            }
        },
        "WebSearch": {
            "type": "function",
            "function": {
                "name": "WebSearch",
                "description": "Perform a web search (Note: GLM 4.7 has built-in web_search - prefer using that)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 5)"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    }
    
    # Filter to allowed tools
    tools = []
    for tool_name in allowed_tools:
        if tool_name in ALL_TOOLS:
            tools.append(ALL_TOOLS[tool_name])
    
    return tools


def get_tool_executor(tool_name: str) -> Callable | None:
    """
    Get the execution function for a tool.
    
    Args:
        tool_name: Name of the tool
    
    Returns:
        Async function that executes the tool, or None if not found
    """
    EXECUTORS = {
        "Read": execute_read,
        "Write": execute_write,
        "Edit": execute_edit,
        "Glob": execute_glob,
        "Grep": execute_grep,
        "Bash": execute_bash,
        "WebFetch": execute_web_fetch,
        "WebSearch": execute_web_search,
    }
    
    return EXECUTORS.get(tool_name)
