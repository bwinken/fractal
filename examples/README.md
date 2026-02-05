# Examples

Working examples for the Fractal framework.

---

## Which Example Should I Read?

| I want to... | Start with | API Key? |
|--------------|-----------|----------|
| **Get started quickly** | [inheritance_example.py](inheritance_example.py) | **No** |
| Build an agent without subclassing | [basic_example.py](basic_example.py) | Partial |
| Use dynamic system prompts | [dynamic_prompt_example.py](dynamic_prompt_example.py) | **No** |
| Use async tools or run tools concurrently | [async_example.py](async_example.py) | Yes |
| Have one agent delegate to another | [multiagent_example.py](multiagent_example.py) | Yes |
| Handle agents with the same tool names | [tool_namespacing_example.py](tool_namespacing_example.py) | Yes |
| Build a knowledge Q&A system (RAG) | [rag_example.py](rag_example.py) | Yes |
| Serve an agent as an HTTP API | [fastapi_example.py](fastapi_example.py) | Yes |
| Serve multiple agents behind a router | [fastapi_multiagent.py](fastapi_multiagent.py) | Yes |
| Record and inspect execution traces | [tracing_example.py](tracing_example.py) | Yes |
| Trace across a delegation chain | [delegation_tracing_example.py](delegation_tracing_example.py) | Yes |
| See per-run trace isolation (`{run_id}`) | [multi_run_demo.py](multi_run_demo.py) | **No** |
| See the full trace-to-visualization workflow | [visualization_demo.py](visualization_demo.py) | Yes |

---

## Setup

```bash
# Install the package
pip install .

# Configure API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run your first example (no API key required for tool introspection)
python examples/inheritance_example.py
```

---

## Example Details

### Core Patterns

These examples cover the fundamental ways to create agents and register tools.

#### [inheritance_example.py](inheritance_example.py) -- Start Here

**No API key required** for tool introspection (Example 3).

Demonstrates the class-based pattern: subclass `BaseAgent`, decorate methods with `@AgentToolkit.register_as_tool`, and let the framework discover tools automatically.

- `WeatherAgent` with weather data tools
- `MathAgent` with calculation tools
- Tool schema inspection without calling the LLM

#### [basic_example.py](basic_example.py)

Alternative pattern using standalone `AgentToolkit` and agent-to-agent communication. Shows how to pass Pydantic objects between tools and agents.

- `WeatherToolkit` + `WeatherAgent`
- `TravelToolkit` + `TravelAgent`
- Pydantic object passing (runnable without API key)

#### [async_example.py](async_example.py)

Async agents with mixed sync/async tools. Demonstrates `AsyncOpenAI`, `asyncio` patterns, and performance comparison of sequential vs concurrent operations.

- `AsyncDatabaseAgent` with sync and async tools
- Concurrent tool execution
- Sequential vs concurrent performance comparison

#### [tool_namespacing_example.py](tool_namespacing_example.py)

When multiple agents define tools with the same name (e.g. both have `search`), this example shows three strategies: delegation (recommended), namespace prefixes, and a hybrid approach.

#### [dynamic_prompt_example.py](dynamic_prompt_example.py)

**No API key required.** Demonstrates dynamic system prompts that change between runs.

- **Template substitution**: `{placeholders}` resolved from `system_context` dict
- **Callable prompts**: Functions that generate prompts dynamically
- **Instance method prompts**: OOP pattern for class-based agents
- **FastAPI integration**: Per-request agent creation with user-specific context
- **RAG context injection**: Updating prompts with retrieved documents

---

### Multi-Agent Patterns

These examples show how agents work together through delegation.

#### [multiagent_example.py](multiagent_example.py)

The core delegation pattern: a coordinator agent delegates tasks to specialist agents via `register_delegate()`.

- `ManagerAgent` coordinates `ResearcherAgent` and `WriterAgent`
- Multi-level workflows and concurrent delegation
- Direct agent-to-agent communication

#### [rag_example.py](rag_example.py)

RAG (Retrieval-Augmented Generation) agent with an in-memory vector store. Uses OpenAI embeddings for semantic document search.

- `VectorStore` with cosine similarity
- `RAGAgent` with `search_knowledge()` tool
- Pre-loaded knowledge base about Fractal and Python

---

### Web / API Integration

These examples show how to serve agents over HTTP with FastAPI.

#### [fastapi_example.py](fastapi_example.py)

Single-agent FastAPI server with agent-backed and direct tool endpoints.

```bash
pip install ".[fastapi]"
python examples/fastapi_example.py
# Visit http://localhost:8000/docs
```

- `DataAgent` with search and statistics tools
- `POST /query` for agent queries, `GET /statistics` for direct tool calls
- Interactive Swagger UI

#### [fastapi_multiagent.py](fastapi_multiagent.py)

Multi-agent FastAPI server with a hub-and-spoke router pattern and lifespan management.

- `RouterAgent` delegates to `ResearchAgent`, `AnalysisAgent`, `ReportAgent`
- `POST /query` routes through the coordinator
- `POST /direct/{agent_name}` for targeted queries
- Startup/shutdown lifecycle

---

### Observability & Tracing

These examples show how to record, export, and visualize execution traces.

#### [tracing_example.py](tracing_example.py)

Enable `TracingKit`, run an agent, export the trace to `.jsonl`, and inspect events programmatically.

- In-memory tracing and file export
- Trace summary statistics
- Performance comparison (with vs without tracing)

#### [delegation_tracing_example.py](delegation_tracing_example.py)

Delegation-aware tracing across multi-level agent chains. Shows the "infection pattern" where the top agent's `TracingKit` propagates to all delegates automatically.

- Two-level tracing: Coordinator → DataAnalyst / Researcher
- Three-level tracing: CoordinatorA → ResearcherB → AnalystC
- Event grouping by `delegation_depth`
- Uses `{run_id}` placeholder for per-run trace files

#### [multi_run_demo.py](multi_run_demo.py)

**No API key required.** Demonstrates that each `run()` creates a separate trace file with unique `run_id`. Essential for FastAPI backends where concurrent requests should not mix traces.

- `{run_id}` placeholder in `tracing_output_file`
- Each run creates: `demo_{run_id}.jsonl`
- Shows all events include `run_id` field

#### [visualization_demo.py](visualization_demo.py)

End-to-end workflow: run agents with tracing, export to `.jsonl`, then visualize with the terminal or HTML viewer.

- `OrchestratorAgent` → `CalculatorAgent` + `DataProcessorAgent`
- Generates trace file and HTML visualization

---

## Sample Trace Files

Pre-generated traces in [traces/](traces/) let you try the visualization tools without running examples:

| File | Source | Content |
|------|--------|---------|
| [tracing_example.jsonl](traces/tracing_example.jsonl) | tracing_example.py | Single agent with tool calls |
| [visualization_demo.jsonl](traces/visualization_demo.jsonl) | visualization_demo.py | Multi-agent delegation |
| [delegation_tracing.jsonl](traces/delegation_tracing.jsonl) | delegation_tracing_example.py | Two-level delegation |
| [multi_level_delegation.jsonl](traces/multi_level_delegation.jsonl) | delegation_tracing_example.py | Three-level delegation |

Try them:

```bash
# Terminal view
fractal view examples/traces/visualization_demo.jsonl --flow

# HTML visualization
fractal visualize examples/traces/visualization_demo.jsonl -o examples/visualizations/visualization_demo.html
```

Pre-generated HTML visualizations are in [visualizations/](visualizations/). Open any `.html` file in a browser for interactive exploration.

---

## Directory Structure

```
examples/
+-- inheritance_example.py          # Start here
+-- basic_example.py                # Standalone toolkit pattern
+-- dynamic_prompt_example.py       # Dynamic system prompts
+-- async_example.py                # Async tools and concurrency
+-- tool_namespacing_example.py     # Overlapping tool names
+-- multiagent_example.py           # Multi-agent delegation
+-- rag_example.py                  # RAG with vector search
+-- fastapi_example.py              # Single-agent HTTP server
+-- fastapi_multiagent.py           # Multi-agent HTTP server
+-- tracing_example.py              # Execution tracing
+-- delegation_tracing_example.py   # Delegation-aware tracing
+-- multi_run_demo.py               # Per-run trace isolation
+-- visualization_demo.py           # Trace visualization workflow
+-- traces/                         # Sample .jsonl trace outputs
+-- visualizations/                 # Sample .html visualizations
```
