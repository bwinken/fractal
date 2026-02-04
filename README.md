# Fractal

**Self-similar agent decomposition for building complex AI workflows**

Just as fractals create complexity through repeated simple patterns, Fractal creates powerful agent systems through recursive delegation. Build multi-agent pipelines where each agent focuses on one task and delegates the rest.

```
Coordinator
  +-- Researcher     (depth=1)
  |     +-- Analyst  (depth=2)
  +-- Writer         (depth=1)
```

## Features

- **Recursive Delegation** - Agents delegate sub-tasks to other agents, forming tree-shaped workflows
- **OpenAI Compatible** - Works with OpenAI API and any OpenAI-compatible endpoint (Azure, Ollama, LM Studio, etc.)
- **Full Async/Await** - Native async support for FastAPI, asyncio, and concurrent operations
- **Decorator-Based Tools** - Register methods as tools with `@tool` and Google-style docstrings
- **Functional Tool Registration** - Add standalone functions as tools via `agent.add_tool(fn)` — no subclassing required
- **Structured I/O** - Pass `str`, `dict`, `list`, or Pydantic `BaseModel` between agents and tools
- **Built-in Observability** - Delegation-aware tracing with zero extra dependencies; export to JSON Lines, view in terminal or interactive HTML
- **FastAPI Ready** - Drop agents into FastAPI endpoints with lifespan management
- **Composition Architecture** - Agent HAS-A Toolkit (not IS-A), clean separation of concerns

## Requirements

- Python >= 3.9
- openai >= 1.0.0
- pydantic >= 2.0.0
- python-dotenv >= 1.0.0

## Installation

```bash
pip install -e .
```

With FastAPI support:

```bash
pip install -e ".[fastapi]"
```

## Configuration

Fractal reads OpenAI settings from environment variables. You can configure them in two ways:

### Option 1: Environment Variables (recommended for deployment)

```bash
export OPENAI_API_KEY=sk-your-api-key-here

# Optional: custom endpoint (Azure, Ollama, LM Studio, etc.)
export OPENAI_BASE_URL=https://your-api.com/v1

# Optional: default model (used when not specified in code)
export OPENAI_MODEL=gpt-4o-mini
```

### Option 2: `.env` File (recommended for local development)

```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY
```

`.env` file:

```bash
OPENAI_API_KEY=sk-your-api-key-here

# Optional: custom endpoint (Azure, Ollama, etc.)
# OPENAI_BASE_URL=https://your-api.com/v1

# Optional: default model
# OPENAI_MODEL=gpt-4o-mini
```

> **Priority:** Constructor arguments > environment variables > defaults.
> For example, `BaseAgent(model="gpt-4")` always uses `gpt-4` regardless of `OPENAI_MODEL`.

### Supported Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | — |
| `OPENAI_BASE_URL` | Custom API endpoint | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | Default model name | `gpt-4o-mini` |
| `CONTEXT_WINDOW` | Token limit for auto-trimming conversation history | disabled |

## Quick Start

### 1. Define an Agent

Create a custom agent by inheriting `BaseAgent` and decorating methods with `@AgentToolkit.register_as_tool`:

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
    """
    Add two numbers.

    Args:
        a (int): First number
        b (int): Second number

    Returns:
        Sum of a and b
    """
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """
    Multiply two numbers.

    Args:
        a (int): First number
        b (int): Second number

    Returns:
        Product of a and b
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
class Coordinator(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Coordinator",
            system_prompt="Delegate math tasks to the calculator.",
            client=AsyncOpenAI()
        )

coordinator = Coordinator()
math_agent = MathAgent()

# Register MathAgent as a callable tool for Coordinator
coordinator.register_delegate(
    math_agent,
    tool_name="calculate",
    description="Perform math calculations"
)

result = await coordinator.run("Compute (3 + 4) * 5")
```

Delegation can be nested to arbitrary depth (A -> B -> C -> ...). When tracing is enabled on the top-level agent, tracing automatically propagates through the entire delegation chain.

### 4. Execution Tracing

Enable tracing to record every agent start/end, tool call, and delegation event:

```python
coordinator = Coordinator()

# Enable tracing with auto-export
class TracedCoordinator(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Coordinator",
            system_prompt="...",
            client=AsyncOpenAI(),
            enable_tracing=True,
            tracing_output_file="examples/traces/output.jsonl"
        )
```

View traces:

```bash
# Terminal ASCII view
fractal view examples/traces/output.jsonl

# Summary only
fractal view examples/traces/output.jsonl --summary

# Interactive HTML
fractal visualize examples/traces/output.jsonl -o output.html
```

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
tests/                        # Test suite: unit / integration / e2e (see tests/README.md)
docs/                         # Additional documentation
```

## API Reference

### BaseAgent

The main agent class. Handles OpenAI API communication, tool execution loop, and delegation.

```python
agent = BaseAgent(
    name="MyAgent",                    # Agent name (used in tracing)
    system_prompt="You are helpful.",   # System prompt
    model="gpt-4o-mini",               # Falls back to OPENAI_MODEL env var, then "gpt-4o-mini"
    client=AsyncOpenAI(),              # Falls back to OPENAI_API_KEY / OPENAI_BASE_URL env vars
    temperature=0.7,                   # Sampling temperature (0-2)
    max_tokens=None,                   # Max response tokens
    enable_tracing=False,              # Enable execution tracing
    tracing_output_file=None,          # Auto-export trace to this file
    context_window=None                # Token limit for auto-trimming (e.g., 128000)
)
```

**Methods:**

| Method | Description |
|--------|-------------|
| `await run(user_input, max_iterations=10, max_retries=3)` | Run the agent and return `AgentResult` |
| `reset()` | Clear conversation history |
| `add_tool(func, name=None, terminate=False)` | Register a standalone function as a tool |
| `register_delegate(agent, tool_name=None, description=None)` | Register an agent as a delegate tool |
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
        """
        Tool description.

        Args:
            query (str): Search query

        Returns:
            Search result
        """
        return f"Result for: {query}"

    @tool(name="custom_name", terminate=True)
    def final_answer(self, answer: str) -> str:
        """Return final answer and stop the agent loop.

        Args:
            answer (str): The final answer

        Returns:
            The answer
        """
        return answer
```

**Decorator options:**
- `name` - Override the tool name (default: method name)
- `terminate` - If `True`, the agent loop stops after this tool executes

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

    Returns:
        Results
    """
    return str(count)

agent.add_tool(mismatch_tool)
# UserWarning: Tool 'mismatch_tool': parameter 'count' type mismatch —
#   annotation says 'int' (→ integer) but docstring says 'string'.
#   The docstring type will be used in the tool schema.
```

**Other constraints:**
- Type information is read from the **docstring `Args:` section**, not from Python type annotations. Annotations are used for validation only.
- `Optional[str]` is fine — the framework unwraps it to `str`. But `Union[str, int]` is not well supported.
- Default values make a parameter optional (not in `required`), but the default value itself is **not** included in the schema — the LLM won't see it.
- If a parameter is missing from the `Args:` section, the LLM receives an empty description.
- If a function has no docstring at all, the tool description defaults to the function name.

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

```python
from fractal import TracingKit, TraceEvent

kit = TracingKit(output_file="trace.jsonl")
kit.start_agent("MyAgent", user_input="hello")
kit.start_tool_call("MyAgent", "my_tool", {"query": "test"})
kit.end_tool_call("MyAgent", "my_tool", result="done")
kit.end_agent("MyAgent", result="completed")

events: list[TraceEvent] = kit.get_trace()
summary: dict = kit.get_summary()
kit.export_json("trace.jsonl")
```

**TraceEvent fields:** `timestamp`, `event_type`, `agent_name`, `parent_agent`, `delegation_depth`, `tool_name`, `arguments`, `result`, `error`, `elapsed_time`, `metadata`

**Event types:** `agent_start`, `agent_end`, `agent_delegate`, `delegation_end`, `tool_call`, `tool_result`, `error`

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

        Returns:
            Result
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

## Examples

See the [examples/](examples/) directory for complete working examples:

| Example | Description |
|---------|-------------|
| [inheritance_example.py](examples/inheritance_example.py) | Agent inheritance pattern (recommended starting point) |
| [async_example.py](examples/async_example.py) | Async agents with sync/async tools |
| [multiagent_example.py](examples/multiagent_example.py) | Multi-agent delegation patterns |
| [rag_example.py](examples/rag_example.py) | RAG agent with vector search |
| [fastapi_example.py](examples/fastapi_example.py) | FastAPI integration |
| [fastapi_multiagent.py](examples/fastapi_multiagent.py) | FastAPI with multi-agent routing |
| [tracing_example.py](examples/tracing_example.py) | Execution tracing and monitoring |
| [delegation_tracing_example.py](examples/delegation_tracing_example.py) | Delegation-aware tracing |
| [visualization_demo.py](examples/visualization_demo.py) | Trace visualization demo |
| [tool_namespacing_example.py](examples/tool_namespacing_example.py) | Tool namespacing across toolkits |
| [basic_example.py](examples/basic_example.py) | Standalone toolkit pattern |

```bash
# Run an example (most require OPENAI_API_KEY in .env)
python examples/inheritance_example.py

# FastAPI example
pip install -e ".[fastapi]"
python examples/fastapi_example.py
# Visit http://localhost:8000/docs
```

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
| [examples/README.md](examples/README.md) | Examples guide |
| [tests/README.md](tests/README.md) | Test suite guide |

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on development setup, code style, and submitting pull requests.

## License

MIT License
