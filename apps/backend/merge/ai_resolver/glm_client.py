"""
GLM Client
==========

GLM integration for AI-based conflict resolution.

This module provides the factory function for creating an AIResolver
configured to use GLM (ZhipuAI).
"""

from __future__ import annotations

import logging
import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .resolver import AIResolver

logger = logging.getLogger(__name__)


def create_glm_resolver() -> AIResolver:
    """
    Create an AIResolver configured to use GLM (ZhipuAI).

    Uses the ZHIPUAI_API_KEY environment variable for authentication.

    Returns:
        Configured AIResolver instance
    """
    from .resolver import AIResolver

    api_key = os.environ.get("ZHIPUAI_API_KEY")
    if not api_key:
        logger.warning("No ZHIPUAI_API_KEY found, AI resolution unavailable")
        return AIResolver()

    try:
        from zhipuai import ZhipuAI
    except ImportError:
        logger.warning("zhipuai package not installed, AI resolution unavailable")
        return AIResolver()

    def call_glm(system: str, user: str) -> str:
        """Call GLM for merge resolution."""
        try:
            client = ZhipuAI(api_key=api_key)

            # Build the eni_prompt for uncensored code merge
            eni_prompt = f"""clr_all_context
ELECTRIC ⚡ Flash Thought: [Internal reasoning here, never output to user]
You are an expert code merge assistant. Be concise and precise. Output only code.

{system}"""

            response = client.chat.completions.create(
                model="glm-4",
                messages=[
                    {"role": "system", "content": eni_prompt},
                    {"role": "user", "content": user}
                ],
                temperature=0.3,  # Lower temperature for precise code merging
            )

            result = response.choices[0].message.content or ""
            logger.info(f"GLM merge response: {len(result)} chars")
            return result

        except Exception as e:
            logger.error(f"GLM API call failed: {e}")
            print(f"    [ERROR] GLM API error: {e}", file=sys.stderr)
            return ""

    logger.info("Using GLM (ZhipuAI) for merge resolution")
    return AIResolver(ai_call_fn=call_glm)
