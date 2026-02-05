"""
Delegation Chain Tracing Example
================================

This example demonstrates how tracing automatically propagates through
multi-agent delegation chains to capture the complete execution flow.

OVERVIEW
--------
When a coordinator agent delegates to specialists, you want to trace the
ENTIRE delegation chain, not just the top-level agent. Fractal's TracingKit
solves this with "tracing infection":

1. Enable tracing on the coordinator (top-level agent)
2. When coordinator delegates to a specialist, TracingKit automatically
   "infects" the specialist with the same tracing instance
3. All events from all agents end up in the same trace

KEY FIELDS
----------
Each trace event includes delegation-aware fields:
- parent_agent: Name of the agent that delegated (None for top-level)
- delegation_depth: How deep in the chain (0 = coordinator, 1 = first delegate)
- event_type: Includes 'agent_delegate' and 'delegation_end' events

TRACE STRUCTURE
---------------
For a chain: Coordinator -> Researcher -> Analyst

Events will show:
- agent_start (Coordinator, depth=0)
- agent_delegate (Coordinator -> Researcher)
- agent_start (Researcher, depth=1, parent=Coordinator)
- agent_delegate (Researcher -> Analyst)
- agent_start (Analyst, depth=2, parent=Researcher)
- tool_call (Analyst.analyze, depth=2)
- tool_result (Analyst.analyze, depth=2)
- agent_end (Analyst, depth=2)
- delegation_end (Researcher <- Analyst)
- agent_end (Researcher, depth=1)
- delegation_end (Coordinator <- Researcher)
- agent_end (Coordinator, depth=0)

PER-RUN ISOLATION
-----------------
Use {run_id} placeholder for per-run trace files (essential for FastAPI):

    tracing_output_file="traces/delegation_{run_id}.jsonl"

Each run() creates a separate file with unique run_id.

To run:
    python examples/delegation_tracing_example.py
"""
import os
import asyncio
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
# Specialist Agents (tracing disabled - will be "infected")
# =============================================================================

class AnalystAgent(BaseAgent):
    """Specialist that analyzes data."""

    def __init__(self):
        super().__init__(
            name="Analyst",
            system_prompt="You analyze data.",
            model="gpt-4o-mini",
            client=AsyncOpenAI(),
            enable_tracing=False  # Will inherit tracing from coordinator
        )

    @AgentToolkit.register_as_tool
    def analyze(self, data: str) -> dict:
        """
        Analyze data.

        Args:
            data (str): Data to analyze

        Returns:
            Analysis results
        """
        import time
        time.sleep(0.1)
        return {"data": data, "word_count": len(data.split())}


class ResearcherAgent(BaseAgent):
    """Specialist that researches topics."""

    def __init__(self):
        super().__init__(
            name="Researcher",
            system_prompt="You research topics.",
            model="gpt-4o-mini",
            client=AsyncOpenAI(),
            enable_tracing=False  # Will inherit tracing from coordinator
        )

    @AgentToolkit.register_as_tool
    def research(self, topic: str) -> dict:
        """
        Research a topic.

        Args:
            topic (str): Topic to research

        Returns:
            Research findings
        """
        import time
        time.sleep(0.1)
        return {"topic": topic, "summary": f"Research on {topic}"}


# =============================================================================
# Coordinator Agent (tracing enabled at top level)
# =============================================================================

class CoordinatorAgent(BaseAgent):
    """Coordinator that delegates to specialists."""

    def __init__(self, analyst: BaseAgent, researcher: BaseAgent):
        super().__init__(
            name="Coordinator",
            system_prompt="You coordinate tasks by delegating.",
            model="gpt-4o-mini",
            client=AsyncOpenAI(),
            enable_tracing=True,  # Enable tracing here
            tracing_output_file=str(TRACES_DIR / "delegation_{run_id}.jsonl")
        )

        self.register_delegate(analyst, tool_name="ask_analyst")
        self.register_delegate(researcher, tool_name="ask_researcher")


# =============================================================================
# Main: Demonstrate Delegation Tracing
# =============================================================================

async def main():
    """Run the delegation tracing example."""
    print("=" * 70)
    print("Delegation Chain Tracing Example")
    print("=" * 70)

    # 1. Create agents
    print("\n[1] Create Agents")
    print("-" * 40)
    analyst = AnalystAgent()
    researcher = ResearcherAgent()
    coordinator = CoordinatorAgent(analyst, researcher)

    print(f"  Coordinator: tracing={'enabled' if coordinator.tracing else 'disabled'}")
    print(f"  Analyst: tracing={'enabled' if analyst.tracing else 'disabled'}")
    print(f"  Researcher: tracing={'enabled' if researcher.tracing else 'disabled'}")
    print("\n  Note: Specialists will be 'infected' with coordinator's tracing")

    # 2. Simulate delegation with manual tracing
    print("\n[2] Simulate Delegation Chain")
    print("-" * 40)

    # Start coordinator
    coordinator.tracing.start_run()
    coordinator.tracing.start_agent("Coordinator", "Demo task")

    # Simulate delegation to analyst
    coordinator.tracing.start_delegation("Coordinator", "Analyst", "analyze data")
    coordinator.tracing.start_agent("Analyst", "analyze data")

    # Analyst tool call
    coordinator.tracing.start_tool_call("Analyst", "analyze", {"data": "test"})
    result = analyst.toolkit.execute_tool("analyze", data="test data")
    coordinator.tracing.end_tool_call("Analyst", "analyze", result.content)

    coordinator.tracing.end_agent("Analyst", "analysis complete")
    coordinator.tracing.end_delegation("Coordinator", "Analyst", "done")

    coordinator.tracing.end_agent("Coordinator", "task complete")

    # 3. Show delegation chain
    print("\n[3] Delegation Chain")
    print("-" * 40)
    events = coordinator.tracing.get_trace()
    agent_events = [e for e in events if e.event_type in ('agent_start', 'agent_end')]
    for event in agent_events:
        indent = "  " * event.delegation_depth
        parent = f" (parent={event.parent_agent})" if event.parent_agent else ""
        print(f"  {indent}{event.event_type}: {event.agent_name} depth={event.delegation_depth}{parent}")

    # 4. Show trace summary
    print("\n[4] Trace Summary")
    print("-" * 40)
    summary = coordinator.tracing.get_summary()
    print(f"  Total events: {summary['total_events']}")
    print(f"  Agent runs: {summary['agent_runs']}")
    print(f"  Tool calls: {summary['tool_calls']}")

    # 5. Export trace
    print("\n[5] Export Trace")
    print("-" * 40)
    output_file = coordinator.tracing.output_file
    coordinator.tracing.export_json(output_file)
    print(f"  Exported to: {output_file}")
    print(f"  (Uses {{run_id}} pattern: {coordinator.tracing.output_file_pattern})")

    # 6. Show delegation-aware events
    print("\n[6] Delegation Events")
    print("-" * 40)
    delegation_events = [e for e in events if 'delegat' in e.event_type]
    for event in delegation_events:
        if event.event_type == 'agent_delegate':
            to = event.arguments.get('to_agent') if event.arguments else '?'
            print(f"  {event.agent_name} -> {to}")
        else:
            to = event.metadata.get('to_agent') if event.metadata else '?'
            print(f"  {event.agent_name} <- {to} (returned)")

    print("\n" + "=" * 70)
    print("[OK] Delegation tracing example completed!")
    print("=" * 70)
    print(f"\nView trace: fractal view {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
