# Examples

Working examples for the Fractal framework. Most examples require an `OPENAI_API_KEY` in your `.env` file.

## Getting Started

```bash
# Install the package
pip install -e .

# Configure API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run your first example (no API key required)
python examples/inheritance_example.py
```

## Examples

### Core Patterns

| Example | API Key? | Description |
|---------|----------|-------------|
| [inheritance_example.py](inheritance_example.py) | No | **Start here.** Agent inheritance pattern with tool introspection. Demonstrates `BaseAgent` subclassing and `@AgentToolkit.register_as_tool`. |
| [basic_example.py](basic_example.py) | Yes | Alternative pattern using standalone `AgentToolkit` and agent-to-agent communication. |
| [async_example.py](async_example.py) | Yes | Async agents with both sync and async tools. Shows `AsyncOpenAI` usage and `asyncio` patterns. |
| [tool_namespacing_example.py](tool_namespacing_example.py) | Yes | Multiple toolkits with overlapping method names. Demonstrates namespace resolution. |

### Multi-Agent

| Example | API Key? | Description |
|---------|----------|-------------|
| [multiagent_example.py](multiagent_example.py) | Yes | Multi-agent delegation. Coordinator delegates to specialist agents via `register_delegate()`. |
| [rag_example.py](rag_example.py) | Yes | RAG (Retrieval-Augmented Generation) agent with in-memory vector store and OpenAI embeddings. |
| [fastapi_example.py](fastapi_example.py) | Yes | Single-agent FastAPI server. Requires `pip install -e ".[fastapi]"`. Run, then visit `http://localhost:8000/docs`. |
| [fastapi_multiagent.py](fastapi_multiagent.py) | Yes | Multi-agent FastAPI server with router pattern. Hub agent delegates to specialists with lifespan management. |

### Observability

| Example | API Key? | Description |
|---------|----------|-------------|
| [tracing_example.py](tracing_example.py) | Yes | Enable `TracingKit`, run an agent, export trace to `.jsonl`, and inspect events programmatically. |
| [delegation_tracing_example.py](delegation_tracing_example.py) | Yes | Delegation-aware tracing across multi-level agent chains (A -> B -> C). Shows "infection pattern" where tracing propagates automatically. |
| [visualization_demo.py](visualization_demo.py) | Yes | End-to-end demo: run agents with tracing, export trace, and view with terminal/HTML visualizers. |

## Sample Trace Files

The `traces/` directory contains pre-generated trace outputs so you can try the visualization tools without running the examples:

| File | Source Example | Content |
|------|----------------|---------|
| [traces/tracing_example.jsonl](traces/tracing_example.jsonl) | `tracing_example.py` | Single agent (DataAgent) with tool calls |
| [traces/visualization_demo.jsonl](traces/visualization_demo.jsonl) | `visualization_demo.py` | Multi-agent delegation (Orchestrator -> Calculator, DataProcessor) |
| [traces/delegation_tracing.jsonl](traces/delegation_tracing.jsonl) | `delegation_tracing_example.py` (ex. 1) | Two-level delegation (Coordinator -> DataAnalyst, Researcher) |
| [traces/multi_level_delegation.jsonl](traces/multi_level_delegation.jsonl) | `delegation_tracing_example.py` (ex. 2) | Three-level delegation (CoordinatorA -> ResearcherB -> AnalystC) |

Try them:

```bash
# View a trace in the terminal
python -m fractal.observability view examples/traces/visualization_demo.jsonl --flow

# Generate interactive HTML
python -m fractal.observability visualize examples/traces/visualization_demo.jsonl -o examples/visualizations/visualization_demo.html
```

## Sample Visualizations

The `visualizations/` directory contains pre-generated HTML visualizations:

| File | Source Trace |
|------|-------------|
| [visualizations/visualization_demo.html](visualizations/visualization_demo.html) | `traces/visualization_demo.jsonl` |

Open any `.html` file in a browser for interactive exploration with timeline, hierarchy, and event list views.

## Directory Structure

```
examples/
+-- inheritance_example.py
+-- basic_example.py
+-- async_example.py
+-- tool_namespacing_example.py
+-- multiagent_example.py
+-- rag_example.py
+-- fastapi_example.py
+-- fastapi_multiagent.py
+-- tracing_example.py
+-- delegation_tracing_example.py
+-- visualization_demo.py
+-- traces/                          # Sample .jsonl trace outputs
|   +-- tracing_example.jsonl
|   +-- visualization_demo.jsonl
|   +-- delegation_tracing.jsonl
|   +-- multi_level_delegation.jsonl
+-- visualizations/                  # Sample .html visualizations
    +-- visualization_demo.html
```
