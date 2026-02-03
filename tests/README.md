# Tests

Test suite for Fractal framework, organized by test type.

## Structure

```
tests/
├── unit/              # Unit tests - Test individual components
│   ├── test_content_types.py      # Content type handling tests
│   └── test_delegate_schema.py    # Delegation schema tests
├── integration/       # Integration tests - Test component interactions
│   ├── test_async.py              # Async functionality tests
│   ├── test_client.py             # Client integration tests
│   ├── test_delegation_tracing.py # Delegation + tracing integration
│   └── test_error_handling.py     # Error handling across components
└── e2e/              # End-to-end tests - Test with real APIs
    └── test_real_api.py          # Real OpenAI API tests
```

## Running Tests

### All Tests
```bash
# Run all tests
python -m pytest tests/

# With coverage
python -m pytest tests/ --cov=fractal
```

### By Category

**Unit Tests** (fast, no external dependencies):
```bash
python -m pytest tests/unit/
```

**Integration Tests** (medium speed, may use mocks):
```bash
python -m pytest tests/integration/
```

**E2E Tests** (slow, requires API key):
```bash
# Requires OPENAI_API_KEY in .env
python -m pytest tests/e2e/
```

### Individual Tests

```bash
# Run specific test file
python tests/unit/test_content_types.py

# Run specific test function
python -m pytest tests/unit/test_content_types.py::test_function_name
```

## Test Categories

### Unit Tests

Test individual components in isolation:
- **test_content_types.py**: Tests Pydantic models, AgentReturnPart, ToolReturnPart
- **test_delegate_schema.py**: Tests tool schema generation for delegated agents

**Characteristics**:
- Fast execution (< 1s each)
- No external dependencies
- No network calls
- Pure logic testing

### Integration Tests

Test how components work together:
- **test_async.py**: Tests async agent execution and tool calling
- **test_client.py**: Tests OpenAI client integration
- **test_delegation_tracing.py**: Tests delegation + tracing interaction
- **test_error_handling.py**: Tests error propagation across components

**Characteristics**:
- Medium execution time
- May use mocked APIs
- Test component interactions
- Test data flow

### E2E Tests

Test complete workflows with real APIs:
- **test_real_api.py**: Tests with real OpenAI API calls

**Characteristics**:
- Slow execution (API calls)
- Requires API credentials
- Tests real-world scenarios
- May incur costs

## Writing Tests

### Test Naming Convention

```python
# Good test names
def test_agent_delegates_to_specialist()
def test_tracing_records_delegation_depth()
def test_error_propagates_through_chain()

# Bad test names
def test_1()
def test_feature()
def test_stuff()
```

### Test Structure

```python
import pytest
from fractal import BaseAgent, TracingKit

class TestDelegation:
    """Test delegation functionality."""

    def test_basic_delegation(self):
        """Test that agent can delegate to another agent."""
        # Arrange
        specialist = SpecialistAgent()
        coordinator = CoordinatorAgent()
        coordinator.register_delegate(specialist)

        # Act
        result = await coordinator.run("task")

        # Assert
        assert result.success
        assert "specialist" in result.content
```

### Fixtures

Common test fixtures should go in `conftest.py`:

```python
# tests/conftest.py
import pytest
from fractal import BaseAgent

@pytest.fixture
def basic_agent():
    """Create a basic test agent."""
    return BaseAgent(
        name="TestAgent",
        system_prompt="You are helpful.",
        model="gpt-4o-mini"
    )
```

## Test Guidelines

1. **Isolation**: Each test should be independent
2. **Speed**: Unit tests should be fast (<1s)
3. **Coverage**: Aim for >80% code coverage
4. **Documentation**: Add docstrings to complex tests
5. **Cleanup**: Clean up resources (files, connections)
6. **Mocking**: Mock external dependencies in unit/integration tests
7. **Real APIs**: Only use real APIs in e2e tests

## Continuous Integration

Tests run automatically on:
- Every commit
- Pull requests
- Before releases

**CI Test Order**:
1. Unit tests (required to pass)
2. Integration tests (required to pass)
3. E2E tests (optional, may be skipped)

## Coverage

Generate coverage report:

```bash
# HTML report
python -m pytest tests/ --cov=fractal --cov-report=html

# Terminal report
python -m pytest tests/ --cov=fractal --cov-report=term
```

View coverage:
```bash
open htmlcov/index.html  # Mac
start htmlcov/index.html # Windows
```

## Debugging Tests

```bash
# Run with verbose output
python -m pytest tests/ -v

# Run with print statements
python -m pytest tests/ -s

# Drop into debugger on failure
python -m pytest tests/ --pdb

# Run only failed tests from last run
python -m pytest tests/ --lf
```

## Setup

Install test dependencies:

```bash
pip install pytest pytest-cov pytest-asyncio
```

## Best Practices

- ✅ Write tests before fixing bugs
- ✅ Test edge cases
- ✅ Test error conditions
- ✅ Keep tests simple and readable
- ✅ Use descriptive test names
- ✅ Mock external dependencies
- ✅ Clean up test artifacts
- ❌ Don't test implementation details
- ❌ Don't make tests depend on each other
- ❌ Don't skip tests without good reason
