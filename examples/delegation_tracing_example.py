"""
Delegation-Aware Tracing Example

This example demonstrates how TracingKit automatically tracks complete delegation chains.

Key features:
- Top agent's TracingKit "infects" all delegated agents
- Tracks parent_agent and delegation_depth for each event
- Records delegation start/end events
- Works seamlessly with multi-level delegation (A -> B -> C)
- Uses {run_id} placeholder for per-run trace files (FastAPI-safe)

To run:
    python examples/delegation_tracing_example.py
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
# Example Agents
# ============================================================================

class DataAnalystAgent(BaseAgent):
    """A specialist agent that analyzes data."""

    def __init__(self):
        super().__init__(
            name="DataAnalyst",
            system_prompt="You are a data analyst. Analyze data and provide insights.",
            model="gpt-4o-mini",
            client=AsyncOpenAI(),
            enable_tracing=False  # Will be infected by coordinator's tracing
        )

    @AgentToolkit.register_as_tool
    def analyze_data(self, data: str) -> dict:
        """
        Analyze data.

        Args:
            data (str): Data to analyze

        Returns:
            Analysis results
        """
        import time
        time.sleep(0.1)  # Simulate analysis
        return {
            "data": data,
            "word_count": len(data.split()),
            "char_count": len(data),
            "sentiment": "positive"
        }


class ResearchAgent(BaseAgent):
    """A specialist agent that researches topics."""

    def __init__(self):
        super().__init__(
            name="Researcher",
            system_prompt="You are a researcher. Research topics and provide information.",
            model="gpt-4o-mini",
            client=AsyncOpenAI(),
            enable_tracing=False  # Will be infected by coordinator's tracing
        )

    @AgentToolkit.register_as_tool
    def research_topic(self, topic: str) -> dict:
        """
        Research a topic.

        Args:
            topic (str): Topic to research

        Returns:
            Research results
        """
        import time
        time.sleep(0.1)  # Simulate research
        return {
            "topic": topic,
            "summary": f"Research findings about {topic}",
            "sources": ["source1", "source2"]
        }


class CoordinatorAgent(BaseAgent):
    """A coordinator agent that delegates to specialists."""

    def __init__(self, analyst: DataAnalystAgent, researcher: ResearchAgent, output_dir: str = "examples/traces"):
        super().__init__(
            name="Coordinator",
            system_prompt="You coordinate tasks by delegating to specialist agents.",
            model="gpt-4o-mini",
            client=AsyncOpenAI(),
            enable_tracing=True,  # Only enable tracing at the top level
            # Each run() creates a separate file with unique run_id
            tracing_output_file=f"{output_dir}/delegation_{{run_id}}.jsonl"
        )

        # Register specialists as delegates
        self.register_delegate(
            analyst,
            tool_name="ask_analyst",
            description="Delegate data analysis tasks to the data analyst"
        )
        self.register_delegate(
            researcher,
            tool_name="ask_researcher",
            description="Delegate research tasks to the researcher"
        )


# ============================================================================
# Examples
# ============================================================================

async def example_basic_delegation_tracing():
    """Example 1: Basic delegation tracing."""
    print("=" * 70)
    print("Example 1: Basic Delegation Tracing")
    print("=" * 70)

    # Create agents - only enable tracing on coordinator
    analyst = DataAnalystAgent()
    researcher = ResearchAgent()
    coordinator = CoordinatorAgent(analyst, researcher)

    print(f"\n[Setup]")
    print(f"  Coordinator tracing: {coordinator.tracing is not None}")
    print(f"  Output file pattern: {coordinator.tracing.output_file_pattern}")
    print(f"  Analyst tracing: {analyst.tracing is not None}")
    print(f"  Researcher tracing: {researcher.tracing is not None}")

    # Run coordinator (will delegate to specialists)
    print(f"\n[Running coordinator...]")
    result = await coordinator.run(
        "Please analyze this data and research the topic: AI agents",
        max_iterations=5
    )

    print(f"\n[Completed]")
    print(f"  Success: {result.success}")

    # Show trace
    if coordinator.tracing:
        print("\n" + "-" * 70)
        print("Trace Summary")
        print("-" * 70)

        summary = coordinator.tracing.get_summary()
        print(f"  Total events: {summary['total_events']}")
        print(f"  Agent runs: {summary['agent_runs']}")
        print(f"  Tool calls: {summary['tool_calls']}")
        print(f"  Total time: {summary['total_time']:.3f}s")

        print("\n" + "-" * 70)
        print("Delegation Chain")
        print("-" * 70)

        events = coordinator.tracing.get_trace()

        # Show agent starts with hierarchy
        agent_starts = [e for e in events if e.event_type == 'agent_start']
        for event in agent_starts:
            indent = "  " * event.delegation_depth
            parent_info = f" <- {event.parent_agent}" if event.parent_agent else ""
            print(f"{indent}{event.agent_name} (depth={event.delegation_depth}){parent_info}")

        # Show delegation events
        print("\n" + "-" * 70)
        print("Delegation Events")
        print("-" * 70)

        delegation_events = [
            e for e in events
            if e.event_type in ('agent_delegate', 'delegation_end')
        ]
        for event in delegation_events:
            if event.event_type == 'agent_delegate':
                to_agent = event.arguments.get('to_agent') if event.arguments else 'unknown'
                print(f"  Delegate: {event.agent_name} -> {to_agent}")
            else:
                to_agent = event.metadata.get('to_agent') if event.metadata else 'unknown'
                success = "[OK]" if event.metadata.get('success') else "[ERROR]"
                print(f"  Return: {to_agent} -> {event.agent_name} {success}")

        # Show auto-exported file path (uses {run_id} pattern)
        print(f"\n[OK] Trace auto-exported to: {coordinator.tracing.output_file}")

    print("\n" + "=" * 70)


async def example_multi_level_delegation():
    """Example 2: Multi-level delegation (A -> B -> C)."""
    print("\nExample 2: Multi-Level Delegation (A -> B -> C)")
    print("=" * 70)

    # Create a 3-level hierarchy
    analyst_c = DataAnalystAgent()
    analyst_c.name = "AnalystC"

    researcher_b = ResearchAgent()
    researcher_b.name = "ResearcherB"
    researcher_b.register_delegate(analyst_c, tool_name="ask_analyst")

    coordinator_a = CoordinatorAgent(DataAnalystAgent(), researcher_b)
    coordinator_a.name = "CoordinatorA"

    print(f"\n[Setup]")
    print(f"  Hierarchy: CoordinatorA -> ResearcherB -> AnalystC")
    print(f"  Only CoordinatorA has tracing enabled")

    # Run
    print(f"\n[Running CoordinatorA...]")
    result = await coordinator_a.run(
        "Research AI agents and analyze the data",
        max_iterations=5
    )

    print(f"\n[Completed]")
    print(f"  Success: {result.success}")

    if coordinator_a.tracing:
        print("\n" + "-" * 70)
        print("Multi-Level Delegation Chain")
        print("-" * 70)

        events = coordinator_a.tracing.get_trace()
        agent_starts = [e for e in events if e.event_type == 'agent_start']

        for event in agent_starts:
            indent = "  " * event.delegation_depth
            parent_info = f" <- {event.parent_agent}" if event.parent_agent else ""
            print(f"{indent}{event.agent_name} (depth={event.delegation_depth}){parent_info}")

        # Show max delegation depth
        max_depth = max(e.delegation_depth for e in events)
        print(f"\n[OK] Maximum delegation depth: {max_depth}")

        # Show auto-exported file path
        print(f"[OK] Trace auto-exported to: {coordinator_a.tracing.output_file}")

    print("\n" + "=" * 70)


async def example_analyze_delegation_trace():
    """Example 3: Analyze delegation trace in detail."""
    print("\nExample 3: Analyze Delegation Trace")
    print("=" * 70)

    # Create and run agents
    analyst = DataAnalystAgent()
    researcher = ResearchAgent()
    coordinator = CoordinatorAgent(analyst, researcher)

    print(f"\n[Running analysis task...]")
    await coordinator.run("Analyze: Hello World", max_iterations=5)

    if coordinator.tracing:
        events = coordinator.tracing.get_trace()

        # Group events by delegation depth
        print("\n" + "-" * 70)
        print("Events by Delegation Depth")
        print("-" * 70)

        events_by_depth = {}
        for event in events:
            depth = event.delegation_depth
            if depth not in events_by_depth:
                events_by_depth[depth] = []
            events_by_depth[depth].append(event)

        for depth in sorted(events_by_depth.keys()):
            print(f"\nDepth {depth} ({len(events_by_depth[depth])} events):")
            for event in events_by_depth[depth]:
                event_name = event.tool_name or event.agent_name
                print(f"  - {event.event_type}: {event_name}")

        # Show time analysis
        print("\n" + "-" * 70)
        print("Time Analysis")
        print("-" * 70)

        agent_ends = [e for e in events if e.event_type == 'agent_end' and e.elapsed_time]
        for event in agent_ends:
            indent = "  " * event.delegation_depth
            print(f"{indent}{event.agent_name}: {event.elapsed_time:.3f}s")

        # Show delegation flow
        print("\n" + "-" * 70)
        print("Delegation Flow (Chronological)")
        print("-" * 70)

        for event in events:
            if event.event_type in ('agent_delegate', 'delegation_end', 'agent_start', 'agent_end'):
                timestamp_str = f"{event.timestamp:.2f}"
                indent = "  " * event.delegation_depth

                if event.event_type == 'agent_delegate':
                    to_agent = event.arguments.get('to_agent') if event.arguments else '?'
                    print(f"[{timestamp_str}] {indent}-> Delegate to {to_agent}")
                elif event.event_type == 'delegation_end':
                    print(f"[{timestamp_str}] {indent}← Return from delegation")
                elif event.event_type == 'agent_start':
                    print(f"[{timestamp_str}] {indent}[START] {event.agent_name}")
                elif event.event_type == 'agent_end':
                    print(f"[{timestamp_str}] {indent}[END] {event.agent_name}")

    print("\n" + "=" * 70)


async def main():
    """Run all delegation tracing examples."""
    examples = [
        ("Basic Delegation", example_basic_delegation_tracing),
        ("Multi-Level Delegation", example_multi_level_delegation),
        ("Analyze Trace", example_analyze_delegation_trace),
    ]

    for name, func in examples:
        try:
            await func()
            print(f"\n[OK] {name} example completed\n")
        except Exception as e:
            print(f"\n[ERROR] {name} example failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
