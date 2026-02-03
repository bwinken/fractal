"""
Trace Visualization Demo

This example demonstrates the complete workflow:
1. Enable tracing on agents
2. Run agents with delegation
3. Export trace to .jsonl
4. Visualize with both HTML and terminal viewers

To run:
    python examples/visualization_demo.py

Then view the traces:
    # Terminal view
    python -m fractal.observability view examples/traces/visualization_demo.jsonl

    # HTML view
    python -m fractal.observability visualize examples/traces/visualization_demo.jsonl -o examples/visualizations/visualization_demo.html
"""
import os
import asyncio
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

class CalculatorAgent(BaseAgent):
    """Agent that performs calculations."""

    def __init__(self):
        super().__init__(
            name="Calculator",
            system_prompt="You are a calculator agent that performs mathematical operations.",
            model="gpt-4o-mini",
            client=AsyncOpenAI(),
            enable_tracing=False  # Will be infected
        )

    @AgentToolkit.register_as_tool
    def add(self, a: float, b: float) -> float:
        """
        Add two numbers.

        Args:
            a (float): First number
            b (float): Second number

        Returns:
            Sum of the two numbers
        """
        import time
        time.sleep(0.1)  # Simulate processing
        return a + b

    @AgentToolkit.register_as_tool
    def multiply(self, a: float, b: float) -> float:
        """
        Multiply two numbers.

        Args:
            a (float): First number
            b (float): Second number

        Returns:
            Product of the two numbers
        """
        import time
        time.sleep(0.05)
        return a * b


class DataProcessorAgent(BaseAgent):
    """Agent that processes data."""

    def __init__(self):
        super().__init__(
            name="DataProcessor",
            system_prompt="You process and format data.",
            model="gpt-4o-mini",
            client=AsyncOpenAI(),
            enable_tracing=False  # Will be infected
        )

    @AgentToolkit.register_as_tool
    def format_result(self, value: float, decimals: int = 2) -> str:
        """
        Format a number for display.

        Args:
            value (float): Value to format
            decimals (int): Number of decimal places

        Returns:
            Formatted string
        """
        import time
        time.sleep(0.05)
        return f"{value:.{decimals}f}"


class OrchestratorAgent(BaseAgent):
    """Orchestrator agent that coordinates tasks."""

    def __init__(self, calculator: CalculatorAgent, processor: DataProcessorAgent):
        super().__init__(
            name="Orchestrator",
            system_prompt="You orchestrate tasks by delegating to specialist agents.",
            model="gpt-4o-mini",
            client=AsyncOpenAI(),
            enable_tracing=True  # Enable tracing at top level
        )

        # Register delegates
        self.register_delegate(calculator, tool_name="use_calculator")
        self.register_delegate(processor, tool_name="use_processor")


# ============================================================================
# Demo
# ============================================================================

async def main():
    print("=" * 80)
    print("Trace Visualization Demo")
    print("=" * 80)

    # Create agents
    print("\n[1] Creating agents...")
    calculator = CalculatorAgent()
    processor = DataProcessorAgent()
    orchestrator = OrchestratorAgent(calculator, processor)

    print("    - Calculator (with add, multiply tools)")
    print("    - DataProcessor (with format_result tool)")
    print("    - Orchestrator (coordinates both)")
    print("    - Tracing enabled: Orchestrator only")

    # Run orchestrator
    print("\n[2] Running orchestrator with complex task...")
    result = await orchestrator.run(
        "Calculate (5 + 3) * 2, then format the result with 2 decimal places",
        max_iterations=10
    )

    print(f"\n[3] Task completed!")
    print(f"    Success: {result.success}")
    print(f"    Result: {result.content[:100] if result.content else 'N/A'}")

    # Get trace summary
    if orchestrator.tracing:
        summary = orchestrator.tracing.get_summary()
        print(f"\n[4] Trace Summary:")
        print(f"    Total events: {summary['total_events']}")
        print(f"    Agent runs: {summary['agent_runs']}")
        print(f"    Tool calls: {summary['tool_calls']}")
        print(f"    Delegations: {len([e for e in orchestrator.tracing.get_trace() if e.event_type == 'agent_delegate'])}")
        print(f"    Duration: {summary['total_time']:.3f}s")

        # Export trace
        output_file = "examples/traces/visualization_demo.jsonl"
        orchestrator.tracing.export_json(output_file)
        print(f"\n[5] Trace exported to: {output_file}")

        # Show visualization commands
        print("\n" + "=" * 80)
        print("Visualization Commands")
        print("=" * 80)
        print("\n1. Terminal View (quick check):")
        print(f"   python -m fractal.observability view {output_file}")
        print("\n   Options:")
        print(f"   python -m fractal.observability view {output_file} --summary")
        print(f"   python -m fractal.observability view {output_file} --flow")
        print(f"   python -m fractal.observability view {output_file} --compact")

        print("\n2. HTML View (interactive):")
        print(f"   python -m fractal.observability visualize {output_file}")
        print(f"   python -m fractal.observability visualize {output_file} -o examples/visualizations/visualization_demo.html")

        print("\n" + "=" * 80)
        print("\n[OK] Demo completed!")
        print("     Try the visualization commands above to explore the trace!\n")


if __name__ == "__main__":
    asyncio.run(main())
