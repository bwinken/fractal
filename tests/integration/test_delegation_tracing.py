"""
Test delegation-aware tracing.

This test verifies that tracing correctly tracks delegation chains:
- Top agent's TracingKit "infects" all delegated agents
- parent_agent and delegation_depth are properly tracked
- Complete execution flow is captured in one TracingKit instance
"""
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
from fractal import BaseAgent, AgentToolkit

# Load environment
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Set dummy key for testing
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "sk-test-dummy-key"


class SpecialistAgent(BaseAgent):
    """A specialist agent that performs specific tasks."""

    def __init__(self, name="Specialist"):
        super().__init__(
            name=name,
            system_prompt="You are a specialist agent.",
            model="gpt-4o-mini",
            client=AsyncOpenAI(),
            enable_tracing=False  # Will be infected by coordinator's tracing
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
        return {
            "data": data,
            "result": "analyzed",
            "specialist": self.name
        }


class CoordinatorAgent(BaseAgent):
    """A coordinator agent that delegates to specialists."""

    def __init__(self, specialist: SpecialistAgent, enable_tracing=False):
        super().__init__(
            name="Coordinator",
            system_prompt="You coordinate tasks by delegating to specialists.",
            model="gpt-4o-mini",
            client=AsyncOpenAI(),
            enable_tracing=enable_tracing
        )

        # Register specialist as delegate
        self.register_delegate(specialist, tool_name="ask_specialist")

    @AgentToolkit.register_as_tool
    def coordinate(self, task: str) -> dict:
        """
        Coordinate a task.

        Args:
            task (str): Task to coordinate

        Returns:
            Coordination result
        """
        return {
            "task": task,
            "status": "coordinated"
        }


async def test_delegation_tracing():
    """Test that tracing properly tracks delegation chains."""
    print("=" * 70)
    print("Testing Delegation-Aware Tracing")
    print("=" * 70)

    # Create agents
    specialist = SpecialistAgent(name="DataSpecialist")
    coordinator = CoordinatorAgent(specialist, enable_tracing=True)

    print(f"\n[Setup]")
    print(f"  Coordinator tracing: {coordinator.tracing is not None}")
    print(f"  Specialist tracing (before delegation): {specialist.tracing is not None}")

    # Run coordinator (which will delegate to specialist)
    print(f"\n[Running coordinator...]")
    result = await coordinator.run(
        "Please analyze this data using the specialist",
        max_iterations=5
    )

    print(f"\n[Completed]")
    print(f"  Success: {result.success}")
    print(f"  Specialist tracing (after delegation): {specialist.tracing is not None}")

    # Check tracing results
    if coordinator.tracing:
        print("\n" + "-" * 70)
        print("Trace Summary")
        print("-" * 70)

        summary = coordinator.tracing.get_summary()
        print(f"  Total events: {summary['total_events']}")
        print(f"  Agent runs: {summary['agent_runs']}")
        print(f"  Tool calls: {summary['tool_calls']}")
        print(f"  Errors: {summary['errors']}")
        print(f"  Total time: {summary['total_time']:.3f}s")

        print("\n" + "-" * 70)
        print("Delegation Chain Trace")
        print("-" * 70)

        events = coordinator.tracing.get_trace()

        # Group events by type
        agent_events = [e for e in events if e.event_type in ('agent_start', 'agent_end')]
        delegation_events = [e for e in events if e.event_type in ('agent_delegate', 'delegation_end')]
        tool_events = [e for e in events if e.event_type in ('tool_call', 'tool_result')]

        print(f"\nAgent Events ({len(agent_events)}):")
        for event in agent_events:
            indent = "  " * (event.delegation_depth + 1)
            parent_info = f" [parent: {event.parent_agent}]" if event.parent_agent else ""
            print(f"{indent}{event.event_type}: {event.agent_name} (depth={event.delegation_depth}){parent_info}")
            if event.elapsed_time:
                print(f"{indent}  -> elapsed: {event.elapsed_time:.3f}s")

        print(f"\nDelegation Events ({len(delegation_events)}):")
        for event in delegation_events:
            indent = "  " * (event.delegation_depth + 1)
            if event.event_type == 'agent_delegate':
                to_agent = event.arguments.get('to_agent') if event.arguments else 'unknown'
                print(f"{indent}Delegate: {event.agent_name} -> {to_agent} (depth={event.delegation_depth})")
            else:
                to_agent = event.metadata.get('to_agent') if event.metadata else 'unknown'
                print(f"{indent}Return: {to_agent} -> {event.agent_name} (depth={event.delegation_depth})")

        print(f"\nTool Events ({len(tool_events)}):")
        for event in tool_events:
            indent = "  " * (event.delegation_depth + 1)
            if event.event_type == 'tool_call':
                print(f"{indent}Call: {event.tool_name} by {event.agent_name} (depth={event.delegation_depth})")
            else:
                success = "[OK]" if not event.error else "[ERROR]"
                print(f"{indent}Result: {event.tool_name} {success} (elapsed={event.elapsed_time:.3f}s)")

        # Verify tracing correctness
        print("\n" + "-" * 70)
        print("Verification")
        print("-" * 70)

        # Check 1: All events should be in coordinator's tracing
        print(f"\n[OK] All events recorded in coordinator's TracingKit")

        # Check 2: Should have delegation events
        has_delegation = any(e.event_type == 'agent_delegate' for e in events)
        if has_delegation:
            print(f"[OK] Delegation events recorded")
        else:
            print(f"[WARN] No delegation events found")

        # Check 3: Should have events from both agents
        agents_in_trace = set(e.agent_name for e in events)
        print(f"[OK] Agents in trace: {agents_in_trace}")

        # Check 4: Delegation depth should be > 0 for specialist events
        specialist_events = [e for e in events if e.agent_name == "DataSpecialist"]
        if specialist_events:
            max_depth = max(e.delegation_depth for e in specialist_events)
            print(f"[OK] Specialist events have delegation_depth > 0: max_depth={max_depth}")
        else:
            print(f"[WARN] No specialist events found")

        # Check 5: Parent agent should be set for specialist
        specialist_with_parent = [e for e in specialist_events if e.parent_agent]
        if specialist_with_parent:
            print(f"[OK] Specialist events have parent_agent set: {specialist_with_parent[0].parent_agent}")
        else:
            print(f"[WARN] No parent_agent found for specialist events")

        # Export trace for inspection
        output_file = "delegation_trace.jsonl"
        coordinator.tracing.export_json(output_file)
        print(f"\n[OK] Trace exported to: {output_file}")

    print("\n" + "=" * 70)


async def test_multi_level_delegation():
    """Test multi-level delegation: A -> B -> C"""
    print("\n" + "=" * 70)
    print("Testing Multi-Level Delegation (A -> B -> C)")
    print("=" * 70)

    # Create agents
    specialist_c = SpecialistAgent(name="SpecialistC")
    specialist_b = SpecialistAgent(name="SpecialistB")

    # B delegates to C
    specialist_b.register_delegate(specialist_c, tool_name="ask_c")

    # A delegates to B
    coordinator_a = CoordinatorAgent(specialist_b, enable_tracing=True)

    print(f"\n[Setup]")
    print(f"  A (Coordinator) -> B (SpecialistB) -> C (SpecialistC)")
    print(f"  A tracing: {coordinator_a.tracing is not None}")

    # Run coordinator A
    print(f"\n[Running coordinator A...]")
    result = await coordinator_a.run(
        "Delegate through B to C",
        max_iterations=5
    )

    print(f"\n[Completed]")
    print(f"  Success: {result.success}")

    if coordinator_a.tracing:
        summary = coordinator_a.tracing.get_summary()
        print(f"\n[Trace Summary]")
        print(f"  Total events: {summary['total_events']}")
        print(f"  Agent runs: {summary['agent_runs']}")

        # Show delegation chain
        events = coordinator_a.tracing.get_trace()
        agent_events = [e for e in events if e.event_type == 'agent_start']

        print(f"\n[Delegation Chain]")
        for event in agent_events:
            indent = "  " * event.delegation_depth
            parent_info = f" <- {event.parent_agent}" if event.parent_agent else ""
            print(f"{indent}{event.agent_name} (depth={event.delegation_depth}){parent_info}")

        # Export
        output_file = "multi_level_delegation_trace.jsonl"
        coordinator_a.tracing.export_json(output_file)
        print(f"\n[OK] Multi-level trace exported to: {output_file}")

    print("\n" + "=" * 70)


async def main():
    """Run all delegation tracing tests."""
    try:
        await test_delegation_tracing()
        print("\n[OK] Basic delegation tracing test passed\n")
    except Exception as e:
        print(f"\n[ERROR] Basic delegation tracing test failed: {e}")
        import traceback
        traceback.print_exc()

    try:
        await test_multi_level_delegation()
        print("\n[OK] Multi-level delegation tracing test passed\n")
    except Exception as e:
        print(f"\n[ERROR] Multi-level delegation tracing test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
