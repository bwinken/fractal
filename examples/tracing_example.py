"""
Tracing Example

This example demonstrates how to use TracingKit to monitor agent execution.

TracingKit records:
- Agent run start/end with elapsed time
- Tool calls with arguments and results
- Errors and failures
- Complete execution flow

To run:
    python examples/tracing_example.py
"""
import os
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
from fractal import BaseAgent, AgentToolkit

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Set dummy key for testing
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "sk-test-dummy-key"


# ============================================================================
# Example Agent with Tracing
# ============================================================================

class DataAgent(BaseAgent):
    """Agent that processes data with tracing enabled."""

    def __init__(self, enable_tracing=False, tracing_output=None):
        super().__init__(
            name="DataAgent",
            system_prompt="You process and analyze data.",
            model="gpt-4o-mini",
            client=AsyncOpenAI(),
            enable_tracing=enable_tracing,  # Enable tracing
            tracing_output_file=tracing_output  # Optional: auto-export to file
        )

    @AgentToolkit.register_as_tool
    def process_data(self, data: str) -> dict:
        """
        Process input data.

        Args:
            data (str): Data to process

        Returns:
            Processed result
        """
        import time
        time.sleep(0.1)  # Simulate processing
        return {
            "original": data,
            "processed": data.upper(),
            "length": len(data)
        }

    @AgentToolkit.register_as_tool
    def analyze_data(self, data: str) -> dict:
        """
        Analyze input data.

        Args:
            data (str): Data to analyze

        Returns:
            Analysis results
        """
        import time
        time.sleep(0.05)  # Simulate analysis
        return {
            "data": data,
            "word_count": len(data.split()),
            "char_count": len(data)
        }


# ============================================================================
# Examples
# ============================================================================

async def example_basic_tracing():
    """Example 1: Basic tracing without file output."""
    print("=" * 70)
    print("Example 1: Basic Tracing")
    print("=" * 70)

    # Create agent with tracing enabled
    agent = DataAgent(enable_tracing=True)

    print(f"\nAgent: {agent.name}")
    print(f"Tracing enabled: {agent.tracing is not None}")

    # Run agent
    print("\n[Running agent...]")
    result = await agent.run(
        "Process this data: Hello World",
        max_iterations=5
    )

    print(f"\nAgent completed:")
    print(f"  Success: {result.success}")
    print(f"  Content: {result.content[:100]}...")

    # Get trace
    if agent.tracing:
        print("\n" + "-" * 70)
        print("Trace Summary:")
        print("-" * 70)
        summary = agent.tracing.get_summary()
        print(f"  Total events: {summary['total_events']}")
        print(f"  Agent runs: {summary['agent_runs']}")
        print(f"  Tool calls: {summary['tool_calls']}")
        print(f"  Errors: {summary['errors']}")
        print(f"  Total time: {summary['total_time']:.3f}s")
        if summary['tool_calls'] > 0:
            print(f"  Avg tool time: {summary['average_tool_time']:.3f}s")

        print("\n" + "-" * 70)
        print("Trace Events:")
        print("-" * 70)
        for i, event in enumerate(agent.tracing.get_trace(), 1):
            print(f"\n{i}. {event.event_type.upper()}")
            print(f"   Agent: {event.agent_name}")
            if event.tool_name:
                print(f"   Tool: {event.tool_name}")
            if event.arguments:
                args_str = json.dumps(event.arguments, ensure_ascii=False)[:100]
                print(f"   Arguments: {args_str}")
            if event.result:
                result_str = str(event.result)[:100]
                print(f"   Result: {result_str}")
            if event.elapsed_time is not None:
                print(f"   Elapsed: {event.elapsed_time:.3f}s")
            if event.error:
                print(f"   Error: {event.error}")

    print("\n" + "=" * 70)


async def example_tracing_with_file_output():
    """Example 2: Tracing with automatic file export."""
    print("\nExample 2: Tracing with File Output")
    print("=" * 70)

    output_file = "examples/traces/tracing_example.jsonl"

    # Create agent with file output
    agent = DataAgent(
        enable_tracing=True,
        tracing_output=output_file
    )

    print(f"\nAgent: {agent.name}")
    print(f"Trace output: {output_file}")

    # Run agent
    print("\n[Running agent...]")
    result = await agent.run(
        "Analyze this text: The quick brown fox jumps over the lazy dog",
        max_iterations=5
    )

    print(f"\nAgent completed:")
    print(f"  Success: {result.success}")

    # Export trace
    if agent.tracing:
        summary = agent.tracing.get_summary()
        print(f"\nTrace summary:")
        print(f"  Events: {summary['total_events']}")
        print(f"  Tool calls: {summary['tool_calls']}")
        print(f"  Time: {summary['total_time']:.3f}s")

        # Note: Events are NOT auto-exported in current implementation
        # You need to manually export
        agent.tracing.export_json(output_file)
        print(f"\nTrace exported to: {output_file}")

        # Read and display first few lines
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:3]
            print(f"\nFirst {len(lines)} events:")
            for line in lines:
                event_data = json.loads(line)
                print(f"  - {event_data['event_type']}: {event_data.get('tool_name', event_data['agent_name'])}")
        except Exception as e:
            print(f"Could not read trace file: {e}")

    print("\n" + "=" * 70)


async def example_tracing_without_enabling():
    """Example 3: Agent without tracing (no overhead)."""
    print("\nExample 3: Without Tracing (No Overhead)")
    print("=" * 70)

    # Create agent WITHOUT tracing
    agent = DataAgent(enable_tracing=False)

    print(f"\nAgent: {agent.name}")
    print(f"Tracing enabled: {agent.tracing is not None}")

    # Run agent
    print("\n[Running agent...]")
    result = await agent.run(
        "Process data without tracing",
        max_iterations=3
    )

    print(f"\nAgent completed:")
    print(f"  Success: {result.success}")
    print(f"  No tracing overhead!")

    print("\n" + "=" * 70)


async def example_compare_tracing_vs_no_tracing():
    """Example 4: Compare performance with and without tracing."""
    print("\nExample 4: Performance Comparison")
    print("=" * 70)

    import time

    # Without tracing
    agent_no_trace = DataAgent(enable_tracing=False)
    start = time.time()
    await agent_no_trace.run("Test", max_iterations=3)
    time_no_trace = time.time() - start

    # With tracing
    agent_with_trace = DataAgent(enable_tracing=True)
    start = time.time()
    await agent_with_trace.run("Test", max_iterations=3)
    time_with_trace = time.time() - start

    print(f"\nPerformance:")
    print(f"  Without tracing: {time_no_trace:.3f}s")
    print(f"  With tracing: {time_with_trace:.3f}s")
    print(f"  Overhead: {(time_with_trace - time_no_trace):.3f}s ({((time_with_trace/time_no_trace - 1) * 100):.1f}%)")

    print("\n" + "=" * 70)


async def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("TracingKit Examples")
    print("=" * 70 + "\n")

    examples = [
        ("Basic Tracing", example_basic_tracing),
        ("File Output", example_tracing_with_file_output),
        ("Without Tracing", example_tracing_without_enabling),
        ("Performance", example_compare_tracing_vs_no_tracing),
    ]

    for name, func in examples:
        try:
            await func()
            print(f"\n[OK] {name} completed\n")
        except Exception as e:
            print(f"\n[ERROR] {name}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
