"""
GLM Tools Package
=================

Tool executors for GLM Agent Client.

Implements file system operations, bash execution, and web access
with security validation and error handling.

Tools:
------
- Filesystem: Read, Write, Edit, Glob, Grep
- Execution: Bash
- Web: WebFetch, WebSearch

Each tool validates inputs, respects security boundaries, and returns
structured results.
"""

from .bash import execute_bash
from .filesystem import execute_edit, execute_glob, execute_grep, execute_read, execute_write
from .registry import get_tool_definitions, get_tool_executor
from .web import execute_web_fetch, execute_web_search

__all__ = [
    # Filesystem
    "execute_read",
    "execute_write",
    "execute_edit",
    "execute_glob",
    "execute_grep",
    # Bash
    "execute_bash",
    # Web
    "execute_web_fetch",
    "execute_web_search",
    # Registry
    "get_tool_definitions",
    "get_tool_executor",
]
