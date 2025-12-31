"""
AI Resolver Module
==================

AI-based conflict resolution for the Auto Claude merge system.

This module provides intelligent conflict resolution using AI with
minimal context to reduce token usage and cost.

Components:
- AIResolver: Main resolver class
- ConflictContext: Minimal context for AI prompts
- create_claude_resolver: Factory for Claude-based resolver
- create_glm_resolver: Factory for GLM-based resolver
- create_ai_resolver: Auto-selects based on AI_PROVIDER env var

Usage:
    from merge.ai_resolver import AIResolver, create_ai_resolver

    # Create resolver with auto-selected provider (based on AI_PROVIDER env)
    resolver = create_ai_resolver()

    # Or create with specific provider
    from merge.ai_resolver import create_glm_resolver
    resolver = create_glm_resolver()

    # Resolve a conflict
    result = resolver.resolve_conflict(conflict, baseline_code, task_snapshots)
"""

import os

from .claude_client import create_claude_resolver
from .context import ConflictContext
from .glm_client import create_glm_resolver
from .resolver import AIResolver


def create_ai_resolver() -> AIResolver:
    """
    Create an AIResolver based on the AI_PROVIDER environment variable.

    Returns:
        AIResolver configured for the current provider (glm or claude)
    """
    provider = os.environ.get("AI_PROVIDER", "claude").lower()
    if provider == "glm":
        return create_glm_resolver()
    return create_claude_resolver()


__all__ = [
    "AIResolver",
    "ConflictContext",
    "create_ai_resolver",
    "create_claude_resolver",
    "create_glm_resolver",
]
