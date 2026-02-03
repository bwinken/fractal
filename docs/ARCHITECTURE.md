# Architecture Overview

## Design Pattern: Composition over Inheritance

The framework uses **composition pattern** for the relationship between `BaseAgent` and `AgentToolkit`.

### Before (Inheritance)
```python
class BaseAgent(AgentToolkit):
    """Agent IS-A Toolkit"""
    pass
```

### After (Composition)
```python
class BaseAgent:
    """Agent HAS-A Toolkit"""
    def __init__(self, ...):
        self.toolkit = AgentToolkit(target=self)
```

## Benefits

1. **Separation of Concerns**
   - `AgentToolkit`: Manages tools, tool discovery, and tool execution
   - `BaseAgent`: Manages LLM interaction, conversation history, and agent logic

2. **Flexibility**
   - Toolkit can be used standalone or with an agent
   - Easier to test components independently
   - Clear ownership of responsibilities

3. **Better Design**
   - Follows composition over inheritance principle
   - Agent "has a" toolkit rather than "is a" toolkit
   - More intuitive conceptual model

## API Compatibility

The `BaseAgent` provides delegation methods for backward compatibility:

```python
# These methods delegate to self.toolkit
agent.get_tools()           # -> self.toolkit.get_tools()
agent.execute_tool(...)     # -> self.toolkit.execute_tool(...)
agent.register_delegate(...) # -> self.toolkit.register_delegate(...)
agent.get_tool_schemas()    # -> self.toolkit.get_tool_schemas()
```

## Usage (Unchanged)

```python
class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="MyAgent",
            system_prompt="You are helpful."
        )

    @AgentToolkit.register_as_tool
    def my_tool(self, query: str) -> str:
        """My custom tool."""
        return f"Result: {query}"

# Works exactly the same
agent = MyAgent()
tools = agent.get_tools()  # Delegation method
result = await agent.execute_tool("my_tool", query="test")
```

## Internal Details

### AgentToolkit
- Can be instantiated with optional `target` parameter
- If `target` is provided, automatically discovers tools from target
- `_discover_tools()` scans target (or self) for decorated methods

### BaseAgent
- Creates `self.toolkit = AgentToolkit(target=self)`
- Toolkit discovers agent's `@AgentToolkit.register_as_tool` methods
- Provides convenience methods that delegate to toolkit

## Advanced Usage

For advanced scenarios (like namespacing), you can access the toolkit directly:

```python
# Access internal toolkit
agent.toolkit._tools  # Direct access (not recommended)
agent.toolkit._tool_schemas

# Better: Use public API
agent.get_tools()
agent.get_tool_schemas()
```
