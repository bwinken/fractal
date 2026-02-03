# Delegation-Aware Tracing Implementation

## Overview

Implemented delegation-aware tracing that automatically tracks complete agent delegation chains with zero configuration overhead. When a top-level agent enables tracing, all delegated agents automatically inherit the same TracingKit instance, allowing for complete execution flow visibility.

## Key Features

### 1. TracingKit "Infection" Pattern

The top agent's TracingKit automatically propagates to all delegated agents:

```python
# Only enable tracing at the top level
coordinator = CoordinatorAgent(enable_tracing=True)
specialist = SpecialistAgent(enable_tracing=False)  # Will be "infected"

coordinator.register_delegate(specialist)

# When coordinator delegates to specialist, specialist temporarily uses
# coordinator's TracingKit instance
await coordinator.run("Task")

# All events from both agents are in coordinator's trace
all_events = coordinator.tracing.get_trace()
```

### 2. Delegation Hierarchy Tracking

Each trace event includes:
- `parent_agent`: The agent that delegated to this agent
- `delegation_depth`: Position in the delegation chain (0 = top level)

```python
# Example trace events:
# CoordinatorA (depth=0, parent=None)
#   -> SpecialistB (depth=1, parent=CoordinatorA)
#      -> SpecialistC (depth=2, parent=SpecialistB)
```

### 3. Delegation Events

Two new event types track delegation flow:
- `agent_delegate`: When an agent delegates to another agent
- `delegation_end`: When delegation returns with result

```python
# Delegation flow:
1. Coordinator calls tool "ask_specialist" (tool_call)
2. Delegation starts (agent_delegate: Coordinator -> Specialist)
3. Specialist starts execution (agent_start: Specialist, depth=1)
4. Specialist completes (agent_end: Specialist)
5. Delegation ends (delegation_end: Specialist -> Coordinator)
6. Tool returns result (tool_result)
```

## Implementation Details

### Modified Files

#### 1. `fractal/tracing.py`

**TraceEvent Dataclass**:
- Added `parent_agent: Optional[str]` field
- Added `delegation_depth: int` field

**TracingKit Class**:
- Added `_delegation_depth: int` tracking
- Added `_current_parent: Optional[str]` tracking
- All event creation methods updated to include parent/depth info
- New methods:
  - `start_delegation()`: Record delegation start
  - `end_delegation()`: Record delegation end

#### 2. `fractal/toolkit.py`

**register_delegate() Method**:
- Modified `agent_caller` wrapper to:
  - Check if calling agent has tracing enabled
  - Temporarily set delegated agent's tracing to calling agent's TracingKit
  - Record delegation start before calling delegated agent
  - Record delegation end after completion
  - Restore original tracing state

```python
async def agent_caller(query: str) -> AgentReturnPart:
    calling_agent = self._target

    if calling_agent and calling_agent.tracing:
        # Save original tracing
        original_tracing = agent.tracing

        # Infect with calling agent's tracing
        agent.tracing = calling_agent.tracing

        # Record delegation
        calling_agent.tracing.start_delegation(...)

        try:
            result = await agent.run(query)
            calling_agent.tracing.end_delegation(...)
            return result
        finally:
            # Restore original tracing
            agent.tracing = original_tracing
    else:
        # No tracing - run normally
        return await agent.run(query)
```

## Event Flow Example

```
Coordinator.run("Task")
  |
  +-- agent_start (Coordinator, depth=0, parent=None)
  |
  +-- tool_call (ask_specialist, depth=0)
  |   |
  |   +-- agent_delegate (Coordinator -> Specialist, depth=0)
  |   |
  |   +-- agent_start (Specialist, depth=1, parent=Coordinator)
  |   |
  |   +-- tool_call (analyze, depth=1)
  |   |
  |   +-- tool_result (analyze, depth=1)
  |   |
  |   +-- agent_end (Specialist, depth=1, parent=Coordinator)
  |   |
  |   +-- delegation_end (Specialist -> Coordinator, depth=0)
  |
  +-- tool_result (ask_specialist, depth=0)
  |
  +-- agent_end (Coordinator, depth=0, parent=None)
```

## Multi-Level Delegation

Works seamlessly with any depth of delegation:

```python
# A -> B -> C hierarchy
coordinator_a = CoordinatorAgent(enable_tracing=True)
specialist_b = SpecialistAgent()
specialist_c = SpecialistAgent()

specialist_b.register_delegate(specialist_c)
coordinator_a.register_delegate(specialist_b)

await coordinator_a.run("Deep task")

# Trace shows complete hierarchy:
# A (depth=0, parent=None)
#   B (depth=1, parent=A)
#     C (depth=2, parent=B)
```

## Usage Examples

### Basic Delegation Tracing

```python
from fractal import BaseAgent

# Create agents
specialist = SpecialistAgent(enable_tracing=False)
coordinator = CoordinatorAgent(enable_tracing=True)
coordinator.register_delegate(specialist)

# Run
result = await coordinator.run("Task")

# View trace
for event in coordinator.tracing.get_trace():
    indent = "  " * event.delegation_depth
    print(f"{indent}{event.event_type}: {event.agent_name}")
```

### Analyzing Delegation Chain

```python
# Get all agent start events
agent_events = [
    e for e in coordinator.tracing.get_trace()
    if e.event_type == 'agent_start'
]

# Show hierarchy
for event in agent_events:
    indent = "  " * event.delegation_depth
    parent = f" <- {event.parent_agent}" if event.parent_agent else ""
    print(f"{indent}{event.agent_name}{parent}")
```

### Finding Delegation Events

```python
# Get delegation flow
delegation_events = [
    e for e in coordinator.tracing.get_trace()
    if e.event_type in ('agent_delegate', 'delegation_end')
]

for event in delegation_events:
    if event.event_type == 'agent_delegate':
        to_agent = event.arguments.get('to_agent')
        print(f"Delegate: {event.agent_name} -> {to_agent}")
    else:
        from_agent = event.metadata.get('to_agent')
        print(f"Return: {from_agent} -> {event.agent_name}")
```

## Testing

### Test Files

1. **test_delegation_tracing.py**: Comprehensive test suite
   - Basic delegation tracing (A -> B)
   - Multi-level delegation (A -> B -> C)
   - Verification of parent_agent and delegation_depth
   - Delegation event recording

2. **examples/delegation_tracing_example.py**: Usage examples
   - Basic delegation with multiple specialists
   - Multi-level delegation hierarchy
   - Detailed trace analysis

### Running Tests

```bash
# Run delegation tracing tests
python test_delegation_tracing.py

# Run examples
python examples/delegation_tracing_example.py
```

## Benefits

1. **Zero Configuration**: Only enable tracing at the top level
2. **Complete Visibility**: See entire execution flow including all delegations
3. **Performance**: Minimal overhead when tracing is disabled
4. **Debugging**: Easily identify which agent performed which actions
5. **Analysis**: Understand delegation patterns and execution flow
6. **Production Ready**: Track delegation chains in production systems

## Trace Export Format

Events are exported in JSON Lines format (.jsonl):

```json
{"timestamp": 1234567890.123, "event_type": "agent_start", "agent_name": "Coordinator", "parent_agent": null, "delegation_depth": 0, ...}
{"timestamp": 1234567890.234, "event_type": "agent_delegate", "agent_name": "Coordinator", "delegation_depth": 0, "arguments": {"to_agent": "Specialist"}, ...}
{"timestamp": 1234567890.345, "event_type": "agent_start", "agent_name": "Specialist", "parent_agent": "Coordinator", "delegation_depth": 1, ...}
{"timestamp": 1234567890.456, "event_type": "agent_end", "agent_name": "Specialist", "parent_agent": "Coordinator", "delegation_depth": 1, ...}
{"timestamp": 1234567890.567, "event_type": "delegation_end", "agent_name": "Coordinator", "delegation_depth": 0, ...}
```

## Documentation

- [TRACING.md](TRACING.md): Complete tracing guide
- [CHANGELOG.md](../CHANGELOG.md): Recent changes
- [examples/delegation_tracing_example.py](../examples/delegation_tracing_example.py): Usage examples

## Summary

Delegation-aware tracing provides complete observability for multi-agent systems with zero configuration overhead. The "infection" pattern ensures that enabling tracing at the top level automatically captures the entire delegation chain, making it easy to debug, analyze, and monitor complex agent hierarchies.
