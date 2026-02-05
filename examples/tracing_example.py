"""
Execution Tracing Example
=========================

This example demonstrates how to enable execution tracing to monitor
agent behavior, tool calls, timing, and errors.

OVERVIEW
--------
TracingKit is Fractal's built-in observability system. It records:

- Agent run start/end with elapsed time
- Tool calls with arguments and results
- Errors and failures
- Complete execution flow

QUICK START
-----------
Enable tracing when creating an agent:

    agent = BaseAgent(
        name="MyAgent",
        enable_tracing=True,                    # Enable tracing
        tracing_output_file="trace.jsonl"       # Optional: export to file
    )

    result = await agent.run("Task")

    # Get trace summary
    summary = agent.tracing.get_summary()
    print(f"Tool calls: {summary['tool_calls']}")

    # Export trace
    agent.tracing.export_json("trace.jsonl")

KEY FEATURES
------------
- Zero external dependencies (pure Python stdlib)
- Low overhead (< 5% performance impact)
- Optional (no overhead when disabled)
- JSON Lines export format
- Works with multi-agent delegation

TRACE EVENTS
------------
Each event in the trace includes:
- timestamp: When the event occurred
- event_type: agent_start, agent_end, tool_call, tool_result, error
- agent_name: Which agent generated the event
- tool_name: Which tool was called (if applicable)
- arguments: Tool arguments
- result: Tool/agent result
- elapsed_time: Duration in seconds

VISUALIZATION
-------------
After exporting a trace, visualize it:

    # Terminal view
    fractal view trace.jsonl

    # HTML visualization
    fractal visualize trace.jsonl -o output.html

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

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Set dummy key for testing (remove if using real API)
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-key")

# Ensure traces directory exists
TRACES_DIR = Path(__file__).parent / "traces"
TRACES_DIR.mkdir(exist_ok=True)


# =============================================================================
# Example Agent with Tracing
# =============================================================================

class DataAgent(BaseAgent):
    """Agent with tools that simulate data processing."""

    def __init__(self, enable_tracing=False, output_file=None):
        super().__init__(
            name="DataAgent",
            system_prompt="You process and analyze data.",
            model="gpt-4o-mini",
            client=AsyncOpenAI(),
            enable_tracing=enable_tracing,
            tracing_output_file=output_file
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
        return {"original": data, "processed": data.upper(), "length": len(data)}

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
        return {"data": data, "word_count": len(data.split()), "char_count": len(data)}


# =============================================================================
# Main: Demonstrate Tracing
# =============================================================================

async def main():
    """Run the tracing example."""
    print("=" * 70)
    print("Execution Tracing Example")
    print("=" * 70)

    output_file = str(TRACES_DIR / "tracing_example.jsonl")

    # 1. Create agent with tracing enabled
    print("\n[1] Create Agent with Tracing")
    print("-" * 40)
    agent = DataAgent(enable_tracing=True, output_file=output_file)

    print(f"  Agent: {agent.name}")
    print(f"  Tracing: {'enabled' if agent.tracing else 'disabled'}")
    print(f"  Output: {output_file}")

    # 2. Run agent (direct tool calls for demo)
    print("\n[2] Execute Tools")
    print("-" * 40)

    # Start the run (required to initialize tracing state)
    agent.tracing.start_run()
    agent.tracing.start_agent(agent.name, "Demo task")

    # Execute tools directly
    result1 = agent.toolkit.execute_tool("process_data", data="Hello World")
    print(f"  process_data('Hello World'):")
    print(f"    -> {result1.content}")

    result2 = agent.toolkit.execute_tool("analyze_data", data="The quick brown fox")
    print(f"  analyze_data('The quick brown fox'):")
    print(f"    -> {result2.content}")

    agent.tracing.end_agent(agent.name, result="Demo completed")

    # 3. Get trace summary
    print("\n[3] Trace Summary")
    print("-" * 40)
    summary = agent.tracing.get_summary()
    print(f"  Total events: {summary['total_events']}")
    print(f"  Agent runs: {summary['agent_runs']}")
    print(f"  Tool calls: {summary['tool_calls']}")
    print(f"  Errors: {summary['errors']}")
    print(f"  Total time: {summary['total_time']:.3f}s")

    # 4. Show trace events
    print("\n[4] Trace Events")
    print("-" * 40)
    events = agent.tracing.get_trace()
    for i, event in enumerate(events, 1):
        print(f"\n  Event {i}: {event.event_type.upper()}")
        print(f"    Agent: {event.agent_name}")
        if event.tool_name:
            print(f"    Tool: {event.tool_name}")
        if event.elapsed_time is not None:
            print(f"    Elapsed: {event.elapsed_time:.3f}s")

    # 5. Export trace
    print("\n[5] Export Trace")
    print("-" * 40)
    agent.tracing.export_json(output_file)
    print(f"  Exported to: {output_file}")

    # Show exported content
    with open(output_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    print(f"  File contains {len(lines)} events")
    print(f"\n  First event:")
    first_event = json.loads(lines[0])
    print(f"    {json.dumps(first_event, indent=4)[:200]}...")

    # 6. Show visualization commands
    print("\n[6] Visualization Commands")
    print("-" * 40)
    print(f"  Terminal: fractal view {output_file}")
    print(f"  HTML:     fractal visualize {output_file} -o output.html")

    print("\n" + "=" * 70)
    print("[OK] Tracing example completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
