"""
Async Agent Example
===================

This example demonstrates how to use async agents with both sync and async tools.
Fractal fully supports asyncio for high-performance concurrent operations.

OVERVIEW
--------
Fractal agents can use both synchronous and asynchronous tools:

- **Sync tools**: Regular Python functions (def)
- **Async tools**: Coroutines (async def)

The framework automatically handles both types seamlessly.

KEY CONCEPTS
------------
1. Use AsyncOpenAI client for async agent operations
2. Tools can be sync (def) or async (async def)
3. Async tools can use await for I/O operations
4. Multiple tool calls execute in parallel automatically

ASYNC VS SYNC
-------------
When LLM requests multiple tools in one response:
- Sequential: Tool A -> Tool B -> Tool C (3s total)
- Parallel: Tool A, B, C together (~1s total)

WHEN TO USE
-----------
- FastAPI or other async web frameworks
- Database operations with async drivers
- HTTP requests to external APIs
- Any I/O-bound operations

To run:
    python examples/async_example.py
"""
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel
from fractal import BaseAgent, AgentToolkit

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Set dummy API key for testing (remove if using real API)
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-key")


# =============================================================================
# Pydantic Models
# =============================================================================

class SearchResult(BaseModel):
    """Search result from database."""
    query: str
    results: list
    count: int


# =============================================================================
# Async Agent with Mixed Tools
# =============================================================================

class DatabaseAgent(BaseAgent):
    """
    Agent demonstrating both sync and async tools.

    This shows:
    - Using AsyncOpenAI client
    - Mixing sync and async tool methods
    - Simulating async I/O operations
    """

    def __init__(self):
        super().__init__(
            name="DatabaseAgent",
            system_prompt="You are a database assistant that can search and query data.",
            model="gpt-4o-mini",
            client=AsyncOpenAI()  # <-- Use AsyncOpenAI for async operations
        )
        # Sample data
        self.data = [
            {"id": 1, "name": "Alice", "age": 30},
            {"id": 2, "name": "Bob", "age": 25},
            {"id": 3, "name": "Charlie", "age": 35},
        ]

    @AgentToolkit.register_as_tool
    def search_by_name(self, name: str) -> SearchResult:
        """
        Search database by name (SYNC tool).

        Args:
            name (str): Name to search for

        Returns:
            Search results
        """
        # Sync operation - runs in thread pool if needed
        results = [r for r in self.data if name.lower() in r["name"].lower()]
        return SearchResult(query=f"name='{name}'", results=results, count=len(results))

    @AgentToolkit.register_as_tool
    async def search_by_age(self, min_age: int) -> SearchResult:
        """
        Search database by minimum age (ASYNC tool).

        Args:
            min_age (int): Minimum age to filter by

        Returns:
            Search results
        """
        # Simulate async database query
        await asyncio.sleep(0.1)
        results = [r for r in self.data if r["age"] >= min_age]
        return SearchResult(query=f"age>={min_age}", results=results, count=len(results))

    @AgentToolkit.register_as_tool
    async def fetch_external_data(self, source: str) -> dict:
        """
        Fetch data from external API (ASYNC tool).

        Args:
            source (str): External data source name

        Returns:
            Data from external source
        """
        # Simulate async HTTP request
        await asyncio.sleep(0.2)
        return {
            "source": source,
            "data": f"Data from {source}",
            "timestamp": "2024-01-01T00:00:00Z"
        }


# =============================================================================
# Main: Demonstrate Async Tools
# =============================================================================

async def main():
    """Run the async agent example."""
    print("=" * 70)
    print("Async Agent Example")
    print("=" * 70)

    # Create async agent
    agent = DatabaseAgent()

    print(f"\nAgent: {agent.name}")
    print(f"Client: AsyncOpenAI")
    print(f"Tools: {list(agent.get_tools().keys())}")

    # 1. Test sync tool
    print("\n[1] Sync Tool (search_by_name)")
    print("-" * 40)
    result = await agent.execute_tool("search_by_name", name="Alice")
    print(f"Result: {result.content.model_dump_json(indent=2)}")

    # 2. Test async tool
    print("\n[2] Async Tool (search_by_age)")
    print("-" * 40)
    result = await agent.execute_tool("search_by_age", min_age=30)
    print(f"Result: {result.content.model_dump_json(indent=2)}")

    # 3. Concurrent execution comparison
    print("\n[3] Performance: Sequential vs Concurrent")
    print("-" * 40)

    import time

    # Sequential execution
    start = time.time()
    await agent.execute_tool("search_by_age", min_age=25)
    await agent.execute_tool("fetch_external_data", source="api_a")
    await agent.execute_tool("fetch_external_data", source="api_b")
    sequential_time = time.time() - start
    print(f"Sequential: {sequential_time:.3f}s")

    # Concurrent execution
    start = time.time()
    await asyncio.gather(
        agent.execute_tool("search_by_age", min_age=25),
        agent.execute_tool("fetch_external_data", source="api_a"),
        agent.execute_tool("fetch_external_data", source="api_b"),
    )
    concurrent_time = time.time() - start
    print(f"Concurrent: {concurrent_time:.3f}s")
    print(f"Speedup: {sequential_time / concurrent_time:.1f}x faster")

    # 4. Run with LLM (requires real API key)
    print("\n[4] Run with LLM")
    print("-" * 40)
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and not api_key.startswith("sk-test"):
        print("Running agent with real API...")
        result = await agent.run("Search for people aged 30 or older")
        print(f"Response: {result.content}")
    else:
        print("Using dummy API key - LLM calls skipped.")
        print("Set real OPENAI_API_KEY to test full agent.")

    print("\n" + "=" * 70)
    print("[OK] Async example completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
