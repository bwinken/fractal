# Examples

Working examples for the Fractal framework. Each example focuses on ONE concept with comprehensive documentation.

---

## Quick Reference

| I want to... | Example | API Key? |
|--------------|---------|----------|
| **Get started quickly** | [inheritance_example.py](inheritance_example.py) | **No** |
| Use functional tool pattern (`add_tool`) | [basic_example.py](basic_example.py) | No |
| Use dynamic system prompts | [dynamic_prompt_example.py](dynamic_prompt_example.py) | **No** |
| Use async tools | [async_example.py](async_example.py) | No |
| Have agents delegate to each other | [multiagent_example.py](multiagent_example.py) | Optional |
| Handle same tool names | [tool_namespacing_example.py](tool_namespacing_example.py) | No |
| Build RAG system | [rag_example.py](rag_example.py) | Yes |
| Serve agent via HTTP | [fastapi_example.py](fastapi_example.py) | Yes |
| Serve multiple agents via HTTP | [fastapi_multiagent.py](fastapi_multiagent.py) | Yes |
| Enable execution tracing | [tracing_example.py](tracing_example.py) | No |
| Trace delegation chains | [delegation_tracing_example.py](delegation_tracing_example.py) | No |
| Per-run trace isolation | [multi_run_demo.py](multi_run_demo.py) | **No** |
| Visualize traces | [visualization_demo.py](visualization_demo.py) | Optional |

---

## Setup

```bash
# Install the package
pip install .

# Configure API key (optional for many examples)
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run your first example
python examples/inheritance_example.py
```

---

## Core Patterns

### [inheritance_example.py](inheritance_example.py) - Start Here

**No API key required.** The recommended way to build agents.

Demonstrates:
- Subclass `BaseAgent`
- Use `@AgentToolkit.register_as_tool` decorator
- Access instance state in tools
- Inspect tool schemas without LLM

### [basic_example.py](basic_example.py) - Functional Tool Pattern

**No API key required.** Alternative pattern using standalone functions.

Demonstrates:
- Use `@tool` decorator on standalone functions
- Register tools with `agent.add_tool(func)`
- Use `terminate=True` for tools that end the agent loop

### [async_example.py](async_example.py) - Async Tools

**No API key required.** Use async/await with agents.

Demonstrates:
- Use `AsyncOpenAI` client
- Mix sync and async tools
- Concurrent tool execution with `asyncio.gather()`

### [dynamic_prompt_example.py](dynamic_prompt_example.py) - Dynamic Prompts

**No API key required.** Runtime-configurable system prompts.

Demonstrates:
- Template substitution: `{placeholder}` + `system_context`
- Callable prompts: functions that return prompt strings
- Per-user personalization patterns

---

## Multi-Agent Patterns

### [multiagent_example.py](multiagent_example.py) - Delegation

**API key optional.** Multi-agent systems with delegation.

Demonstrates:
- Create coordinator + specialist agents
- Use `register_delegate()` to expose agents as tools
- Tree-shaped delegation workflows

### [tool_namespacing_example.py](tool_namespacing_example.py) - Name Conflicts

**No API key required.** Handle agents with same tool names.

Demonstrates:
- Problem: two agents both have `search` tool
- Solution: use delegation (recommended)
- Each agent's tools stay encapsulated

### [rag_example.py](rag_example.py) - RAG

**Requires API key.** Retrieval-Augmented Generation.

Demonstrates:
- In-memory vector store with cosine similarity
- OpenAI embeddings for semantic search
- RAG agent with `search_knowledge()` tool

---

## Web Integration

### [fastapi_example.py](fastapi_example.py) - Single Agent

**Requires API key.** Serve one agent via FastAPI.

```bash
pip install ".[fastapi]"
python examples/fastapi_example.py
# Visit http://localhost:8000/docs
```

### [fastapi_multiagent.py](fastapi_multiagent.py) - Multi-Agent

**Requires API key.** Serve multiple agents via FastAPI.

Demonstrates:
- Router agent delegates to specialists
- `POST /query` for coordinated queries
- `POST /direct/{agent_name}` for targeted queries

---

## Observability

### [tracing_example.py](tracing_example.py) - Basic Tracing

**No API key required.** Enable execution tracing.

Demonstrates:
- Enable tracing: `enable_tracing=True`
- Get summary: `agent.tracing.get_summary()`
- Export: `agent.tracing.export_json("trace.jsonl")`

### [delegation_tracing_example.py](delegation_tracing_example.py) - Chain Tracing

**No API key required.** Trace entire delegation chains.

Demonstrates:
- Tracing "infects" delegated agents automatically
- Track `parent_agent` and `delegation_depth`
- Use `{run_id}` for per-run isolation

### [multi_run_demo.py](multi_run_demo.py) - Per-Run Isolation

**No API key required.** Each run() gets separate trace file.

Demonstrates:
- `{run_id}` placeholder in trace file path
- Essential for FastAPI with concurrent requests

### [visualization_demo.py](visualization_demo.py) - Visualization

**API key optional.** End-to-end tracing workflow.

```bash
# Terminal view
fractal view examples/traces/visualization_demo.jsonl

# HTML view
fractal visualize examples/traces/visualization_demo.jsonl -o output.html
```

---

## Sample Traces

Pre-generated traces in [traces/](traces/) for trying visualization:

```bash
fractal view examples/traces/tracing_example.jsonl
fractal visualize examples/traces/visualization_demo.jsonl -o output.html
```

---

## Directory Structure

```
examples/
├── inheritance_example.py      # Agent inheritance pattern (START HERE)
├── basic_example.py            # Standalone toolkit pattern
├── async_example.py            # Async tools
├── dynamic_prompt_example.py   # Dynamic system prompts
├── multiagent_example.py       # Multi-agent delegation
├── tool_namespacing_example.py # Handling name conflicts
├── rag_example.py              # RAG with vector search
├── fastapi_example.py          # Single-agent HTTP
├── fastapi_multiagent.py       # Multi-agent HTTP
├── tracing_example.py          # Basic tracing
├── delegation_tracing_example.py # Delegation chain tracing
├── multi_run_demo.py           # Per-run trace isolation
├── visualization_demo.py       # Trace visualization
├── traces/                     # Sample .jsonl traces
└── visualizations/             # Sample .html visualizations
```
