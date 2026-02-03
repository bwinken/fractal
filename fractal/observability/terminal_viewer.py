"""
Trace Viewer - Terminal ASCII Visualization

View agent trace files in the terminal with ASCII art.
Zero dependencies - pure Python stdlib.

Usage:
    python -m fractal.observability view trace.jsonl
    python -m fractal.observability view trace.jsonl --compact
"""
import json
import sys
import argparse
from typing import List, Dict, Any
from pathlib import Path


def load_trace(filepath: str) -> List[Dict[str, Any]]:
    """Load trace events from .jsonl file."""
    events = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    return events


def get_event_icon(event_type: str) -> str:
    """Get icon for event type."""
    icons = {
        'agent_start': '[>]',
        'agent_end': '[<]',
        'agent_delegate': '[>>]',
        'delegation_end': '[<<]',
        'tool_call': '[T]',
        'tool_result': '[R]',
        'error': '[X]',
    }
    return icons.get(event_type, '[?]')


def format_time(seconds: float) -> str:
    """Format time in seconds."""
    if seconds < 0.001:
        return f"{seconds*1000:.1f}us"
    elif seconds < 1:
        return f"{seconds*1000:.1f}ms"
    else:
        return f"{seconds:.3f}s"


def render_timeline(events: List[Dict[str, Any]], compact: bool = False):
    """Render timeline view in terminal."""
    print("=" * 80)
    print("TRACE TIMELINE")
    print("=" * 80)

    if not events:
        print("No events to display")
        return

    start_time = events[0]['timestamp']

    for i, event in enumerate(events):
        rel_time = event['timestamp'] - start_time
        depth = event.get('delegation_depth', 0)
        indent = "  " * depth

        # Event icon and type
        icon = get_event_icon(event['event_type'])
        event_type = event['event_type'].replace('_', ' ').upper()

        # Time info
        time_str = f"+{format_time(rel_time)}"

        # Event description
        agent = event['agent_name']
        desc = ""

        if event['event_type'] == 'agent_start':
            desc = f"{agent} STARTED"
        elif event['event_type'] == 'agent_end':
            elapsed = event.get('elapsed_time')
            desc = f"{agent} ENDED"
            if elapsed:
                desc += f" (took {format_time(elapsed)})"
        elif event['event_type'] == 'agent_delegate':
            to_agent = event.get('arguments', {}).get('to_agent', '?')
            desc = f"{agent} -> {to_agent}"
        elif event['event_type'] == 'delegation_end':
            to_agent = event.get('metadata', {}).get('to_agent', '?')
            desc = f"{to_agent} -> {agent}"
        elif event['event_type'] == 'tool_call':
            tool = event.get('tool_name', '?')
            desc = f"{agent} calls {tool}"
        elif event['event_type'] == 'tool_result':
            tool = event.get('tool_name', '?')
            elapsed = event.get('elapsed_time')
            desc = f"{tool} returned"
            if elapsed:
                desc += f" ({format_time(elapsed)})"
            if event.get('error'):
                desc += " [ERROR]"
        elif event['event_type'] == 'error':
            desc = f"{agent} ERROR: {event.get('error', '?')}"

        # Print line
        if compact:
            print(f"{time_str:>12} {indent}{icon} {desc}")
        else:
            print(f"\n[{i+1}] {time_str}")
            print(f"{indent}{icon} {event_type}")
            print(f"{indent}    {desc}")

            # Show parent if available
            if event.get('parent_agent'):
                print(f"{indent}    Parent: {event['parent_agent']}")

    print("\n" + "=" * 80)


def render_hierarchy(events: List[Dict[str, Any]]):
    """Render delegation hierarchy."""
    print("=" * 80)
    print("DELEGATION HIERARCHY")
    print("=" * 80)

    # Get unique agent starts
    agent_starts = [e for e in events if e['event_type'] == 'agent_start']

    if not agent_starts:
        print("No agents found")
        return

    for event in agent_starts:
        depth = event.get('delegation_depth', 0)
        indent = "  " * depth
        agent = event['agent_name']
        parent = event.get('parent_agent')

        if parent:
            print(f"{indent}|- {agent} (parent: {parent}, depth: {depth})")
        else:
            print(f"{indent}|- {agent} (depth: {depth})")

    print("=" * 80)


def render_summary(events: List[Dict[str, Any]]):
    """Render trace summary."""
    if not events:
        return

    # Calculate statistics
    agents = set()
    tool_calls = 0
    delegations = 0
    errors = 0

    for event in events:
        agents.add(event['agent_name'])
        if event['event_type'] == 'tool_call':
            tool_calls += 1
        elif event['event_type'] == 'agent_delegate':
            delegations += 1
        elif event['event_type'] == 'error':
            errors += 1

    duration = events[-1]['timestamp'] - events[0]['timestamp']

    print("=" * 80)
    print("TRACE SUMMARY")
    print("=" * 80)
    print(f"Total Events:    {len(events)}")
    print(f"Agents:          {len(agents)}")
    print(f"Tool Calls:      {tool_calls}")
    print(f"Delegations:     {delegations}")
    print(f"Errors:          {errors}")
    print(f"Duration:        {format_time(duration)}")
    print(f"\nAgents: {', '.join(sorted(agents))}")
    print("=" * 80)


def render_flow_chart(events: List[Dict[str, Any]]):
    """Render a simplified flow chart."""
    print("=" * 80)
    print("EXECUTION FLOW")
    print("=" * 80)

    if not events:
        print("No events to display")
        return

    current_depth = 0

    for event in events:
        depth = event.get('delegation_depth', 0)
        event_type = event['event_type']

        # Only show key events
        if event_type not in ['agent_start', 'agent_end', 'agent_delegate', 'delegation_end']:
            continue

        indent = "  " * depth

        if event_type == 'agent_start':
            print(f"{indent}+-- START: {event['agent_name']}")
        elif event_type == 'agent_end':
            elapsed = event.get('elapsed_time')
            elapsed_str = f" ({format_time(elapsed)})" if elapsed else ""
            print(f"{indent}+-- END: {event['agent_name']}{elapsed_str}")
        elif event_type == 'agent_delegate':
            to_agent = event.get('arguments', {}).get('to_agent', '?')
            print(f"{indent}+--> DELEGATE TO: {to_agent}")
        elif event_type == 'delegation_end':
            print(f"{indent}+<-- RETURN")

    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description='View agent trace files in terminal (ASCII visualization)'
    )
    parser.add_argument(
        'input',
        help='Input trace file (.jsonl)'
    )
    parser.add_argument(
        '--compact', '-c',
        action='store_true',
        help='Compact timeline view'
    )
    parser.add_argument(
        '--hierarchy', '-H',
        action='store_true',
        help='Show only hierarchy view'
    )
    parser.add_argument(
        '--flow', '-f',
        action='store_true',
        help='Show only flow chart view'
    )
    parser.add_argument(
        '--summary', '-s',
        action='store_true',
        help='Show only summary'
    )

    args = parser.parse_args()

    # Check input file exists
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    # Load trace events
    print(f"\nLoading trace from: {args.input}\n")
    events = load_trace(args.input)

    if not events:
        print("Error: No events found in trace file")
        sys.exit(1)

    # Render based on options
    if args.summary:
        render_summary(events)
    elif args.hierarchy:
        render_hierarchy(events)
    elif args.flow:
        render_flow_chart(events)
    else:
        # Default: show everything
        render_summary(events)
        print()
        render_hierarchy(events)
        print()
        render_flow_chart(events)
        print()
        render_timeline(events, compact=args.compact)


if __name__ == '__main__':
    main()
