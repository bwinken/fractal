# Fractal

**Self-similar agent decomposition for building complex AI workflows.**

Just as fractals create complexity through repeated simple patterns, Fractal creates powerful agent systems through recursive delegation. Each agent focuses on one task and delegates the rest — the same pattern at every depth.

```
Coordinator
  +-- Researcher     (depth=1)
  |     +-- Analyst  (depth=2)
  +-- Writer         (depth=1)
```

---

## Table of Contents

- [Design Philosophy](#design-philosophy)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
  - [Class-Based Agent](#1-class-based-agent)
  - [Functional Style](#2-functional-style-no-subclassing)
  - [Multi-Agent Delegation](#3-multi-agent-delegation)
  - [Execution Tracing](#4-execution-tracing)
- [API Reference](#api-reference)
  - [BaseAgent](#baseagent)
  - [@tool / @AgentToolkit.register_as_tool](#tool--agenttoolkitregister_as_tool)
  - [Tool Argument Constraints](#tool-argument-constraints)
  - [AgentResult](#agentresult)
  - [ToolResult](#toolresult)
  - [TracingKit](#tracingkit)
- [Observability CLI](#observability-cli)
- [FastAPI Integration](#fastapi-integration)
- [Examples](#examples)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Design Philosophy

Fractal is built on three core ideas:

**1. Recursive Delegation**
An agent that can't do something delegates to one that can. The delegated agent may delegate further. This creates tree-shaped workflows of arbitrary depth — the same pattern repeating at every level, like a fractal.

**2. Composition over Inheritance**
Each `BaseAgent` owns an `AgentToolkit` (HAS-A, not IS-A). You can build agents by subclassing and decorating methods, or by composing standalone functions with `add_tool()`. Both approaches use the same underlying toolkit.

**3. Tools via Docstrings**
Write a Python function with a Google-style docstring and Fractal automatically generates the [OpenAI tool schema](https://platform.openai.com/docs/guides/function-calling). No manual JSON. No schema files. The docstring *is* the schema.

---

## Features

| Category | Details |
|----------|---------|
| **Delegation** | Recursive agent-to-agent delegation with structured or simple inputs |
| **LLM** | OpenAI API + any compatible endpoint (Azure, Ollama, LM Studio) |
| **Async** | Native `async`/`await`; mixed sync and async tools |
| **Tools** | Decorator-based (`@tool`) or functional (`add_tool()`) registration |
| **Dynamic Prompts** | Template placeholders or callables for per-request system prompts |
| **I/O** | `str`, `dict`, `list`, or Pydantic `BaseModel` between agents and tools |
| **Observability** | Delegation-aware tracing → JSON Lines → terminal ASCII or interactive HTML |
| **FastAPI** | Drop agents into endpoints with lifespan management |
| **Validation** | Registration-time checks for unsupported types, docstring mismatches |

---

## Installation

```bash
pip install .
```

With FastAPI support:

```bash
pip install ".[fastapi]"
```

**Requirements:** Python >= 3.9, openai >= 1.0.0, pydantic >= 2.0.0, python-dotenv >= 1.0.0

---

## Configuration

Fractal reads OpenAI settings from environment variables or a `.env` file.

```bash
# .env (recommended for local development)
OPENAI_API_KEY=sk-your-api-key-here
# OPENAI_BASE_URL=https://your-api.com/v1   # Optional: Azure, Ollama, etc.
# OPENAI_MODEL=gpt-4o-mini                  # Optional: default model
```

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | — |
| `OPENAI_BASE_URL` | Custom API endpoint | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | Default model name | `gpt-4o-mini` |
| `CONTEXT_WINDOW` | Token limit for auto-trimming conversation history | disabled |

> **Priority:** Constructor arguments > environment variables > defaults.

---

## Quick Start

### 1. Class-Based Agent

Subclass `BaseAgent` and decorate methods with `@tool`:

```python
import asyncio
from openai import AsyncOpenAI
from fractal import BaseAgent, AgentToolkit

class MathAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="MathBot",
            system_prompt="You are a math assistant. Use tools to compute.",
            model="gpt-4o-mini",
            client=AsyncOpenAI()
        )

    @AgentToolkit.register_as_tool
    def add(self, a: int, b: int) -> int:
        """
        Add two numbers.

        Args:
            a (int): First number
            b (int): Second number

        Returns:
            Sum of a and b
        """
        return a + b

    @AgentToolkit.register_as_tool
    def multiply(self, a: int, b: int) -> int:
        """
        Multiply two numbers.

        Args:
            a (int): First number
            b (int): Second number

        Returns:
            Product of a and b
        """
        return a * b

async def main():
    agent = MathAgent()
    result = await agent.run("What is (3 + 4) * 5?")
    print(result.content)

asyncio.run(main())
```

The framework automatically:
1. Discovers methods decorated with `@AgentToolkit.register_as_tool`
2. Parses Google-style docstrings into OpenAI tool schemas
3. Handles the tool-call loop until the agent produces a final response

### 2. Functional Style (No Subclassing)

Use `add_tool()` to register standalone functions — no inheritance required:

```python
import asyncio
from fractal import BaseAgent, tool

agent = BaseAgent(
    name="MathBot",
    system_prompt="You are a math assistant. Use tools to compute."
)

@tool
def add(a: int, b: int) -> int:
    """Add two numbers.

    Args:
        a (int): First number
        b (int): Second number
    """
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers.

    Args:
        a (int): First number
        b (int): Second number
    """
    return a * b

agent.add_tool(add)
agent.add_tool(multiply)

async def main():
    result = await agent.run("What is (3 + 4) * 5?")
    print(result.content)

asyncio.run(main())
```

### 3. Multi-Agent Delegation

Register one agent as a delegate of another with `register_delegate()`:

```python
coordinator = Coordinator()
math_agent = MathAgent()

# Simple: delegate receives a single query string
coordinator.register_delegate(
    math_agent,
    tool_name="calculate",
    description="Perform math calculations"
)

result = await coordinator.run("Compute (3 + 4) * 5")
```

For more control, use `parameters` to define structured inputs — the delegate receives a dict:

```python
coordinator.register_delegate(
    data_agent,
    tool_name="query_data",
    description="Query the data warehouse",
    parameters={
        "sql": {"type": "str", "description": "SQL query to execute"},
        "limit": {"type": "int", "description": "Max rows to return", "required": False},
    }
)
# LLM calls: query_data(sql="SELECT ...", limit=100)
# data_agent.run({"sql": "SELECT ...", "limit": 100})
```

Delegation can be nested to arbitrary depth (A → B → C → ...). When tracing is enabled on the top-level agent, it automatically propagates through the entire chain.

### 4. Execution Tracing

Enable tracing to record every agent start/end, tool call, and delegation event:

```python
class TracedCoordinator(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Coordinator",
            system_prompt="...",
            client=AsyncOpenAI(),
            enable_tracing=True,
            # Each run() creates a separate file: trace_a1b2c3d4.jsonl
            tracing_output_file="trace_{run_id}.jsonl"
        )
```

The `tracing_output_file` supports placeholders:
- `{run_id}` — unique ID for this run (12-char hex)
- `{timestamp}` — ISO timestamp (`20240115_143022`)

Each `run()` call creates a separate trace file, so concurrent requests in a FastAPI backend won't mix traces.

View traces:

```bash
fractal view trace_a1b2c3d4.jsonl              # Terminal ASCII view
fractal view trace_a1b2c3d4.jsonl --summary    # Summary statistics
fractal visualize trace_a1b2c3d4.jsonl -o out.html   # Interactive HTML
```

---

## API Reference

### BaseAgent

The main agent class. Handles OpenAI API communication, tool execution loop, and delegation.

```python
agent = BaseAgent(
    name="MyAgent",                    # Agent name (used in tracing)
    system_prompt="You are helpful.",   # System prompt (str or Callable[[], str])
    system_context=None,               # Dict for template placeholders (e.g., {"user": "Alice"})
    model="gpt-4o-mini",               # Falls back to OPENAI_MODEL env var, then "gpt-4o-mini"
    client=AsyncOpenAI(),              # Falls back to OPENAI_API_KEY / OPENAI_BASE_URL env vars
    temperature=0.7,                   # Sampling temperature (0-2)
    max_tokens=None,                   # Max response tokens
    enable_tracing=False,              # Enable execution tracing
    tracing_output_file=None,          # Auto-export trace to this file
    context_window=None                # Token limit for auto-trimming (e.g., 128000)
)
```

**Dynamic System Prompts:**

The `system_prompt` parameter accepts either a static string or a callable (function/lambda) that returns a string. When using templates with `{placeholders}`, provide a `system_context` dict for substitution:

```python
# Template-based: placeholders resolved from system_context
agent = BaseAgent(
    name="Support",
    system_prompt="You help {user_name} ({plan} plan). Be {tone}.",
    system_context={"user_name": "Alice", "plan": "pro", "tone": "friendly"}
)
# → "You help Alice (pro plan). Be friendly."

# Update context at runtime
agent.update_system_context(user_name="Bob", tone="formal")

# Callable-based: full dynamic control
external_state = {"mode": "debug"}
agent = BaseAgent(
    name="Debug",
    system_prompt=lambda: f"Mode: {external_state['mode']}"
)
# Prompt recomputed on each run() call
```

**Methods:**

| Method | Description |
|--------|-------------|
| `await run(user_input, max_iterations=10, max_retries=3)` | Run the agent and return `AgentResult` |
| `reset()` | Clear conversation history |
| `update_system_context(**kwargs)` | Merge new values into `system_context` (for template prompts) |
| `add_tool(func, name=None, terminate=False)` | Register a standalone function as a tool |
| `register_delegate(agent, tool_name=None, description=None, parameters=None)` | Register an agent as a delegate tool |
| `get_tools()` | Get all registered tools |
| `get_tool_schemas()` | Get OpenAI-compatible tool schemas |
| `await execute_tool(tool_name, **kwargs)` | Execute a registered tool by name |

### @tool / @AgentToolkit.register_as_tool

Register agent methods as callable tools. Both forms are equivalent:

```python
from fractal import BaseAgent, tool

class MyAgent(BaseAgent):
    @tool
    def my_tool(self, query: str) -> str:
        """Tool description.

        Args:
            query (str): Search query
        """
        return f"Result for: {query}"

    @tool(name="custom_name", terminate=True)
    def final_answer(self, answer: str) -> str:
        """Return final answer and stop the agent loop.

        Args:
            answer (str): The final answer
        """
        return answer
```

**Decorator options:**
- `name` — Override the tool name (default: method name)
- `terminate` — If `True`, the agent loop stops after this tool executes

### Tool Argument Constraints

Tool parameters are converted to [OpenAI tool schemas](https://platform.openai.com/docs/guides/function-calling) via Google-style docstrings. The framework validates tools at registration time to catch common mistakes early.

**Supported parameter types:**

| Python type | JSON Schema type | Notes |
|-------------|-----------------|-------|
| `str` | `string` | |
| `int` | `integer` | |
| `float` | `number` | |
| `bool` | `boolean` | |
| `list` | `array` | No `items` schema — LLM won't know the element type |
| `dict` | `object` | No `properties` schema — LLM won't know the key/value types |

**Raises `TypeError` (blocks registration):**
- `tuple`, `set`, `bytes`, `datetime` — no JSON Schema equivalent
- Pydantic `BaseModel` subclasses — LLM arguments are raw JSON, not model instances
- Any custom class — same reason

```python
@tool
def bad_tool(profile: UserProfile, tags: tuple) -> str:
    """Process data."""
    return "result"

agent.add_tool(bad_tool)
# TypeError: Tool 'bad_tool': parameter 'profile' has unsupported type annotation
#   'UserProfile'. Supported types: str, int, float, bool, list, dict.
```

**Issues `UserWarning` (registration succeeds):**
- Missing docstring — LLM gets no tool description
- Parameter not in docstring `Args:` section — LLM gets no parameter description
- Type annotation vs docstring type mismatch — schema uses docstring type, may cause runtime errors

```python
@tool
def mismatch_tool(count: int) -> str:
    """Search.

    Args:
        count (str): Number of results    # docstring says str, annotation says int!
    """
    return str(count)

agent.add_tool(mismatch_tool)
# UserWarning: Tool 'mismatch_tool': parameter 'count' type mismatch —
#   annotation says 'int' (→ integer) but docstring says 'string'.
#   The docstring type will be used in the tool schema.
```

**Other constraints:**
- Type information comes from the **docstring `Args:` section**, not from Python annotations. Annotations are used for validation only.
- `Optional[str]` is fine — unwraps to `str`. `Union[str, int]` is not well supported.
- Default values make a parameter optional (omitted from `required`), but the default value itself is **not** included in the schema.
- A parameter missing from `Args:` receives an empty description.
- A function with no docstring uses the function name as the tool description.

### AgentResult

Returned by `agent.run()`.

| Field | Type | Description |
|-------|------|-------------|
| `content` | `str \| dict \| list \| BaseModel` | Agent response |
| `agent_name` | `str` | Name of the agent |
| `metadata` | `dict \| None` | Additional metadata |
| `success` | `bool` | Whether execution succeeded |

### ToolResult

Returned by `agent.execute_tool()`.

| Field | Type | Description |
|-------|------|-------------|
| `content` | `str \| dict \| list \| BaseModel` | Tool output |
| `tool_name` | `str` | Name of the tool |
| `metadata` | `dict \| None` | Execution metadata |
| `error` | `str \| None` | Error message if failed |

### TracingKit

Execution tracing with delegation awareness. When the top-level agent has tracing enabled, the `TracingKit` instance automatically propagates to all delegated agents ("infection pattern"), recording `parent_agent` and `delegation_depth` for each event.

Each `run()` call starts a new trace session with a unique `run_id`. Events from previous runs are cleared, and a new output file is created (when using `{run_id}` or `{timestamp}` placeholders).

```python
from fractal import TracingKit, TraceEvent

kit = TracingKit(output_file="trace_{run_id}.jsonl")

# Start a new run (clears previous events, generates run_id)
run_id = kit.start_run()

kit.start_agent("MyAgent", user_input="hello")
kit.start_tool_call("MyAgent", "my_tool", {"query": "test"})
kit.end_tool_call("MyAgent", "my_tool", result="done")
kit.end_agent("MyAgent", result="completed")

kit.end_run()

events: list[TraceEvent] = kit.get_trace()
summary: dict = kit.get_summary()
```

**TraceEvent fields:** `timestamp`, `event_type`, `agent_name`, `run_id`, `parent_agent`, `delegation_depth`, `tool_name`, `arguments`, `result`, `error`, `elapsed_time`, `metadata`

**Event types:** `agent_start`, `agent_end`, `agent_delegate`, `delegation_end`, `tool_call`, `tool_result`, `error`

---

## Observability CLI

```bash
# Terminal view (ASCII art, zero dependencies)
fractal view trace.jsonl
fractal view trace.jsonl --summary
fractal view trace.jsonl --flow
fractal view trace.jsonl --hierarchy
fractal view trace.jsonl --compact

# HTML view (interactive, self-contained single file)
fractal visualize trace.jsonl
fractal visualize trace.jsonl -o output.html
```

Sample output:

```
================================================================================
EXECUTION FLOW
================================================================================
+-- START: Orchestrator
+--> DELEGATE TO: Calculator
  +-- START: Calculator
  +-- END: Calculator (1.532s)
+<-- RETURN
+--> DELEGATE TO: DataProcessor
  +-- START: DataProcessor
  +-- END: DataProcessor (0.608s)
+<-- RETURN
+-- END: Orchestrator (5.875s)
================================================================================
```

---

## FastAPI Integration

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from openai import AsyncOpenAI
from fractal import BaseAgent, AgentToolkit

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="APIAgent",
            system_prompt="You are helpful.",
            client=AsyncOpenAI()
        )

    @AgentToolkit.register_as_tool
    def lookup(self, query: str) -> str:
        """Look up information.

        Args:
            query (str): Search query
        """
        return f"Info about {query}"

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.agent = MyAgent()
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/query")
async def query(text: str):
    result = await app.state.agent.run(text)
    return {"response": result.content, "success": result.success}
```

See [examples/fastapi_example.py](examples/fastapi_example.py) and [examples/fastapi_multiagent.py](examples/fastapi_multiagent.py) for complete examples.

---

## Examples

Choose the right example for your use case:

### Getting Started

| What you want to do | Example | API Key? |
|---------------------|---------|----------|
| Understand the basics, explore tool schemas | [inheritance_example.py](examples/inheritance_example.py) | **No** |
| See the functional `add_tool()` pattern | [basic_example.py](examples/basic_example.py) | Partial |

### Single-Agent Patterns

| What you want to do | Example | API Key? |
|---------------------|---------|----------|
| Build agents with class inheritance | [inheritance_example.py](examples/inheritance_example.py) | No |
| Use standalone toolkit without subclassing | [basic_example.py](examples/basic_example.py) | Yes |
| Use dynamic system prompts (templates, callables) | [dynamic_prompt_example.py](examples/dynamic_prompt_example.py) | **No** |
| Mix sync and async tools, concurrent execution | [async_example.py](examples/async_example.py) | Yes |

### Multi-Agent Patterns

| What you want to do | Example | API Key? |
|---------------------|---------|----------|
| Coordinator delegates to specialists | [multiagent_example.py](examples/multiagent_example.py) | Yes |
| Handle overlapping tool names across agents | [tool_namespacing_example.py](examples/tool_namespacing_example.py) | Yes |
| Knowledge-based Q&A with vector search (RAG) | [rag_example.py](examples/rag_example.py) | Yes |

### Web / API Integration

| What you want to do | Example | API Key? |
|---------------------|---------|----------|
| Serve a single agent over HTTP | [fastapi_example.py](examples/fastapi_example.py) | Yes |
| Serve multiple agents with routing | [fastapi_multiagent.py](examples/fastapi_multiagent.py) | Yes |

### Observability & Tracing

| What you want to do | Example | API Key? |
|---------------------|---------|----------|
| Record and inspect trace events | [tracing_example.py](examples/tracing_example.py) | Yes |
| Trace delegation chains (A → B → C) | [delegation_tracing_example.py](examples/delegation_tracing_example.py) | Yes |
| Full workflow: trace → export → visualize | [visualization_demo.py](examples/visualization_demo.py) | Yes |

```bash
# Run an example
python examples/inheritance_example.py

# FastAPI examples
pip install ".[fastapi]"
python examples/fastapi_example.py
# Visit http://localhost:8000/docs
```

See [examples/README.md](examples/README.md) for detailed descriptions and sample trace files.

---

## Project Structure

```
fractal/
+-- __init__.py              # Public API exports
+-- agent.py                 # BaseAgent - LLM interaction, tool loop, delegation
+-- toolkit.py               # AgentToolkit - tool registration, discovery, execution
+-- models.py                # AgentResult, ToolResult (Pydantic models)
+-- parser.py                # Google-style docstring -> OpenAI tool schema
+-- observability/
    +-- __init__.py           # Exports TracingKit, TraceEvent
    +-- __main__.py           # CLI: fractal {view,visualize}
    +-- tracing.py            # TracingKit, TraceEvent
    +-- terminal_viewer.py    # ASCII terminal visualization
    +-- html_visualizer.py    # Interactive HTML visualization

examples/                     # Working examples (see examples/README.md)
tests/                        # Test suite (see tests/README.md)
docs/                         # Additional documentation
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Planned features and improvements |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Composition pattern and design decisions |
| [docs/ASYNC_SUPPORT.md](docs/ASYNC_SUPPORT.md) | Async/await guide and patterns |
| [docs/MULTIAGENT.md](docs/MULTIAGENT.md) | Multi-agent collaboration patterns |
| [docs/TRACING.md](docs/TRACING.md) | Execution tracing guide |
| [docs/TRACE_VISUALIZATION.md](docs/TRACE_VISUALIZATION.md) | Visualization tools guide |
| [docs/MODEL_SELECTION.md](docs/MODEL_SELECTION.md) | Model selection guide |
| [examples/README.md](examples/README.md) | Examples guide with sample traces |
| [tests/README.md](tests/README.md) | Test suite guide |

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on development setup, code style, and submitting pull requests.

## License

MIT License
