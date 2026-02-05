# Changelog

## [Unreleased]

### Added - Dynamic System Prompts

**New Feature: Runtime-Configurable System Prompts**

System prompts can now be dynamically generated at runtime using templates or callables.

**Features**:
- **Template substitution**: Use `{placeholder}` syntax with `system_context` dict
- **Callable prompts**: Pass a function/lambda that returns the prompt string
- **Runtime updates**: Use `update_system_context()` to modify template values
- **Per-request personalization**: Ideal for FastAPI backends with user-specific prompts

**Usage**:
```python
# Template-based
agent = BaseAgent(
    name="Support",
    system_prompt="You help {user_name} ({plan} plan). Be {tone}.",
    system_context={"user_name": "Alice", "plan": "pro", "tone": "friendly"}
)
# → "You help Alice (pro plan). Be friendly."

# Update at runtime
agent.update_system_context(user_name="Bob", tone="formal")

# Callable-based (full dynamic control)
state = {"mode": "debug"}
agent = BaseAgent(
    name="Debug",
    system_prompt=lambda: f"Mode: {state['mode']}"
)
```

**Use Cases**:
- Per-user personalization in web backends
- RAG context injection before each query
- Multi-tenant SaaS with tenant-specific prompts
- A/B testing different prompt variants

See [examples/dynamic_prompt_example.py](examples/dynamic_prompt_example.py) for complete examples.

---

### Added - Parallel Tool Execution

**New Feature: Concurrent Tool Execution with `asyncio.gather()`**

When the LLM requests multiple tool calls in a single response, they now execute in parallel instead of sequentially.

**Features**:
- Tools execute concurrently using `asyncio.gather()`
- Each tool call tracked by `tool_call_id` for accurate timing
- `parallel_group_id` groups tool calls from the same batch
- Tracing correctly handles overlapping start/end events
- Termination tools still work (checked after all tools complete)
- Backward compatible with existing sequential code

**Performance**:
```
# Before (sequential): Tool A (1s) → Tool B (1s) → Tool C (1s) = 3s total
# After (parallel):    Tool A, B, C execute together = ~1s total
```

**Trace Events**:
```json
{"event_type": "tool_call", "tool_name": "get_weather", "tool_call_id": "call_abc", "parallel_group_id": "grp_123"}
{"event_type": "tool_call", "tool_name": "get_stock", "tool_call_id": "call_def", "parallel_group_id": "grp_123"}
{"event_type": "tool_result", "tool_name": "get_stock", "tool_call_id": "call_def", "elapsed_time": 0.3}
{"event_type": "tool_result", "tool_name": "get_weather", "tool_call_id": "call_abc", "elapsed_time": 0.5}
```

---

### Added - Per-Run Trace Isolation

**New Feature: `{run_id}` Placeholder for Trace Files**

Each `run()` call now generates a unique `run_id`, enabling separate trace files per execution.

**Features**:
- `{run_id}` placeholder in `tracing_output_file` creates unique files
- `{timestamp}` placeholder also supported
- Events cleared between runs (no cross-contamination)
- Essential for FastAPI backends with concurrent requests

**Usage**:
```python
agent = BaseAgent(
    name="Agent",
    enable_tracing=True,
    tracing_output_file="traces/run_{run_id}.jsonl"  # Each run() creates new file
)

# Run 1 → traces/run_a1b2c3d4.jsonl
# Run 2 → traces/run_e5f6g7h8.jsonl
```

See [examples/multi_run_demo.py](examples/multi_run_demo.py) for demonstration.

---

### Added - `fractal` CLI Command

**New Feature: Short CLI Command**

Added `fractal` as a console script entry point for easier trace visualization.

**Before**:
```bash
python -m fractal.observability view trace.jsonl
python -m fractal.observability visualize trace.jsonl
```

**After** (recommended):
```bash
fractal view trace.jsonl
fractal visualize trace.jsonl -o output.html
```

Both invocation methods work. Install with `pip install .` to enable the `fractal` command.

---

### Refactored - Code Organization

**Code Structure Refactoring**

Reorganized tracing and visualization code into a dedicated `observability` submodule for better maintainability and clarity.

**Changes**:
- Created `fractal/observability/` submodule
- Moved `tracing.py` → `observability/tracing.py`
- Renamed `trace_visualizer.py` → `observability/html_visualizer.py` (clearer naming)
- Renamed `trace_viewer.py` → `observability/terminal_viewer.py` (clearer naming)
- Added unified CLI entry point via `observability/__main__.py`

**New Commands** (recommended):
```bash
# View trace in terminal
python -m fractal.observability view trace.jsonl

# Generate HTML visualization
python -m fractal.observability visualize trace.jsonl
```

**Old Commands** (still supported):
```bash
python -m fractal.observability.terminal_viewer trace.jsonl
python -m fractal.observability.html_visualizer trace.jsonl
```

**Backward Compatibility**: ✅ Fully backward compatible
- All existing imports still work: `from fractal import TracingKit, TraceEvent`
- No code changes required for existing projects
- Old commands work via full module paths

See [docs/REFACTORING.md](docs/REFACTORING.md) for complete details.

---

### Added - TracingKit for Observability

**New Feature: Execution Tracing and Monitoring**

Added `TracingKit` - a lightweight tracing toolkit for monitoring agent execution with zero dependencies.

**Features**:
- Record agent runs (start/end, elapsed time, results)
- Record tool calls (name, arguments, results, elapsed time)
- Track errors and failures
- **Delegation-aware tracing**: Automatically tracks complete delegation chains
  - Top agent's TracingKit "infects" all delegated agents
  - Tracks `parent_agent` and `delegation_depth` for each event
  - Records delegation start/end events
  - Works seamlessly with multi-level delegation (A → B → C)
- Export traces to JSON Lines format
- Get execution summaries and statistics
- Optional enable/disable (no overhead when disabled)

**Usage**:
```python
# Enable tracing
agent = MyAgent(
    name="Agent",
    system_prompt="You are helpful.",
    enable_tracing=True,  # Enable tracing
    tracing_output_file="trace.jsonl"  # Optional: export to file
)

# Run agent
result = await agent.run("Task")

# Get trace summary
summary = agent.tracing.get_summary()
print(f"Tool calls: {summary['tool_calls']}")
print(f"Total time: {summary['total_time']:.2f}s")

# Export trace
agent.tracing.export_json("trace.jsonl")
```

**Benefits**:
- Zero external dependencies (pure Python stdlib)
- Low overhead (< 5% performance impact)
- Optional (no impact when disabled)
- Detailed execution flow tracking
- Easy integration with logging systems

See [docs/TRACING.md](docs/TRACING.md) and [examples/tracing_example.py](examples/tracing_example.py) for details.

### Added - Trace Visualization Tools

**New Feature: Zero-Dependency Trace Visualization**

Added two visualization tools for analyzing agent execution traces:

**1. HTML Visualizer (`observability/html_visualizer.py`)**:
- Interactive web-based visualization
- Timeline, hierarchy, and event list views
- Click events to see full details
- Self-contained HTML output

```bash
python -m fractal.observability visualize trace.jsonl -o output.html
```

**2. Terminal Viewer (`observability/terminal_viewer.py`)**:
- ASCII art visualization in terminal
- Summary, hierarchy, flow chart, and timeline views
- Perfect for quick checks and CI/CD
- Compact mode for dense output

```bash
python -m fractal.observability view trace.jsonl --flow
```

**Features**:
- Zero external dependencies (Python stdlib + browser for HTML)
- Visualize delegation chains and execution flow
- Color-coded event types (HTML) and icons (Terminal)
- Performance analysis with elapsed times
- Interactive exploration (HTML) or quick checks (Terminal)

See [docs/TRACE_VISUALIZATION.md](docs/TRACE_VISUALIZATION.md) for complete usage guide.

---

### Changed - API Improvements

#### Better Delegation API Naming

**1. Renamed `register_agent()` → `register_delegate()`**

The new name better reflects the intent: registering a **subordinate/specialist agent** for task delegation.

```python
# Before (still works for backwards compatibility)
self.register_agent(specialist, tool_name="ask_specialist")

# Now (recommended)
self.register_delegate(specialist, tool_name="ask_specialist")
```

**Why?**
- **More intuitive**: Clearly indicates hierarchy (coordinator → delegate)
- **Better semantics**: "delegate" implies task delegation, not just registration
- **Clearer intent**: Shows this is for multi-agent collaboration

**2. Updated default tool naming**

Default tool names now use `delegate_to_` prefix instead of `call_`:

```python
# Before
specialist = SpecialistAgent(name="Specialist")
coordinator.register_agent(specialist)
# Created tool: "call_specialist"

# Now
specialist = SpecialistAgent(name="Specialist")
coordinator.register_delegate(specialist)
# Created tool: "delegate_to_specialist"
```

**3. Fixed type annotations**

```python
# Before (incorrect)
def register_agent(self, agent: 'AgentToolkit', ...)

# Now (correct)
def register_delegate(self, agent: 'BaseAgent', ...)
```

The parameter type is now correctly `BaseAgent` instead of `AgentToolkit`, since:
- Agents no longer inherit from AgentToolkit (composition pattern)
- The registered object needs a `run()` method, which is part of BaseAgent

### Backwards Compatibility

The old `register_agent()` method is kept as a deprecated alias:

```python
def register_agent(self, agent, tool_name=None, description=None):
    """Deprecated: Use register_delegate() instead."""
    self.register_delegate(agent, tool_name, description)
```

**All existing code continues to work without changes!**

### Documentation Updates

- Updated [MULTIAGENT.md](docs/MULTIAGENT.md) with new API
- Updated all examples to use `register_delegate()`
- Added clearer explanations of delegation hierarchy

### Migration Guide

**Optional migration** (old code still works):

```python
# Old way (still supported)
class Coordinator(BaseAgent):
    def __init__(self, specialist):
        super().__init__(...)
        self.register_agent(specialist, "ask_specialist")

# New way (recommended)
class Coordinator(BaseAgent):
    def __init__(self, specialist):
        super().__init__(...)
        self.register_delegate(specialist, "ask_specialist")
```

No code changes required - migration is optional for better clarity!

---

## Previous Changes

### Architecture Refactoring

**Changed from Inheritance to Composition**

- `BaseAgent` no longer inherits from `AgentToolkit`
- Uses composition: `self.toolkit = AgentToolkit(target=self)`
- Benefits:
  - Clearer separation of concerns
  - More flexible architecture
  - Follows "Composition over Inheritance" principle

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.
