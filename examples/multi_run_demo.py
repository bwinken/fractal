"""
Multi-Run Tracing Demo

Demonstrates that each run() call creates a separate trace file with unique run_id.
This is essential for FastAPI backends where concurrent requests should not mix traces.

To run:
    python examples/multi_run_demo.py
"""
import os
import asyncio
from pathlib import Path
from fractal.observability import TracingKit

# Ensure traces directory exists
TRACES_DIR = Path(__file__).parent / "traces"
TRACES_DIR.mkdir(exist_ok=True)


def demo_multiple_runs():
    """Simulate 3 separate runs, each creating its own trace file."""
    print("=" * 70)
    print("Multi-Run Tracing Demo")
    print("=" * 70)
    print(f"\nOutput directory: {TRACES_DIR}")

    # Create TracingKit with {run_id} pattern
    kit = TracingKit(
        output_file=str(TRACES_DIR / "demo_{run_id}.jsonl"),
        auto_export=True
    )

    created_files = []

    for i in range(3):
        print(f"\n--- Run {i + 1} ---")

        # Start a new run (generates unique run_id, clears previous events)
        run_id = kit.start_run()
        print(f"  run_id: {run_id}")
        print(f"  output_file: {kit.output_file}")

        # Simulate agent activity
        kit.start_agent(f"Agent{i + 1}", f"Task {i + 1}")
        kit.start_tool_call(f"Agent{i + 1}", "process", {"data": f"item_{i}"})
        kit.end_tool_call(f"Agent{i + 1}", "process", result=f"processed_{i}")
        kit.end_agent(f"Agent{i + 1}", result=f"Completed task {i + 1}")

        # End the run
        kit.end_run()

        created_files.append(kit.output_file)
        print(f"  events: {len(kit.events)}")

    # Show created files
    print("\n" + "=" * 70)
    print("Created Files")
    print("=" * 70)

    for filepath in created_files:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                lines = f.readlines()
            print(f"\n{os.path.basename(filepath)} ({len(lines)} events):")
            for line in lines[:2]:  # Show first 2 events
                import json
                event = json.loads(line)
                print(f"  - {event['event_type']}: {event['agent_name']} (run_id={event['run_id']})")
            if len(lines) > 2:
                print(f"  ... and {len(lines) - 2} more events")

    print("\n" + "=" * 70)
    print("[OK] Each run created a separate trace file!")
    print("=" * 70)

    # List all demo files
    print(f"\nTo view traces:")
    for filepath in created_files:
        basename = os.path.basename(filepath)
        print(f"  fractal view examples/traces/{basename}")


if __name__ == "__main__":
    demo_multiple_runs()
