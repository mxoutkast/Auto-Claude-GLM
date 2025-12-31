"""Test Provider Switching
=======================

Quick test script to verify AI_PROVIDER switching works correctly.
Does not require API keys - just tests client creation logic.
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


def test_provider_detection():
    """Test get_ai_provider() function."""
    from core.client import get_ai_provider
    
    # Test default
    os.environ.pop("AI_PROVIDER", None)
    assert get_ai_provider() == "claude", "Default should be claude"
    
    # Test explicit claude
    os.environ["AI_PROVIDER"] = "claude"
    assert get_ai_provider() == "claude"
    
    # Test GLM
    os.environ["AI_PROVIDER"] = "glm"
    assert get_ai_provider() == "glm"
    
    # Test case insensitive
    os.environ["AI_PROVIDER"] = "GLM"
    assert get_ai_provider() == "glm"
    
    print("✓ Provider detection works")


def test_claude_client_creation():
    """Test Claude client creation (requires SDK)."""
    from core.client import CLAUDE_SDK_AVAILABLE
    
    if not CLAUDE_SDK_AVAILABLE:
        print("⚠ Claude SDK not available - skipping Claude test")
        return
    
    from core.client import _create_claude_client
    
    os.environ["AI_PROVIDER"] = "claude"
    os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = "test_token"
    
    try:
        client = _create_claude_client(
            project_dir=Path.cwd(),
            spec_dir=Path.cwd() / "spec",
            model="claude-sonnet-4-20250514",
            agent_type="coder",
            max_thinking_tokens=None,
            output_format=None,
        )
        print("✓ Claude client creation works")
    except Exception as e:
        print(f"✗ Claude client creation failed: {e}")


def test_glm_client_creation():
    """Test GLM client creation (requires openai package)."""
    try:
        from core.glm_client import GLMAgentClient
    except ImportError:
        print("⚠ GLM client not available - skipping GLM test")
        return
    
    from core.client import _create_glm_client
    
    os.environ["AI_PROVIDER"] = "glm"
    os.environ["ZHIPUAI_API_KEY"] = "test_key"
    
    try:
        client = _create_glm_client(
            project_dir=Path.cwd(),
            spec_dir=Path.cwd() / "spec",
            model="glm-4-plus",
            agent_type="coder",
            max_thinking_tokens=None,
            output_format=None,
        )
        print("✓ GLM client creation works")
        print(f"  - Model: {client.options.model}")
        print(f"  - Tools: {len(client.options.allowed_tools)}")
        print(f"  - Tool names: {client.options.allowed_tools}")
    except Exception as e:
        print(f"✗ GLM client creation failed: {e}")


def test_simple_client_switching():
    """Test simple client provider switching."""
    from core.simple_client import create_simple_client, CLAUDE_SDK_AVAILABLE
    
    # Test Claude
    if CLAUDE_SDK_AVAILABLE:
        os.environ["AI_PROVIDER"] = "claude"
        os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = "test_token"
        try:
            client = create_simple_client(agent_type="merge_resolver")
            print("✓ Simple Claude client creation works")
        except Exception as e:
            print(f"⚠ Simple Claude client failed (may need real token): {e}")
    
    # Test GLM
    try:
        from core.glm_client import GLMAgentClient
        os.environ["AI_PROVIDER"] = "glm"
        os.environ["ZHIPUAI_API_KEY"] = "test_key"
        try:
            client = create_simple_client(
                agent_type="merge_resolver",
                model="glm-4-flash"
            )
            print("✓ Simple GLM client creation works")
            print(f"  - Model: {client.options.model}")
            print(f"  - Tools: {client.options.allowed_tools}")
        except Exception as e:
            print(f"✗ Simple GLM client failed: {e}")
    except ImportError:
        print("⚠ GLM client not available - skipping simple GLM test")


def test_tool_filtering():
    """Test that GLM clients get core tools only."""
    try:
        from core.glm_client import GLMAgentClient
    except ImportError:
        print("⚠ GLM client not available - skipping tool filtering test")
        return
    
    from core.client import _create_glm_client
    
    os.environ["AI_PROVIDER"] = "glm"
    os.environ["ZHIPUAI_API_KEY"] = "test_key"
    
    try:
        # coder normally has MCP tools, but GLM should filter them out
        client = _create_glm_client(
            project_dir=Path.cwd(),
            spec_dir=Path.cwd() / "spec",
            model="glm-4-plus",
            agent_type="coder",
            max_thinking_tokens=None,
            output_format=None,
        )
        
        core_tools = ["Read", "Write", "Edit", "Glob", "Grep", "Bash", "WebFetch", "WebSearch"]
        tools = client.options.allowed_tools
        
        # Check all tools are in core_tools
        non_core = [t for t in tools if t not in core_tools]
        assert not non_core, f"Found non-core tools: {non_core}"
        
        print("✓ Tool filtering works - only core tools present")
        print(f"  - Tools: {tools}")
    except Exception as e:
        print(f"✗ Tool filtering test failed: {e}")


def main():
    """Run all tests."""
    print("Testing Auto-Claude Provider Switching")
    print("=" * 50)
    print()
    
    test_provider_detection()
    test_claude_client_creation()
    test_glm_client_creation()
    test_simple_client_switching()
    test_tool_filtering()
    
    print()
    print("=" * 50)
    print("Tests complete!")
    print()
    print("To test with real API:")
    print("  1. Set AI_PROVIDER=glm")
    print("  2. Set ZHIPUAI_API_KEY=your_key")
    print("  3. Run: python -m core.test_provider_switching")


if __name__ == "__main__":
    main()
