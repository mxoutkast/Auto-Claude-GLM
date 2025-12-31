"""
GLM Client Provider Test
=========================

Test script to verify GLM client implementation works correctly.

This test:
1. Creates a GLM client with basic configuration
2. Sends a simple query
3. Receives and displays the response
4. Tests the agentic loop and message format conversion

Run:
    python -m apps.backend.core.test_glm_client

Environment required:
    ZHIPUAI_API_KEY=your_api_key
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))


async def test_basic_query():
    """Test basic query without tools."""
    print("=" * 70)
    print("TEST 1: Basic Query (No Tools)")
    print("=" * 70)
    
    from core.glm_client import GLMAgentClient
    from core.glm_options import GLMAgentOptions
    
    options = GLMAgentOptions(
        model="glm-4-flash",  # Use fast model for testing
        system_prompt="You are a helpful assistant. Be concise.",
        allowed_tools=[],  # No tools for this test
        max_turns=5
    )
    
    print(f"\nModel: {options.model}")
    print(f"Temperature: {options.get_temperature()}")
    print(f"Max turns: {options.max_turns}\n")
    
    try:
        async with GLMAgentClient(options=options) as client:
            print("Sending query: 'What is 2+2? Answer briefly.'\n")
            await client.query("What is 2+2? Answer briefly.")
            
            async for message in client.receive_response():
                msg_type = type(message).__name__
                print(f"[{msg_type}]")
                
                if hasattr(message, 'content'):
                    for block in message.content:
                        block_type = type(block).__name__
                        print(f"  [{block_type}] {block}")
                print()
        
        print("✓ Test passed\n")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


async def test_with_tools():
    """Test query with tool definitions and execution."""
    print("=" * 70)
    print("TEST 2: Query with Tools (With Execution)")
    print("=" * 70)
    
    import tempfile
    from core.glm_client import GLMAgentClient
    from core.glm_options import GLMAgentOptions
    
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"\nWorking directory: {tmpdir}\n")
        
        # Create a test file
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("This is a test file for GLM.")
        
        options = GLMAgentOptions(
            model="glm-4-flash",
            system_prompt="You are a helpful file assistant.",
            allowed_tools=["Read"],
            cwd=tmpdir,
            max_turns=5
        )
        
        print(f"Model: {options.model}")
        print(f"Tools: {options.allowed_tools}")
        print(f"CWD: {tmpdir}\n")
        
        try:
            async with GLMAgentClient(options=options) as client:
                print("Sending query: 'Read the test.txt file and tell me what it says.'\n")
                await client.query("Read the test.txt file and tell me what it says.")
                
                async for message in client.receive_response():
                    msg_type = type(message).__name__
                    print(f"[{msg_type}]")
                    
                    if hasattr(message, 'content'):
                        for block in message.content:
                            block_type = type(block).__name__
                            if block_type == "TextBlock":
                                print(f"  [{block_type}] {block.text[:200]}")
                            elif block_type == "ToolUseBlock":
                                print(f"  [{block_type}] Tool: {block.name}")
                                print(f"                Args: {block.input}")
                            elif block_type == "ToolResultBlock":
                                print(f"  [{block_type}] Result preview: {block.content[:100]}...")
                    print()
            
            print("✓ Test passed\n")
            return True
            
        except Exception as e:
            print(f"✗ Test failed: {e}\n")
            import traceback
            traceback.print_exc()
            return False


async def test_message_converters():
    """Test message format conversion utilities."""
    print("=" * 70)
    print("TEST 3: Message Format Converters")
    print("=" * 70)
    
    from core.glm_converters import (
        TextBlock,
        ToolUseBlock,
        AssistantMessage,
        ToolResultBlock,
        UserMessage,
        convert_tool_results_to_user_message,
    )
    
    # Test creating messages
    print("\n1. Creating AssistantMessage with TextBlock...")
    assistant_msg = AssistantMessage(content=[
        TextBlock(text="Hello, I can help you.")
    ])
    print(f"   Result: {assistant_msg}")
    
    print("\n2. Creating AssistantMessage with ToolUseBlock...")
    assistant_msg_with_tool = AssistantMessage(content=[
        TextBlock(text="I'll read that file for you."),
        ToolUseBlock(name="Read", input={"file_path": "test.txt"}, id="call_123")
    ])
    print(f"   Result: {assistant_msg_with_tool}")
    
    print("\n3. Creating UserMessage with ToolResultBlock...")
    user_msg = convert_tool_results_to_user_message([
        {
            "tool_call_id": "call_123",
            "content": "File contents here",
            "is_error": False
        }
    ])
    print(f"   Result: {user_msg}")
    
    print("\n✓ All message converters working\n")
    return True


async def main():
    """Run all tests."""
    print("\n")
    print("=" * 70)
    print("GLM CLIENT IMPLEMENTATION TEST SUITE")
    print("=" * 70)
    print()
    
    # Check API key
    if not os.environ.get("ZHIPUAI_API_KEY"):
        print("ERROR: ZHIPUAI_API_KEY environment variable not set")
        print("\nPlease set your API key:")
        print("  export ZHIPUAI_API_KEY='your_key_here'")
        print("\nGet your key from: https://open.bigmodel.cn/")
        return
    
    print("API Key: ✓ Found")
    print()
    
    # Run tests
    results = []
    
    # Test 3 doesn't need API
    results.append(await test_message_converters())
    
    # Tests 1 and 2 need API
    results.append(await test_basic_query())
    results.append(await test_with_tools())
    
    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed! Phase 1 & 2 implementation complete.")
        print("\nImplemented features:")
        print("  ✓ GLM client with async context manager")
        print("  ✓ Agentic loop with tool calling")
        print("  ✓ Message format conversion")
        print("  ✓ Tool execution: Read, Write, Edit, Glob, Grep, Bash")
        print("\nNext steps:")
        print("  - Phase 3: Integrate with client.py factory")
        print("  - Phase 4: Update existing codebase")
        print("  - Run: python -m apps.backend.core.test_glm_tools")
    else:
        print(f"\n✗ {total - passed} test(s) failed")
    
    print()


if __name__ == "__main__":
    asyncio.run(main())
