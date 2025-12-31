"""
GLM client wrapper for AI analysis.
"""

import os
from pathlib import Path
from typing import Any

from core.glm_client import GLMAgentClient
from core.glm_options import GLMAgentOptions


class ClaudeAnalysisClient:
    """Wrapper for GLM client with analysis-specific configuration.
    
    Note: Class named ClaudeAnalysisClient for backwards compatibility,
    but now uses GLM as the backend.
    """

    DEFAULT_MODEL = "glm-4.7"
    ALLOWED_TOOLS = ["Read", "Glob", "Grep"]
    MAX_TURNS = 50

    def __init__(self, project_dir: Path):
        """
        Initialize GLM client.

        Args:
            project_dir: Root directory of project being analyzed
        """
        if not os.environ.get("ZHIPUAI_API_KEY"):
            raise RuntimeError(
                "ZHIPUAI_API_KEY not set. Set your API key in .env file."
            )

        self.project_dir = project_dir

    async def run_analysis_query(self, prompt: str) -> str:
        """
        Run a GLM query for analysis.

        Args:
            prompt: The analysis prompt

        Returns:
            GLM's response text
        """
        client = self._create_client()

        async with client:
            await client.query(prompt)
            return await self._collect_response(client)

    def _create_client(self) -> GLMAgentClient:
        """
        Create configured GLM client.

        Returns:
            GLMAgentClient instance
        """
        system_prompt = (
            f"You are a senior software architect analyzing this codebase. "
            f"Your working directory is: {self.project_dir.resolve()}\n"
            f"Use Read, Grep, and Glob tools to analyze actual code. "
            f"Output your analysis as valid JSON only."
        )

        return GLMAgentClient(
            options=GLMAgentOptions(
                model=self.DEFAULT_MODEL,
                system_prompt=system_prompt,
                allowed_tools=self.ALLOWED_TOOLS,
                max_turns=self.MAX_TURNS,
                cwd=str(self.project_dir.resolve()),
            )
        )

    async def _collect_response(self, client: GLMAgentClient) -> str:
        """
        Collect text response from GLM client.

        Args:
            client: GLMAgentClient instance

        Returns:
            Collected response text
        """
        response_text = ""

        async for msg in client.receive_response():
            msg_type = type(msg).__name__

            if msg_type == "AssistantMessage":
                for content in msg.content:
                    if hasattr(content, "text"):
                        response_text += content.text

        return response_text
