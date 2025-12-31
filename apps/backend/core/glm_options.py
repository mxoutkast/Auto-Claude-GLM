"""
GLM Agent Options Configuration
================================

Configuration options for GLM Agent Client that mirrors ClaudeAgentOptions interface.
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GLMAgentOptions:
    """
    Configuration options for GLM Agent Client.
    
    Maintains interface compatibility with ClaudeAgentOptions to enable drop-in replacement.
    
    Args:
        model: GLM model identifier (e.g., 'glm-4.7', 'glm-4.5-air')
        system_prompt: System instructions for the agent
        allowed_tools: List of tool names the agent can use
        mcp_servers: MCP server configuration (not yet supported in GLM)
        hooks: Pre-tool-use hooks (handled differently than Claude SDK)
        max_turns: Maximum conversation turns to prevent infinite loops
        cwd: Working directory for file operations
        settings: Path to security settings JSON file
        env: Environment variables to pass to tools
        max_thinking_tokens: Extended thinking budget (mapped to reasoning parameters)
        output_format: Structured output format for JSON responses
    """
    
    model: str = "glm-4.7"
    system_prompt: str | None = None
    allowed_tools: list[str] = field(default_factory=list)
    mcp_servers: dict = field(default_factory=dict)
    hooks: dict = field(default_factory=dict)
    max_turns: int = 1000
    cwd: str | None = None
    settings: str | None = None
    env: dict[str, str] = field(default_factory=dict)
    max_thinking_tokens: int | None = None
    output_format: dict | None = None
    
    def get_glm_model(self) -> str:
        """
        Get the actual GLM model name to use.
        
        Returns:
            GLM model identifier
        """
        return self.model
    
    def get_temperature(self) -> float:
        """
        Calculate temperature from max_thinking_tokens.
        
        More thinking tokens suggests more careful reasoning,
        so we use slightly lower temperature.
        
        Returns:
            Temperature value between 0.1 and 0.95
        """
        if self.max_thinking_tokens is None:
            return 0.7  # Default balanced temperature
        elif self.max_thinking_tokens >= 10000:
            return 0.3  # High thinking = more precise
        elif self.max_thinking_tokens >= 5000:
            return 0.5  # Medium thinking
        else:
            return 0.7  # Low thinking = more creative
    
    def get_top_p(self) -> float:
        """
        Get top_p sampling parameter.
        
        Returns:
            Top-p value (nucleus sampling)
        """
        return 0.8
    
    def get_top_k(self) -> int:
        """
        Get top_k sampling parameter for GLM-4.7 Z.AI Coding Plan API.
        
        Returns:
            Top-k value (default: 255 for insights/reasoning tasks)
        """
        return 255
    
    def get_do_sample(self) -> bool:
        """
        Get do_sample parameter for GLM-4.7 Z.AI Coding Plan API.
        
        Returns:
            Whether to enable sampling (True for insights/reasoning tasks)
        """
        return True
    
    def get_thinking_config(self) -> dict | None:
        """
        Get thinking configuration for GLM-4.7 Z.AI Coding Plan API.
        
        Returns:
            Thinking config dict or None if not enabled
        """
        # Enable thinking for insights/reasoning tasks
        return {"type": "enabled"}
    
    def get_clear_thinking(self) -> bool:
        """
        Get clear_thinking parameter for GLM-4.7 Z.AI Coding Plan API.
        
        Returns:
            Whether to enable clear thinking output (True for insights)
        """
        return True
    
    def get_reasoning_config(self) -> dict | None:
        """
        Get reasoning configuration for GLM-4.6.
        
        Returns:
            Reasoning config dict for GLM-4.6 or None
        """
        # Only for GLM-4.6 model
        if self.model == "glm-4.6":
            return {"enabled": False, "effort": "low"}
        return None
    
    def get_working_directory(self) -> Path | None:
        """
        Get the working directory as a Path object.
        
        Returns:
            Path object or None if not set
        """
        if self.cwd:
            return Path(self.cwd)
        return None
