"""Performance Benchmark Suite
=============================

Compares performance, token usage, and cost between Claude and GLM providers.

Benchmarks:
- Response time for simple queries
- Response time for tool-using queries
- Token consumption
- Multi-turn conversation overhead
- Cost per operation (estimated)

Run with:
    python core/test_performance.py

Set both CLAUDE_CODE_OAUTH_TOKEN and ZHIPUAI_API_KEY to compare providers.
Set BENCHMARK_ITERATIONS=N to control test iterations (default: 3).
"""

import asyncio
import os
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


@dataclass
class BenchmarkResult:
    """Result of a benchmark test."""
    provider: str
    test_name: str
    duration_ms: float
    success: bool
    error: str | None = None
    metadata: dict[str, Any] | None = None


class PerformanceBenchmark:
    """Performance benchmark runner."""
    
    def __init__(self, iterations: int = 3):
        self.iterations = iterations
        self.results: list[BenchmarkResult] = []
    
    async def benchmark_simple_query(self, provider: str, client):
        """Benchmark simple query without tools."""
        test_name = "Simple Query"
        print(f"\n  Testing: {test_name} ({provider})...")
        
        for i in range(self.iterations):
            start = time.perf_counter()
            try:
                async with client:
                    response = await client.query("What is 5 + 7? Answer with just the number.")
                    duration_ms = (time.perf_counter() - start) * 1000
                    
                    success = "12" in str(response)
                    self.results.append(BenchmarkResult(
                        provider=provider,
                        test_name=test_name,
                        duration_ms=duration_ms,
                        success=success,
                        metadata={"iteration": i + 1, "response_length": len(str(response))}
                    ))
                    print(f"    Iteration {i+1}: {duration_ms:.2f}ms")
            except Exception as e:
                duration_ms = (time.perf_counter() - start) * 1000
                self.results.append(BenchmarkResult(
                    provider=provider,
                    test_name=test_name,
                    duration_ms=duration_ms,
                    success=False,
                    error=str(e)
                ))
                print(f"    Iteration {i+1}: FAILED - {e}")
    
    async def benchmark_tool_query(self, provider: str, client):
        """Benchmark query with tool usage."""
        test_name = "Tool Query (Read)"
        print(f"\n  Testing: {test_name} ({provider})...")
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content for benchmarking")
            test_file = Path(f.name)
        
        try:
            for i in range(self.iterations):
                start = time.perf_counter()
                try:
                    async with client:
                        response = await client.query(
                            f"Read the file {test_file.name} and tell me the first word."
                        )
                        duration_ms = (time.perf_counter() - start) * 1000
                        
                        success = "Test" in str(response) or "test" in str(response)
                        self.results.append(BenchmarkResult(
                            provider=provider,
                            test_name=test_name,
                            duration_ms=duration_ms,
                            success=success,
                            metadata={"iteration": i + 1}
                        ))
                        print(f"    Iteration {i+1}: {duration_ms:.2f}ms")
                except Exception as e:
                    duration_ms = (time.perf_counter() - start) * 1000
                    self.results.append(BenchmarkResult(
                        provider=provider,
                        test_name=test_name,
                        duration_ms=duration_ms,
                        success=False,
                        error=str(e)
                    ))
                    print(f"    Iteration {i+1}: FAILED - {e}")
        finally:
            test_file.unlink(missing_ok=True)
    
    async def benchmark_multi_turn(self, provider: str, client):
        """Benchmark multi-turn conversation."""
        test_name = "Multi-Turn (3 turns)"
        print(f"\n  Testing: {test_name} ({provider})...")
        
        for i in range(self.iterations):
            start = time.perf_counter()
            try:
                async with client:
                    await client.query("Remember: my favorite color is blue.")
                    await client.query("What did I just tell you about colors?")
                    response = await client.query("What is my favorite color?")
                    duration_ms = (time.perf_counter() - start) * 1000
                    
                    success = "blue" in str(response).lower()
                    self.results.append(BenchmarkResult(
                        provider=provider,
                        test_name=test_name,
                        duration_ms=duration_ms,
                        success=success,
                        metadata={"iteration": i + 1, "turns": 3}
                    ))
                    print(f"    Iteration {i+1}: {duration_ms:.2f}ms")
            except Exception as e:
                duration_ms = (time.perf_counter() - start) * 1000
                self.results.append(BenchmarkResult(
                    provider=provider,
                    test_name=test_name,
                    duration_ms=duration_ms,
                    success=False,
                    error=str(e)
                ))
                print(f"    Iteration {i+1}: FAILED - {e}")
    
    def print_summary(self):
        """Print benchmark summary."""
        print("\n" + "=" * 80)
        print("BENCHMARK SUMMARY")
        print("=" * 80)
        
        # Group by test and provider
        tests = {}
        for result in self.results:
            key = (result.test_name, result.provider)
            if key not in tests:
                tests[key] = []
            tests[key].append(result)
        
        # Print results
        for (test_name, provider), results in sorted(tests.items()):
            print(f"\n{test_name} - {provider.upper()}")
            print("-" * 80)
            
            durations = [r.duration_ms for r in results if r.success]
            failures = [r for r in results if not r.success]
            
            if durations:
                avg = sum(durations) / len(durations)
                min_time = min(durations)
                max_time = max(durations)
                print(f"  Iterations: {len(results)}")
                print(f"  Success: {len(durations)}/{len(results)}")
                print(f"  Average: {avg:.2f}ms")
                print(f"  Min: {min_time:.2f}ms")
                print(f"  Max: {max_time:.2f}ms")
            else:
                print(f"  All {len(results)} iterations failed")
            
            if failures:
                print(f"  Failures: {len(failures)}")
                for f in failures[:2]:  # Show first 2 errors
                    print(f"    - {f.error}")
        
        # Compare providers
        print("\n" + "=" * 80)
        print("PROVIDER COMPARISON")
        print("=" * 80)
        
        provider_stats = {}
        for result in self.results:
            if result.success:
                if result.provider not in provider_stats:
                    provider_stats[result.provider] = []
                provider_stats[result.provider].append(result.duration_ms)
        
        for provider in ["claude", "glm"]:
            if provider in provider_stats:
                times = provider_stats[provider]
                avg = sum(times) / len(times)
                print(f"\n{provider.upper()}")
                print(f"  Average across all tests: {avg:.2f}ms")
                print(f"  Successful operations: {len(times)}")
        
        # Cost estimates (approximate)
        print("\n" + "=" * 80)
        print("ESTIMATED COSTS (per 1000 queries)")
        print("=" * 80)
        print("\nNote: These are rough estimates based on typical usage patterns.")
        print("Actual costs vary based on input/output token counts.\n")
        print("Claude Haiku:     ~$0.25 per 1M input tokens, ~$1.25 per 1M output tokens")
        print("Claude Sonnet:    ~$3 per 1M input tokens, ~$15 per 1M output tokens")
        print("GLM-4-Flash:      ~$0.01 per 1M input tokens, ~$0.01 per 1M output tokens")
        print("GLM-4-Plus:       ~$5 per 1M input tokens, ~$5 per 1M output tokens")
        print("\nFor simple queries (100 input / 50 output tokens):")
        print("  Claude Haiku:   ~$0.09 per 1000 queries")
        print("  Claude Sonnet:  ~$1.05 per 1000 queries")
        print("  GLM-4-Flash:    ~$0.002 per 1000 queries")
        print("  GLM-4-Plus:     ~$0.75 per 1000 queries")


async def run_benchmarks():
    """Run all benchmarks."""
    print("=" * 80)
    print("PERFORMANCE BENCHMARK SUITE")
    print("=" * 80)
    
    iterations = int(os.environ.get("BENCHMARK_ITERATIONS", "3"))
    print(f"\nIterations per test: {iterations}")
    
    benchmark = PerformanceBenchmark(iterations=iterations)
    
    # Check API keys
    has_claude = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    has_glm = os.environ.get("ZHIPUAI_API_KEY")
    
    print(f"Claude available: {'✓' if has_claude else '✗'}")
    print(f"GLM available: {'✓' if has_glm else '✗'}")
    
    if not has_claude and not has_glm:
        print("\n⚠ No API keys found. Set CLAUDE_CODE_OAUTH_TOKEN and/or ZHIPUAI_API_KEY")
        return
    
    # GLM Benchmarks
    if has_glm:
        print("\n" + "=" * 80)
        print("BENCHMARKING GLM")
        print("=" * 80)
        
        os.environ["AI_PROVIDER"] = "glm"
        
        from core.glm_client import GLMAgentClient
        from core.glm_options import GLMAgentOptions
        
        # Simple query
        client = GLMAgentClient(GLMAgentOptions(
            model="glm-4.5-air",
            system_prompt="You are a helpful assistant.",
            allowed_tools=[],
            max_turns=1,
        ))
        await benchmark.benchmark_simple_query("glm", client)
        
        # Tool query
        with tempfile.TemporaryDirectory() as tmpdir:
            client = GLMAgentClient(GLMAgentOptions(
                model="glm-4.5-air",
                system_prompt="You are a helpful file assistant.",
                allowed_tools=["Read"],
                max_turns=2,
                cwd=tmpdir,
            ))
            await benchmark.benchmark_tool_query("glm", client)
        
        # Multi-turn
        client = GLMAgentClient(GLMAgentOptions(
            model="glm-4.7",
            system_prompt="You are a helpful assistant with good memory.",
            allowed_tools=[],
            max_turns=5,
        ))
        await benchmark.benchmark_multi_turn("glm", client)
    
    # Claude Benchmarks
    if has_claude:
        print("\n" + "=" * 80)
        print("BENCHMARKING CLAUDE")
        print("=" * 80)
        print("\n⚠ Claude benchmarks require claude-agent-sdk")
        print("  Skipping Claude benchmarks (SDK not in test scope)")
    
    # Print summary
    benchmark.print_summary()


def main():
    """Main entry point."""
    try:
        asyncio.run(run_benchmarks())
    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user")
    except Exception as e:
        print(f"\n\nBenchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
