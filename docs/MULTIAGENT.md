# Multi-Agent Collaboration Guide

This guide explains how to build multi-agent systems where agents can collaborate and delegate tasks to each other.

## Overview

The framework supports multi-agent collaboration through:
1. **Agent Registration** - Register other agents as callable tools
2. **Delegation** - Agents can delegate tasks to specialists
3. **Coordination** - Main agent coordinates multiple specialists
4. **FastAPI Integration** - Lifecycle management for production

## Quick Start

### Basic Agent Delegation

```python
from fractal import BaseAgent, AgentToolkit

# Create specialist agent
class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Researcher",
            system_prompt="You gather information."
        )

    @AgentToolkit.register_as_tool
    def search(self, query: str) -> dict:
        """Search for information."""
        return {"results": f"Info about {query}"}

# Create coordinator agent
class ManagerAgent(BaseAgent):
    def __init__(self, research_agent):
        super().__init__(
            name="Manager",
            system_prompt="You coordinate tasks."
        )

        # Register researcher as a subordinate/delegate
        self.register_delegate(
            research_agent,
            tool_name="ask_researcher",
            description="Delegate research to specialist"
        )

# Use
researcher = ResearchAgent()
manager = ManagerAgent(researcher)

# Manager can now delegate to researcher
result = await manager.run("Research AI trends and summarize")
```

## Delegation API

### `register_delegate(agent, tool_name, description)`

Register a subordinate agent for task delegation.

**Parameters:**
- `agent` (BaseAgent): The subordinate agent to register for delegation
- `tool_name` (str, optional): Name for the tool (default: "delegate_to_{agent_name}")
- `description` (str, optional): Tool description for LLM

**Example:**
```python
class CoordinatorAgent(BaseAgent):
    def __init__(self, specialist_a, specialist_b):
        super().__init__(
            name="Coordinator",
            system_prompt="You coordinate specialists."
        )

        # Register Specialist A as delegate
        self.register_delegate(
            specialist_a,
            tool_name="ask_specialist_a",
            description="Delegate to Specialist A for task X"
        )

        # Register Specialist B as delegate
        self.register_delegate(
            specialist_b,
            tool_name="ask_specialist_b",
            description="Delegate to Specialist B for task Y"
        )
```

## Architecture Patterns

### 1. Hub-and-Spoke (Router Pattern)

One main agent delegates to multiple specialists.

```python
class RouterAgent(BaseAgent):
    """Main coordinator that routes to specialists."""

    def __init__(self, research, analysis, writing):
        super().__init__(
            name="Router",
            system_prompt="Route tasks to appropriate specialists."
        )

        self.register_delegate(research, "use_research")
        self.register_delegate(analysis, "use_analysis")
        self.register_delegate(writing, "use_writing")

# Usage
research = ResearchAgent()
analysis = AnalysisAgent()
writing = WritingAgent()

router = RouterAgent(research, analysis, writing)

# Router intelligently delegates
result = await router.run(
    "Research AI, analyze trends, write summary"
)
```

### 2. Pipeline Pattern

Agents pass results sequentially.

```python
async def pipeline(input_data):
    # Step 1: Research
    research_agent = ResearchAgent()
    research_result = await research_agent.run(
        f"Research: {input_data}"
    )

    # Step 2: Analysis
    analysis_agent = AnalysisAgent()
    analysis_result = await analysis_agent.run(
        f"Analyze: {research_result.content}"
    )

    # Step 3: Report
    report_agent = ReportAgent()
    final_result = await report_agent.run(
        f"Create report: {analysis_result.content}"
    )

    return final_result
```

### 3. Peer-to-Peer Pattern

Agents collaborate directly with each other.

```python
class CollaborativeAgent(BaseAgent):
    def __init__(self, peer_agents: list):
        super().__init__(
            name="Collaborator",
            system_prompt="Collaborate with peers."
        )

        # Register all peers as delegates
        for peer in peer_agents:
            self.register_delegate(
                peer,
                tool_name=f"ask_{peer.name.lower()}"
            )
```

## FastAPI Integration

### Lifespan Management

Initialize agents once at startup:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

# Global agent storage
agents = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize multi-agent system on startup."""

    # Create specialist agents
    research = ResearchAgent()
    analysis = AnalysisAgent()
    writing = WritingAgent()

    # Create coordinator
    coordinator = CoordinatorAgent(
        research_agent=research,
        analysis_agent=analysis,
        writing_agent=writing
    )

    # Store in global dict
    agents['coordinator'] = coordinator
    agents['research'] = research
    agents['analysis'] = analysis
    agents['writing'] = writing

    print(f"✅ Initialized {len(agents)} agents")

    yield

    # Cleanup
    print("🛑 Shutting down agents")

app = FastAPI(lifespan=lifespan)

@app.post("/query")
async def query_endpoint(query: str):
    """Route query through coordinator."""
    coordinator = agents['coordinator']
    result = await coordinator.run(query)
    return {"response": result.content}
```

### Direct Agent Access

Provide endpoints for direct agent access:

```python
@app.post("/agent/{agent_name}")
async def direct_agent(agent_name: str, query: str):
    """Query specific agent directly."""
    if agent_name not in agents:
        raise HTTPException(404, f"Agent not found: {agent_name}")

    agent = agents[agent_name]
    result = await agent.run(query)
    return {
        "agent": agent.name,
        "response": result.content
    }
```

## Advanced Features

### 1. Concurrent Delegation

Execute multiple delegations in parallel:

```python
class ParallelCoordinator(BaseAgent):
    async def delegate_parallel(self, tasks: list):
        """Delegate multiple tasks concurrently."""
        results = await asyncio.gather(*[
            self.agents[agent_name].run(task)
            for agent_name, task in tasks
        ])
        return results
```

### 2. Custom Delegation Logic

Add custom logic in delegation tools:

```python
class SmartCoordinator(BaseAgent):
    def __init__(self, specialists):
        super().__init__(...)

        self.specialists = specialists

        # Don't just register - add custom tool
        @AgentToolkit.register_as_tool
        async def smart_delegate(query: str) -> str:
            """
            Smart delegation with routing logic.

            Args:
                query: Query to delegate

            Returns:
                Result from best specialist
            """
            # Custom routing logic
            if "research" in query.lower():
                agent = self.specialists['research']
            elif "analyze" in query.lower():
                agent = self.specialists['analysis']
            else:
                agent = self.specialists['general']

            result = await agent.run(query)
            return result.content
```

### 3. Agent Context Sharing

Share context between agents:

```python
class ContextAwareCoordinator(BaseAgent):
    def __init__(self):
        super().__init__(...)
        self.shared_context = {}

    async def delegate_with_context(self, agent, query, context_key):
        """Delegate with shared context."""
        # Add context to query
        context = self.shared_context.get(context_key, "")
        full_query = f"Context: {context}\n\nQuery: {query}"

        result = await agent.run(full_query)

        # Update shared context
        self.shared_context[context_key] = result.content

        return result
```

## Best Practices

### 1. Clear Role Definition

Each agent should have a clear, specific role:

```python
ResearchAgent - "You gather and organize information"
AnalysisAgent - "You analyze data and provide insights"
WritingAgent - "You create clear, formatted content"
CoordinatorAgent - "You delegate to specialists efficiently"
```

### 2. Tool Naming

Use descriptive names for delegation tools:

```python
# Good
self.register_delegate(research, "delegate_to_research")
self.register_delegate(analysis, "delegate_to_analysis")

# Bad
self.register_delegate(research, "tool1")
self.register_delegate(analysis, "agent2")
```

### 3. Error Handling

Handle delegation failures gracefully:

```python
@AgentToolkit.register_as_tool
async def safe_delegate(query: str) -> str:
    """Delegate with error handling."""
    try:
        result = await self.specialist.run(query)
        if not result.success:
            return f"Delegation failed: {result.metadata.get('error')}"
        return result.content
    except Exception as e:
        return f"Error in delegation: {str(e)}"
```

### 4. Resource Management

Reuse agent instances, don't create new ones per request:

```python
# Good - Create once at startup
@asynccontextmanager
async def lifespan(app):
    agents['specialist'] = SpecialistAgent()  # Reused
    yield

# Bad - Create per request
@app.post("/query")
async def query(q: str):
    agent = SpecialistAgent()  # Don't do this!
    return await agent.run(q)
```

## Example: Complete Multi-Agent System

See [examples/fastapi_multiagent.py](../examples/fastapi_multiagent.py) for a complete working example with:
- Router agent coordinating 3 specialists
- FastAPI lifespan management
- Direct and delegated access patterns
- Error handling
- API documentation

Run it with:
```bash
pip install fastapi uvicorn
python examples/fastapi_multiagent.py
```

Visit http://localhost:8000/docs for interactive API.

## Testing Multi-Agent Systems

### Unit Testing Individual Agents

```python
@pytest.mark.asyncio
async def test_specialist_agent():
    agent = ResearchAgent()
    result = await agent.run("Test query")
    assert result.success
```

### Integration Testing Delegation

```python
@pytest.mark.asyncio
async def test_delegation():
    specialist = SpecialistAgent()
    coordinator = CoordinatorAgent(specialist)

    result = await coordinator.run("Delegate to specialist")
    assert "specialist" in result.metadata
```

### Testing Concurrent Operations

```python
@pytest.mark.asyncio
async def test_concurrent_delegation():
    coordinator = MultiAgentCoordinator()

    tasks = [
        coordinator.run("task 1"),
        coordinator.run("task 2"),
        coordinator.run("task 3")
    ]

    results = await asyncio.gather(*tasks)
    assert all(r.success for r in results)
```

## Troubleshooting

### Agent Not Found in Tools

**Problem:** Registered agent doesn't appear in tools list

**Solution:** Make sure to register after calling `super().__init__()`:

```python
def __init__(self, specialist):
    super().__init__(...)  # First
    self.register_delegate(specialist)  # Then register delegate
```

### Circular Dependencies

**Problem:** Agent A needs Agent B, Agent B needs Agent A

**Solution:** Use lazy registration or coordinator pattern:

```python
class CoordinatorAgent(BaseAgent):
    def __init__(self):
        super().__init__(...)

        # Create both agents first
        self.agent_a = AgentA()
        self.agent_b = AgentB()

        # Then register as delegates
        self.register_delegate(self.agent_a)
        self.register_delegate(self.agent_b)
```

### Memory Accumulation

**Problem:** Message history grows too large

**Solution:** Reset agent state periodically:

```python
# After processing
agent.reset()  # Clears message history
```

## Summary

Multi-agent collaboration enables:
- ✅ Specialized agents for different tasks
- ✅ Intelligent task routing and coordination
- ✅ Scalable FastAPI integration
- ✅ Concurrent processing
- ✅ Clean separation of concerns

The `register_delegate()` API makes it simple to build complex multi-agent systems with clear delegation hierarchies!
