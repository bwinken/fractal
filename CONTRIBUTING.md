# Contributing to Fractal

Thanks for your interest in contributing! This guide covers the process for submitting changes.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/your-username/fractal.git
cd fractal

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Copy environment config
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY (needed for e2e tests only)
```

## Project Structure

```
fractal/          # Core framework
  agent.py        # BaseAgent - LLM interaction, tool loop, delegation
  toolkit.py      # AgentToolkit - tool registration, discovery, execution
  models.py       # Pydantic models (AgentResult, ToolResult)
  parser.py       # Docstring → OpenAI tool schema
  observability/  # Tracing and visualization
examples/         # Working examples
tests/            # Test suite (unit / integration / e2e)
docs/             # Documentation
```

## Running Tests

```bash
# Unit tests (fast, no API key needed)
python -m pytest tests/unit/ -v

# Integration tests (may use mocks)
python -m pytest tests/integration/ -v

# E2E tests (requires OPENAI_API_KEY, incurs API costs)
python -m pytest tests/e2e/ -v

# All tests with coverage
python -m pytest tests/ --cov=fractal
```

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Code Style

- Follow existing patterns in the codebase
- Use type annotations for function signatures
- Write Google-style docstrings for public methods:

```python
def my_method(self, query: str, limit: int = 10) -> list:
    """Short description of what this does.

    Args:
        query (str): What to search for
        limit (int): Maximum results to return

    Returns:
        List of matching results
    """
```

- Keep methods focused — one method, one responsibility
- Prefer composition over inheritance (agent HAS-A toolkit, not IS-A)

### 3. Write Tests

- Add unit tests for new functionality in `tests/unit/`
- Test edge cases and error conditions
- Tests should be independent and fast (< 1s each for unit tests)
- Mock external dependencies — don't call real APIs in unit/integration tests

### 4. Commit Messages

Use clear, descriptive commit messages:

```
Add context window management for BaseAgent

- Add context_window parameter with env var fallback
- Implement sliding window trimming with atomic tool-call groups
- Add token estimation with tiktoken fallback
```

Format:
- First line: imperative mood, under 72 characters
- Blank line, then details if needed
- Reference issues with `#123` if applicable

### 5. Submit a Pull Request

```bash
git push origin feature/your-feature-name
```

Then open a PR on GitHub with:
- A clear title describing the change
- Description of what and why (not just how)
- Link to any related issues

## What to Contribute

See [docs/ROADMAP.md](docs/ROADMAP.md) for planned features. Other welcome contributions:

- Bug fixes
- New examples demonstrating real-world use cases
- Documentation improvements
- Test coverage improvements
- Performance optimizations

## Guidelines

- **Don't break the public API** — `BaseAgent`, `AgentToolkit`, `tool` / `register_as_tool`, `register_delegate`, `AgentResult`, `ToolResult`, `TracingKit` are all public. Changes to their signatures should be backward compatible.
- **Keep dependencies minimal** — The core framework depends only on `openai`, `pydantic`, and `python-dotenv`. New dependencies should be optional.
- **Test before submitting** — Run `python -m pytest tests/unit/` at minimum.

## Questions?

Open an issue on GitHub if you have questions or want to discuss a larger change before implementing it.
