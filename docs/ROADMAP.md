# Roadmap

Planned improvements for the Fractal framework.

## Features

- [ ] **Streaming Support** - Add `run_stream()` method for token-by-token output, useful for real-time UIs and FastAPI `StreamingResponse`
- [ ] **Parallel Tool Execution** - When the LLM returns multiple tool calls in one response, execute them concurrently with `asyncio.gather` instead of sequentially
- [ ] **Structured Output** - Support OpenAI's `response_format={"type": "json_schema", ...}` so agents can return validated Pydantic models directly
- [x] **Context Window Management** - Automatically trim old conversation history when approaching token limits

## Engineering

- [ ] **GitHub Actions CI** - Automated unit + integration tests on every PR
- [ ] **PyPI Publishing** - `pip install fractal-agent` without cloning the repo
- [ ] **py.typed + mypy** - Type checking support for better developer experience

## Documentation

- [x] **CONTRIBUTING.md** - Contribution guidelines (PR flow, code style, commit conventions)
- [ ] **More Examples** - Real-world patterns: RAG agent, code generation agent, multi-step research agent
