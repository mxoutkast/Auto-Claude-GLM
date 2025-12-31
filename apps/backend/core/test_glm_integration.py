"""GLM Integration Tests
=======================

Comprehensive integration tests for GLM client with real API calls.
Requires ZHIPUAI_API_KEY environment variable.

Run with:
    python -m pytest core/test_glm_integration.py -v
    # or
    python core/test_glm_integration.py

Note: These tests make real API calls and will consume API credits.
Set SKIP_API_TESTS=1 to skip tests requiring API key.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


def check_api_key():
    """Check if ZHIPUAI_API_KEY is set."""
    api_key = os.environ.get("ZHIPUAI_API_KEY")
    if not api_key:
        print("⚠ ZHIPUAI_API_KEY not set - skipping API tests")
        print("  Get your key from: https://open.bigmodel.cn/")
        return False
    return True


def check_skip_api_tests():
    """Check if API tests should be skipped."""
    return os.environ.get("SKIP_API_TESTS") == "1"


@pytest.mark.asyncio
async def test_glm_client_basic_query():
    """Test basic query with GLM client."""
    if not check_api_key() or check_skip_api_tests():
        return False
    
    print("\n" + "=" * 60)
    print("Test 1: Basic Query")
    print("=" * 60)
    
    from core.glm_client import GLMAgentClient
    from core.glm_options import GLMAgentOptions
    
    options = GLMAgentOptions(
        model="glm-4.7",  # Use standard model
        system_prompt="You are a helpful assistant. Be concise.",
        allowed_tools=[],  # No tools for this test
        max_turns=1,
    )
    
    try:
        client = GLMAgentClient(options=options)
        async with client:
            print("Querying: What is 2 + 2?")
            await client.query("What is 2 + 2? Answer with just the number.")
            
            # Collect response
            response_text = ""
            async for message in client.receive_response():
                if hasattr(message, 'text'):
                    response_text += message.text
            
            print(f"Response: {response_text}")
            
            # Check response contains "4"
            if "4" in response_text:
                print("[PASS] Basic query works")
                return True
            else:
                print(f"[FAIL] Unexpected response: {response_text}")
                return False
    except Exception as e:
        print(f"[FAIL] Basic query failed: {e}")
        import traceback
        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_glm_client_with_read_tool():
    """Test GLM client with Read tool."""
    if not check_api_key() or check_skip_api_tests():
        return False
    
    print("\n" + "=" * 60)
    print("Test 2: Read Tool")
    print("=" * 60)
    
    from core.glm_client import GLMAgentClient
    from core.glm_options import GLMAgentOptions
    
    # Create a test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Hello from GLM test!")
        test_file = Path(f.name)
    
    try:
        options = GLMAgentOptions(
            model="glm-4.5-air",
            system_prompt="You are a helpful file assistant.",
            allowed_tools=["Read"],
            max_turns=3,
            cwd=str(test_file.parent),
        )
        
        client = GLMAgentClient(options=options)
        async with client:
            query = f"Read the file {test_file.name} and tell me what it says."
            print(f"Querying: {query}")
            await client.query(query)
            
            # Collect response
            response_text = ""
            async for message in client.receive_response():
                if hasattr(message, 'text'):
                    response_text += message.text
            
            print(f"Response: {response_text}")
            
            # Check if response mentions the content
            if "Hello from GLM test" in response_text or "GLM test" in response_text:
                print("[PASS] Read tool works")
                return True
            else:
                print(f"⚠ Response doesn't mention file content: {response_text}")
                return False
    except Exception as e:
        print(f"[FAIL] Read tool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        test_file.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_glm_client_with_write_tool():
    """Test GLM client with Write tool."""
    if not check_api_key() or check_skip_api_tests():
        return False
    
    print("\n" + "=" * 60)
    print("Test 3: Write Tool")
    print("=" * 60)
    
    from core.glm_client import GLMAgentClient
    from core.glm_options import GLMAgentOptions
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        test_file = test_dir / "test_output.txt"
        
        try:
            options = GLMAgentOptions(
                model="glm-4.5-air",
                system_prompt="You are a helpful file assistant.",
                allowed_tools=["Write"],
                max_turns=3,
                cwd=str(test_dir),
            )
            
            client = GLMAgentClient(options=options)
            async with client:
                query = f"Write 'GLM integration test successful!' to the file {test_file.name}"
                print(f"Querying: {query}")
                await client.query(query)
                
                # Collect response
                response_text = ""
                async for message in client.receive_response():
                    if hasattr(message, 'text'):
                        response_text += message.text
                
                print(f"Response: {response_text}")
                
                # Check if file was created
                if test_file.exists():
                    content = test_file.read_text()
                    print(f"File content: {content}")
                    if "GLM integration test successful" in content:
                        print("[PASS] Write tool works")
                        return True
                    else:
                        print(f"⚠ File created but wrong content: {content}")
                        return False
                else:
                    print("[FAIL] File was not created")
                    return False
        except Exception as e:
            print(f"[FAIL] Write tool test failed: {e}")
            import traceback
            traceback.print_exc()
            return False


@pytest.mark.asyncio
async def test_glm_client_multi_turn():
    """Test multi-turn conversation with GLM client."""
    if not check_api_key() or check_skip_api_tests():
        return False
    
    print("\n" + "=" * 60)
    print("Test 4: Multi-Turn Conversation")
    print("=" * 60)
    
    from core.glm_client import GLMAgentClient
    from core.glm_options import GLMAgentOptions
    
    options = GLMAgentOptions(
        model="glm-4.7",
        system_prompt="You are a helpful assistant. Remember context from previous messages.",
        allowed_tools=[],
        max_turns=3,
    )
    
    try:
        client = GLMAgentClient(options=options)
        async with client:
            # Turn 1
            print("Turn 1: My name is Alice")
            await client.query("My name is Alice. Remember this.")
            response1 = ""
            async for message in client.receive_response():
                if hasattr(message, 'text'):
                    response1 += message.text
            print(f"Response 1: {response1}")
            
            # Turn 2
            print("Turn 2: What is my name?")
            await client.query("What is my name?")
            response2 = ""
            async for message in client.receive_response():
                if hasattr(message, 'text'):
                    response2 += message.text
            print(f"Response 2: {response2}")
            
            # Check if it remembers
            if "Alice" in response2:
                print("[PASS] Multi-turn conversation works")
                return True
            else:
                print(f"⚠ Didn't remember name: {response2}")
                return False
    except Exception as e:
        print(f"[FAIL] Multi-turn test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_provider_switching():
    """Test that GLM is now the only provider (no switching needed)."""
    print("\n" + "=" * 60)
    print("Test 5: GLM-Only Provider")
    print("=" * 60)
    
    from core.client import create_client
    from core.glm_client import GLMAgentClient
    
    # Ensure API key is set
    if not os.environ.get("ZHIPUAI_API_KEY"):
        os.environ["ZHIPUAI_API_KEY"] = "test_key"
    
    try:
        # Test that create_client returns GLM client
        client = create_client(
            project_dir=Path.cwd(),
            spec_dir=Path.cwd() / "spec",
            model="glm-4.7",
            agent_type="coder",
        )
        
        if not isinstance(client, GLMAgentClient):
            print(f"[FAIL] Expected GLMAgentClient, got {type(client)}")
            return False
        print("[PASS] create_client returns GLMAgentClient")
        
        # Verify model is correct
        if client.options.model != "glm-4.7":
            print(f"[FAIL] Expected model 'glm-4.7', got '{client.options.model}'")
            return False
        print("[PASS] Model is correctly set to glm-4.7")
        
        print("[PASS] GLM-only provider configuration works")
        return True
    except Exception as e:
        print(f"[FAIL] GLM-only provider test failed: {e}")
        return False


@pytest.mark.asyncio
async def test_simple_client_glm():
    """Test simple client with GLM provider."""
    if not check_api_key() or check_skip_api_tests():
        return False
    
    print("\n" + "=" * 60)
    print("Test 6: Simple Client with GLM")
    print("=" * 60)
    
    from core.simple_client import create_simple_client
    
    os.environ["AI_PROVIDER"] = "glm"
    
    try:
        client = create_simple_client(
            agent_type="merge_resolver",
            model="glm-4.5-air",
        )
        
        async with client:
            await client.query("What is 3 + 3? Answer with just the number.")
            
            # Collect response
            response_text = ""
            async for message in client.receive_response():
                if hasattr(message, 'text'):
                    response_text += message.text
            
            print(f"Response: {response_text}")
            
            if "6" in response_text:
                print("[PASS] Simple client with GLM works")
                return True
            else:
                print(f"⚠ Unexpected response: {response_text}")
                return False
    except Exception as e:
        print(f"[FAIL] Simple client test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_tool_filtering():
    """Test that GLM clients get core tools plus MCP tools when configured."""
    print("\n" + "=" * 60)
    print("Test 7: Tool Filtering")
    print("=" * 60)
    
    from core.client import create_client
    
    if not os.environ.get("ZHIPUAI_API_KEY"):
        os.environ["ZHIPUAI_API_KEY"] = "test_key"
    
    try:
        client = create_client(
            project_dir=Path.cwd(),
            spec_dir=Path.cwd() / "spec",
            model="glm-4.7",
            agent_type="coder",  # coder has many tools
            max_thinking_tokens=None,
            output_format=None,
        )
        
        core_tools = ["Read", "Write", "Edit", "Glob", "Grep", "Bash", "WebFetch", "WebSearch"]
        tools = client.options.allowed_tools
        
        # Check core tools are present
        for ct in core_tools:
            if ct not in tools:
                print(f"[FAIL] Missing core tool: {ct}")
                return False
        
        print(f"[PASS] Tool filtering works - {len(tools)} tools available")
        print(f"  Core Tools: {[t for t in tools if t in core_tools]}")
        # Show MCP tools if any
        mcp_tools = [t for t in tools if t not in core_tools]
        if mcp_tools:
            print(f"  MCP Tools: {mcp_tools[:5]}...")  # Show first 5
        return True
    except Exception as e:
        print(f"[FAIL] Tool filtering test failed: {e}")
        return False


async def main():
    """Run all integration tests."""
    print("=" * 60)
    print("GLM Integration Tests")
    print("=" * 60)
    
    if check_skip_api_tests():
        print("\n⚠ SKIP_API_TESTS=1 - Skipping API tests")
    
    if not check_api_key() and not check_skip_api_tests():
        print("\n⚠ No API key found - limited testing only")
        print("  Set ZHIPUAI_API_KEY to run full test suite")
    
    # Run tests
    results = []
    
    # Always run these (no API needed)
    results.append(("Provider Switching", await test_provider_switching()))
    results.append(("Tool Filtering", await test_tool_filtering()))
    
    # API tests
    if check_api_key() and not check_skip_api_tests():
        results.append(("Basic Query", await test_glm_client_basic_query()))
        results.append(("Read Tool", await test_glm_client_with_read_tool()))
        results.append(("Write Tool", await test_glm_client_with_write_tool()))
        results.append(("Multi-Turn", await test_glm_client_multi_turn()))
        results.append(("Simple Client", await test_simple_client_glm()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS] PASS" if result else "[FAIL] FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
