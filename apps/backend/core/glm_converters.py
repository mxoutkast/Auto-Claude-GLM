"""
GLM Message Format Converters
==============================

Converts between GLM API responses and Claude SDK-compatible message formats.
This allows existing code to work without changes.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class TextBlock:
    """Text content block in a message."""
    
    text: str
    
    def __str__(self) -> str:
        return self.text


@dataclass
class ToolUseBlock:
    """Tool use block in an assistant message."""
    
    name: str
    input: dict[str, Any]
    id: str
    
    def __str__(self) -> str:
        return f"Tool: {self.name}"


@dataclass
class ToolResultBlock:
    """Tool result block in a user message."""
    
    content: str
    is_error: bool
    tool_use_id: str
    
    def __str__(self) -> str:
        return self.content


@dataclass
class AssistantMessage:
    """
    Assistant message containing text and/or tool use blocks.
    
    Matches the format from claude-agent-sdk for compatibility.
    """
    
    content: list[TextBlock | ToolUseBlock]
    
    @property
    def text(self) -> str:
        """Get combined text from all TextBlock content."""
        text_parts = []
        for block in self.content:
            if isinstance(block, TextBlock):
                text_parts.append(block.text)
        return "\n".join(text_parts)
    
    def __str__(self) -> str:
        parts = []
        for block in self.content:
            parts.append(str(block))
        return "\n".join(parts)


@dataclass
class UserMessage:
    """
    User message containing tool results.
    
    Matches the format from claude-agent-sdk for compatibility.
    """
    
    content: list[ToolResultBlock]
    
    def __str__(self) -> str:
        parts = []
        for block in self.content:
            parts.append(str(block))
        return "\n".join(parts)


def convert_glm_to_assistant_message(response: Any) -> AssistantMessage:
    """
    Convert GLM API response to Claude-compatible AssistantMessage.
    
    Args:
        response: GLM API response object (openai.ChatCompletion)
    
    Returns:
        AssistantMessage with TextBlock and/or ToolUseBlock content
    """
    content = []
    
    if not response.choices:
        return AssistantMessage(content=[])
    
    choice = response.choices[0]
    message = choice.message
    
    # Add text content if present
    if message.content:
        content.append(TextBlock(text=message.content))
    
    # Add tool calls if present
    if hasattr(message, 'tool_calls') and message.tool_calls:
        import json
        for tool_call in message.tool_calls:
            # Parse arguments - GLM returns JSON string
            try:
                arguments = json.loads(tool_call.function.arguments)
            except (json.JSONDecodeError, AttributeError):
                arguments = {}
            
            content.append(ToolUseBlock(
                name=tool_call.function.name,
                input=arguments,
                id=tool_call.id
            ))
    
    return AssistantMessage(content=content)


def convert_tool_results_to_user_message(results: list[dict]) -> UserMessage:
    """
    Convert tool execution results to Claude-compatible UserMessage.
    
    Args:
        results: List of tool execution results with keys:
                - tool_call_id: Tool call identifier
                - content: Result content as string
                - is_error: Whether execution failed
    
    Returns:
        UserMessage with ToolResultBlock content
    """
    content = []
    
    for result in results:
        content.append(ToolResultBlock(
            content=result["content"],
            is_error=result.get("is_error", False),
            tool_use_id=result["tool_call_id"]
        ))
    
    return UserMessage(content=content)


def format_tool_results_for_glm(results: list[dict]) -> list[dict]:
    """
    Format tool results for GLM API consumption.
    
    Args:
        results: List of tool execution results
    
    Returns:
        List of messages in GLM tool message format
    """
    messages = []
    
    for result in results:
        messages.append({
            "role": "tool",
            "content": result["content"],
            "tool_call_id": result["tool_call_id"]
        })
    
    return messages
