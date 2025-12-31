"""
GLM Tools Test Suite
====================

Tests for file system, bash, and web tools.

Run:
    python -m apps.backend.core.test_glm_tools
"""

import asyncio
import tempfile
from pathlib import Path

# Test filesystem tools
async def test_filesystem_tools():
    """Test Read, Write, Edit, Glob, Grep tools."""
    print("=" * 70)
    print("TEST: Filesystem Tools")
    print("=" * 70)
    
    from core.glm_tools.filesystem import (
        execute_read,
        execute_write,
        execute_edit,
        execute_glob,
        execute_grep
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        cwd = Path(tmpdir)
        print(f"\nWorking directory: {cwd}\n")
        
        # Test Write
        print("1. Testing Write...")
        result = await execute_write({
            "file_path": "test.txt",
            "content": "Hello World\nLine 2\nLine 3"
        }, cwd)
        
        if "error" in result:
            print(f"   ✗ Write failed: {result['error']}")
            return False
        print(f"   ✓ Wrote {result['bytes_written']} bytes")
        
        # Test Read
        print("\n2. Testing Read...")
        result = await execute_read({"file_path": "test.txt"}, cwd)
        
        if "error" in result:
            print(f"   ✗ Read failed: {result['error']}")
            return False
        print(f"   ✓ Read {len(result['content'])} chars")
        print(f"   Content preview: {result['content'][:50]}...")
        
        # Test Edit
        print("\n3. Testing Edit...")
        result = await execute_edit({
            "file_path": "test.txt",
            "old_string": "World",
            "new_string": "GLM"
        }, cwd)
        
        if "error" in result:
            print(f"   ✗ Edit failed: {result['error']}")
            return False
        print(f"   ✓ Made {result['replacements']} replacement(s)")
        
        # Verify edit
        verify = await execute_read({"file_path": "test.txt"}, cwd)
        if "Hello GLM" in verify.get("content", ""):
            print("   ✓ Edit verified")
        else:
            print("   ✗ Edit verification failed")
            return False
        
        # Create more files for Glob/Grep
        await execute_write({"file_path": "subdir/file1.py", "content": "import os\nprint('test')"}, cwd)
        await execute_write({"file_path": "subdir/file2.py", "content": "import sys\nprint('hello')"}, cwd)
        await execute_write({"file_path": "file3.txt", "content": "text file"}, cwd)
        
        # Test Glob
        print("\n4. Testing Glob...")
        result = await execute_glob({"pattern": "**/*.py"}, cwd)
        
        if "error" in result:
            print(f"   ✗ Glob failed: {result['error']}")
            return False
        print(f"   ✓ Found {result['count']} Python files")
        print(f"   Files: {result['files']}")
        
        # Test Grep
        print("\n5. Testing Grep...")
        result = await execute_grep({
            "pattern": "import",
            "file_pattern": "**/*.py"
        }, cwd)
        
        if "error" in result:
            print(f"   ✗ Grep failed: {result['error']}")
            return False
        print(f"   ✓ Found {result['total_matches']} matches")
        for match in result['matches'][:3]:
            print(f"     {match['file']}:{match['line']} - {match['content'][:50]}")
    
    print("\n✓ All filesystem tools passed\n")
    return True


async def test_bash_tool():
    """Test Bash tool execution."""
    print("=" * 70)
    print("TEST: Bash Tool")
    print("=" * 70)
    
    from core.glm_tools.bash import execute_bash
    
    with tempfile.TemporaryDirectory() as tmpdir:
        cwd = Path(tmpdir)
        print(f"\nWorking directory: {cwd}\n")
        
        # Test simple command
        print("1. Testing simple command (echo)...")
        result = await execute_bash({"command": "echo 'Hello from Bash'"}, cwd)
        
        if "error" in result:
            print(f"   ✗ Bash failed: {result['error']}")
            return False
        
        print(f"   Exit code: {result['exit_code']}")
        print(f"   Stdout: {result['stdout'].strip()}")
        
        if result['exit_code'] == 0 and "Hello from Bash" in result['stdout']:
            print("   ✓ Command executed successfully")
        else:
            print("   ✗ Unexpected result")
            return False
        
        # Test command that creates a file
        print("\n2. Testing file creation...")
        result = await execute_bash({
            "command": "echo 'test content' > output.txt"
        }, cwd)
        
        if result['exit_code'] == 0:
            # Verify file exists
            if (cwd / "output.txt").exists():
                print("   ✓ File created successfully")
            else:
                print("   ✗ File not created")
                return False
        else:
            print(f"   ✗ Command failed: {result.get('stderr', '')}")
            return False
        
        # Test command with error
        print("\n3. Testing error handling...")
        result = await execute_bash({"command": "nonexistent_command"}, cwd)
        
        if result['exit_code'] != 0:
            print(f"   ✓ Error detected (exit code: {result['exit_code']})")
        else:
            print("   ✗ Should have failed")
            return False
    
    print("\n✓ Bash tool tests passed\n")
    return True


async def test_tool_registry():
    """Test tool registry functions."""
    print("=" * 70)
    print("TEST: Tool Registry")
    print("=" * 70)
    
    from core.glm_tools.registry import get_tool_definitions, get_tool_executor
    
    # Test getting tool definitions
    print("\n1. Testing get_tool_definitions...")
    tools = get_tool_definitions(["Read", "Write", "Bash"])
    
    if len(tools) != 3:
        print(f"   ✗ Expected 3 tools, got {len(tools)}")
        return False
    
    print(f"   ✓ Got {len(tools)} tool definitions")
    for tool in tools:
        print(f"     - {tool['function']['name']}")
    
    # Test getting executors
    print("\n2. Testing get_tool_executor...")
    executors_to_test = ["Read", "Write", "Edit", "Glob", "Grep", "Bash"]
    
    for tool_name in executors_to_test:
        executor = get_tool_executor(tool_name)
        if executor is None:
            print(f"   ✗ No executor for {tool_name}")
            return False
        print(f"   ✓ {tool_name} executor: {executor.__name__}")
    
    # Test unknown tool
    print("\n3. Testing unknown tool...")
    executor = get_tool_executor("NonexistentTool")
    if executor is None:
        print("   ✓ Unknown tool returns None")
    else:
        print("   ✗ Should return None for unknown tool")
        return False
    
    print("\n✓ Tool registry tests passed\n")
    return True


async def test_integrated_workflow():
    """Test a complete workflow using multiple tools."""
    print("=" * 70)
    print("TEST: Integrated Workflow")
    print("=" * 70)
    
    from core.glm_tools.filesystem import execute_write, execute_read, execute_grep
    from core.glm_tools.bash import execute_bash
    
    with tempfile.TemporaryDirectory() as tmpdir:
        cwd = Path(tmpdir)
        print(f"\nWorking directory: {cwd}\n")
        
        # Workflow: Create Python file -> Run it -> Read output
        print("1. Create Python script...")
        script_content = """#!/usr/bin/env python3
print("Hello from Python script!")
print("This is line 2")
"""
        result = await execute_write({
            "file_path": "script.py",
            "content": script_content
        }, cwd)
        
        if "error" in result:
            print(f"   ✗ Failed: {result['error']}")
            return False
        print("   ✓ Script created")
        
        # Run the script
        print("\n2. Execute Python script...")
        result = await execute_bash({
            "command": "python script.py"
        }, cwd)
        
        if "error" in result or result['exit_code'] != 0:
            print(f"   ✗ Failed: {result.get('error', result.get('stderr'))}")
            return False
        print(f"   ✓ Script executed")
        print(f"   Output: {result['stdout'].strip()}")
        
        # Create multiple files and search
        print("\n3. Create multiple files and search...")
        await execute_write({"file_path": "data1.txt", "content": "ERROR: something failed"}, cwd)
        await execute_write({"file_path": "data2.txt", "content": "INFO: all good"}, cwd)
        await execute_write({"file_path": "data3.txt", "content": "ERROR: another issue"}, cwd)
        
        result = await execute_grep({
            "pattern": "ERROR",
            "file_pattern": "*.txt"
        }, cwd)
        
        if "error" in result:
            print(f"   ✗ Failed: {result['error']}")
            return False
        
        print(f"   ✓ Found {result['total_matches']} errors")
        for match in result['matches']:
            print(f"     {match['file']}: {match['content']}")
    
    print("\n✓ Integrated workflow passed\n")
    return True


async def main():
    """Run all tool tests."""
    print("\n")
    print("=" * 70)
    print("GLM TOOLS TEST SUITE - PHASE 2")
    print("=" * 70)
    print()
    
    results = []
    
    # Run tests
    results.append(await test_tool_registry())
    results.append(await test_filesystem_tools())
    results.append(await test_bash_tool())
    results.append(await test_integrated_workflow())
    
    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed! Phase 2 implementation complete.")
        print("\nTools implemented:")
        print("  ✓ Read - Read file contents")
        print("  ✓ Write - Write to files")
        print("  ✓ Edit - String replacement in files")
        print("  ✓ Glob - Find files by pattern")
        print("  ✓ Grep - Search in files")
        print("  ✓ Bash - Execute shell commands")
        print("\nNext steps:")
        print("  - Test with GLM API (set ZHIPUAI_API_KEY)")
        print("  - Phase 3: Integration with core/client.py")
        print("  - Phase 4: Update existing codebase to support GLM")
    else:
        print(f"\n✗ {total - passed} test(s) failed")
    
    print()


if __name__ == "__main__":
    asyncio.run(main())
