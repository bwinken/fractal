"""
Tracing and observability toolkit for monitoring agent execution.
"""
import time
import json
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime


@dataclass
class TraceEvent:
    """
    A single trace event in the agent execution flow.

    Attributes:
        timestamp: Unix timestamp when the event occurred
        event_type: Type of event (agent_start, agent_end, agent_delegate, tool_call, tool_result, error)
        agent_name: Name of the agent
        run_id: Unique identifier for this run (groups events from one run() call)
        parent_agent: Name of the parent agent (for delegated agents)
        delegation_depth: Depth in the delegation chain (0 = top agent)
        tool_name: Name of the tool (for tool-related events)
        tool_call_id: Unique ID for this tool call (for matching start/end in parallel execution)
        parallel_group_id: Groups tool calls that execute in parallel (same group = same batch)
        arguments: Arguments passed to the tool
        result: Result from the tool or agent
        error: Error message if an error occurred
        elapsed_time: Time taken for the operation (in seconds)
        metadata: Additional metadata
    """
    timestamp: float
    event_type: str
    agent_name: str
    run_id: Optional[str] = None
    parent_agent: Optional[str] = None
    delegation_depth: int = 0
    tool_name: Optional[str] = None
    tool_call_id: Optional[str] = None
    parallel_group_id: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    elapsed_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary, handling non-serializable types."""
        data = asdict(self)

        # Convert result to string if it's not JSON serializable
        if data['result'] is not None:
            try:
                json.dumps(data['result'])
            except (TypeError, ValueError):
                data['result'] = str(data['result'])

        return data

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class TracingKit:
    """
    Toolkit for tracing and monitoring agent execution.

    Records agent actions including:
    - Agent run start/end
    - Tool calls with arguments
    - Tool results and errors
    - Elapsed time for each operation

    Example::

        # Enable tracing for an agent
        agent = MyAgent(enable_tracing=True)

        # Run the agent
        result = await agent.run("task")

        # Get trace events
        trace = agent.tracing.get_trace()

        # Export to JSON file
        agent.tracing.export_json("trace.jsonl")
    """

    def __init__(self, output_file: Optional[str] = None, auto_export: bool = True):
        """
        Initialize the tracing toolkit.

        Args:
            output_file: Optional file path pattern for trace output. Supports placeholders:
                - ``{run_id}`` — unique ID for this run (e.g., ``trace_{run_id}.jsonl``)
                - ``{timestamp}`` — ISO timestamp (e.g., ``trace_{timestamp}.jsonl``)
                If the pattern contains ``{run_id}`` or ``{timestamp}``, a new file is
                created for each ``run()`` call. Otherwise, all runs append to the same file.
            auto_export: If True (default), export each event immediately to file.
        """
        self.events: List[TraceEvent] = []
        self.output_file_pattern = output_file
        self.output_file: Optional[str] = None  # Resolved path for current run
        self.auto_export = auto_export
        self._operation_stack: List[Dict[str, Any]] = []  # Stack for tracking nested operations
        self._delegation_depth: int = 0  # Track delegation depth
        self._current_parent: Optional[str] = None  # Track current parent agent
        self._run_id: Optional[str] = None  # Current run ID
        # Dict-based tracking for parallel tool calls (keyed by tool_call_id)
        self._tool_start_times: Dict[str, float] = {}

    def _add_event(self, event: TraceEvent):
        """Add an event and optionally export it."""
        # Attach current run_id to event
        event.run_id = self._run_id
        self.events.append(event)

        if self.auto_export and self.output_file:
            self._export_event(event)

    def start_run(self, run_id: Optional[str] = None) -> str:
        """
        Start a new trace run. Call this before ``start_agent()``.

        Clears previous events, generates a new run_id, and resolves the output file path.

        Args:
            run_id: Optional custom run ID. If None, a UUID is generated.

        Returns:
            The run_id for this run.
        """
        # Clear state from previous run
        self.events.clear()
        self._operation_stack.clear()
        self._tool_start_times.clear()
        self._delegation_depth = 0
        self._current_parent = None

        # Generate or use provided run_id
        self._run_id = run_id or uuid.uuid4().hex[:12]

        # Resolve output file path from pattern
        if self.output_file_pattern:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_file = (
                self.output_file_pattern
                .replace("{run_id}", self._run_id)
                .replace("{timestamp}", ts)
            )
        else:
            self.output_file = None

        return self._run_id

    def end_run(self):
        """
        End the current trace run.

        Finalizes the trace. The events remain available via ``get_trace()`` until
        the next ``start_run()`` call.
        """
        self._run_id = None

    @property
    def run_id(self) -> Optional[str]:
        """Current run ID, or None if no run is active."""
        return self._run_id

    def _export_event(self, event: TraceEvent):
        """Export a single event to file (JSON Lines format)."""
        try:
            with open(self.output_file, 'a', encoding='utf-8') as f:
                f.write(event.to_json() + '\n')
        except Exception as e:
            # Don't let tracing errors break the agent
            print(f"Warning: Failed to export trace event: {e}")

    def start_agent(self, agent_name: str, user_input: Any, metadata: Optional[Dict] = None):
        """
        Record agent run start.

        Args:
            agent_name: Name of the agent
            user_input: Input provided to the agent
            metadata: Optional metadata
        """
        start_time = time.time()

        # Push to stack
        self._operation_stack.append({
            'type': 'agent',
            'name': agent_name,
            'start_time': start_time
        })

        event = TraceEvent(
            timestamp=start_time,
            event_type='agent_start',
            agent_name=agent_name,
            parent_agent=self._current_parent,
            delegation_depth=self._delegation_depth,
            arguments={'user_input': str(user_input)[:200]},  # Truncate for readability
            metadata=metadata or {}
        )
        self._add_event(event)

    def end_agent(self, agent_name: str, result: Any, success: bool = True, metadata: Optional[Dict] = None):
        """
        Record agent run end.

        Args:
            agent_name: Name of the agent
            result: Result from the agent
            success: Whether the agent run was successful
            metadata: Optional metadata
        """
        end_time = time.time()

        # Pop from stack and calculate elapsed time
        elapsed = None
        if self._operation_stack and self._operation_stack[-1]['type'] == 'agent':
            op = self._operation_stack.pop()
            elapsed = end_time - op['start_time']

        # Truncate result for readability
        result_str = str(result)[:200] if result else None

        event = TraceEvent(
            timestamp=end_time,
            event_type='agent_end',
            agent_name=agent_name,
            parent_agent=self._current_parent,
            delegation_depth=self._delegation_depth,
            result=result_str,
            elapsed_time=elapsed,
            metadata={
                **(metadata or {}),
                'success': success
            }
        )
        self._add_event(event)

    def start_tool_call(
        self,
        agent_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        metadata: Optional[Dict] = None,
        tool_call_id: Optional[str] = None,
        parallel_group_id: Optional[str] = None
    ):
        """
        Record tool call start.

        Args:
            agent_name: Name of the agent calling the tool
            tool_name: Name of the tool
            arguments: Arguments passed to the tool
            metadata: Optional metadata
            tool_call_id: Unique ID for this tool call (for parallel execution tracking)
            parallel_group_id: Groups tool calls that execute in parallel
        """
        start_time = time.time()

        if tool_call_id:
            # Dict-based tracking for parallel tool calls
            self._tool_start_times[tool_call_id] = start_time
        else:
            # Legacy: Push to stack for sequential tool calls
            self._operation_stack.append({
                'type': 'tool',
                'name': tool_name,
                'start_time': start_time
            })

        event = TraceEvent(
            timestamp=start_time,
            event_type='tool_call',
            agent_name=agent_name,
            parent_agent=self._current_parent,
            delegation_depth=self._delegation_depth,
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            parallel_group_id=parallel_group_id,
            arguments=arguments,
            metadata=metadata or {}
        )
        self._add_event(event)

    def end_tool_call(
        self,
        agent_name: str,
        tool_name: str,
        result: Any,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None,
        tool_call_id: Optional[str] = None,
        parallel_group_id: Optional[str] = None
    ):
        """
        Record tool call end.

        Args:
            agent_name: Name of the agent
            tool_name: Name of the tool
            result: Result from the tool
            error: Error message if tool failed
            metadata: Optional metadata
            tool_call_id: Unique ID for this tool call (for parallel execution tracking)
            parallel_group_id: Groups tool calls that execute in parallel
        """
        end_time = time.time()

        # Calculate elapsed time
        elapsed = None
        if tool_call_id and tool_call_id in self._tool_start_times:
            # Dict-based tracking for parallel tool calls
            elapsed = end_time - self._tool_start_times.pop(tool_call_id)
        elif self._operation_stack and self._operation_stack[-1]['type'] == 'tool':
            # Legacy: Pop from stack for sequential tool calls
            op = self._operation_stack.pop()
            elapsed = end_time - op['start_time']

        # Truncate result for readability
        result_str = str(result)[:200] if result else None

        event = TraceEvent(
            timestamp=end_time,
            event_type='tool_result',
            agent_name=agent_name,
            parent_agent=self._current_parent,
            delegation_depth=self._delegation_depth,
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            parallel_group_id=parallel_group_id,
            result=result_str,
            error=error,
            elapsed_time=elapsed,
            metadata={
                **(metadata or {}),
                'success': error is None
            }
        )
        self._add_event(event)

    def record_error(self, agent_name: str, error: str, tool_name: Optional[str] = None, metadata: Optional[Dict] = None):
        """
        Record an error.

        Args:
            agent_name: Name of the agent
            error: Error message
            tool_name: Name of the tool that caused the error (if applicable)
            metadata: Optional metadata
        """
        event = TraceEvent(
            timestamp=time.time(),
            event_type='error',
            agent_name=agent_name,
            parent_agent=self._current_parent,
            delegation_depth=self._delegation_depth,
            tool_name=tool_name,
            error=error,
            metadata=metadata or {}
        )
        self._add_event(event)

    def start_delegation(self, from_agent: str, to_agent: str, query: str, metadata: Optional[Dict] = None):
        """
        Record delegation start (agent delegating to another agent).

        Args:
            from_agent: Name of the delegating agent
            to_agent: Name of the delegate agent
            query: Query being delegated
            metadata: Optional metadata
        """
        start_time = time.time()

        # Push to stack
        self._operation_stack.append({
            'type': 'delegation',
            'from': from_agent,
            'to': to_agent,
            'start_time': start_time
        })

        # Increase delegation depth
        self._delegation_depth += 1
        self._current_parent = from_agent

        event = TraceEvent(
            timestamp=start_time,
            event_type='agent_delegate',
            agent_name=from_agent,
            parent_agent=self._current_parent if self._delegation_depth > 1 else None,
            delegation_depth=self._delegation_depth - 1,  # Depth of the calling agent
            arguments={'to_agent': to_agent, 'query': str(query)[:200]},
            metadata=metadata or {}
        )
        self._add_event(event)

    def end_delegation(self, from_agent: str, to_agent: str, result: Any, success: bool = True, metadata: Optional[Dict] = None):
        """
        Record delegation end.

        Args:
            from_agent: Name of the delegating agent
            to_agent: Name of the delegate agent
            result: Result from the delegated agent
            success: Whether the delegation was successful
            metadata: Optional metadata
        """
        end_time = time.time()

        # Pop from stack and calculate elapsed time
        elapsed = None
        if self._operation_stack and self._operation_stack[-1]['type'] == 'delegation':
            op = self._operation_stack.pop()
            elapsed = end_time - op['start_time']

        # Decrease delegation depth
        self._delegation_depth = max(0, self._delegation_depth - 1)

        # Update current parent (pop up the hierarchy)
        if self._delegation_depth > 0 and self._operation_stack:
            # Find the parent in the stack
            for item in reversed(self._operation_stack):
                if item['type'] == 'agent':
                    self._current_parent = item['name']
                    break
        else:
            self._current_parent = None

        # Truncate result for readability
        result_str = str(result)[:200] if result else None

        event = TraceEvent(
            timestamp=end_time,
            event_type='delegation_end',
            agent_name=from_agent,
            parent_agent=self._current_parent,
            delegation_depth=self._delegation_depth,
            result=result_str,
            elapsed_time=elapsed,
            metadata={
                **(metadata or {}),
                'to_agent': to_agent,
                'success': success
            }
        )
        self._add_event(event)

    def get_trace(self) -> List[TraceEvent]:
        """
        Get all trace events.

        Returns:
            List of trace events
        """
        return self.events

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the trace.

        Returns:
            Dictionary with trace statistics
        """
        if not self.events:
            return {
                'total_events': 0,
                'agent_runs': 0,
                'tool_calls': 0,
                'errors': 0,
                'total_time': 0
            }

        agent_starts = [e for e in self.events if e.event_type == 'agent_start']
        agent_ends = [e for e in self.events if e.event_type == 'agent_end']
        tool_calls = [e for e in self.events if e.event_type == 'tool_call']
        tool_results = [e for e in self.events if e.event_type == 'tool_result']
        errors = [e for e in self.events if e.event_type == 'error']

        # Calculate total time
        total_time = 0
        for end_event in agent_ends:
            if end_event.elapsed_time:
                total_time += end_event.elapsed_time

        # Calculate average tool call time
        tool_times = [e.elapsed_time for e in tool_results if e.elapsed_time]
        avg_tool_time = sum(tool_times) / len(tool_times) if tool_times else 0

        return {
            'total_events': len(self.events),
            'agent_runs': len(agent_starts),
            'tool_calls': len(tool_calls),
            'errors': len(errors),
            'total_time': total_time,
            'average_tool_time': avg_tool_time,
            'success_rate': (len(tool_results) - len([e for e in tool_results if e.error])) / len(tool_results) if tool_results else 1.0
        }

    def export_json(self, filepath: str):
        """
        Export all trace events to a JSON Lines file.

        Args:
            filepath: Path to output file
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            for event in self.events:
                f.write(event.to_json() + '\n')

    def export_summary(self, filepath: str):
        """
        Export trace summary to a JSON file.

        Args:
            filepath: Path to output file
        """
        summary = self.get_summary()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dumps(summary, indent=2, ensure_ascii=False)

    def clear(self):
        """Clear all trace events."""
        self.events.clear()
        self._operation_stack.clear()
        self._tool_start_times.clear()

    def __str__(self) -> str:
        """String representation with summary."""
        summary = self.get_summary()
        return (
            f"TracingKit(events={summary['total_events']}, "
            f"agent_runs={summary['agent_runs']}, "
            f"tool_calls={summary['tool_calls']}, "
            f"errors={summary['errors']})"
        )

    def __repr__(self) -> str:
        return f"<TracingKit: {len(self.events)} events>"
