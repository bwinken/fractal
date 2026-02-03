"""
Async example demonstrating async agent operations.

This example shows how to use async agents with both sync and async tools.
Perfect for integrating with FastAPI and other async frameworks.
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

# Set dummy API key for testing (comment out if using real API)
os.environ["OPENAI_API_KEY"] = "sk-test-dummy-key-for-testing"


class DatabaseResult(BaseModel):
    """Database query result."""
    query: str
    results: list
    count: int


class AsyncDatabaseAgent(BaseAgent):
    """Agent with both sync and async tools."""

    def __init__(self, client=None):
        super().__init__(
            name="AsyncDatabaseAgent",
            system_prompt="You are a database assistant that can perform queries.",
            model="gpt-4o-mini",
            client=client if client is not None else AsyncOpenAI()
        )
        self.data = [
            {"id": 1, "name": "Alice", "age": 30},
            {"id": 2, "name": "Bob", "age": 25},
            {"id": 3, "name": "Charlie", "age": 35},
        ]

    @AgentToolkit.register_as_tool
    def search_sync(self, name: str) -> DatabaseResult:
        """
        Synchronous database search.

        Args:
            name (str): Name to search for

        Returns:
            Search results
        """
        results = [item for item in self.data if name.lower() in item["name"].lower()]
        return DatabaseResult(
            query=f"search for '{name}'",
            results=results,
            count=len(results)
        )

    @AgentToolkit.register_as_tool
    async def search_async(self, min_age: int) -> DatabaseResult:
        """
        Asynchronous database search (simulates async I/O).

        Args:
            min_age (int): Minimum age filter

        Returns:
            Search results
        """
        # Simulate async I/O operation
        await asyncio.sleep(0.1)

        results = [item for item in self.data if item["age"] >= min_age]
        return DatabaseResult(
            query=f"age >= {min_age}",
            results=results,
            count=len(results)
        )

    @AgentToolkit.register_as_tool
    async def fetch_external_data(self, source: str) -> dict:
        """
        Fetch data from external source (async).

        Args:
            source (str): Data source name

        Returns:
            External data
        """
        # Simulate async API call
        await asyncio.sleep(0.2)

        return {
            "source": source,
            "data": f"External data from {source}",
            "timestamp": "2024-01-01T00:00:00Z"
        }

    @AgentToolkit.register_as_tool
    def list_sources(self) -> list:
        """
        List available data sources.

        Returns:
            List of source names
        """
        return ["source_a", "source_b", "source_c"]


async def example_async_tools():
    """Example: Using both sync and async tools."""
    print("=" * 70)
    print("Example 1: Async Agent with Mixed Tools")
    print("=" * 70)

    # Create async agent
    agent = AsyncDatabaseAgent()

    print(f"\nAgent: {agent.name}")
    print(f"Registered tools: {list(agent.get_tools().keys())}")

    # Test sync tool
    print("\n[1] Testing sync tool (search_sync):")
    result = await agent.execute_tool("search_sync", name="Alice")
    print(f"Result: {result.content.model_dump_json(indent=2)}")

    # Test async tool
    print("\n[2] Testing async tool (search_async):")
    result = await agent.execute_tool("search_async", min_age=30)
    print(f"Result: {result.content.model_dump_json(indent=2)}")

    # Test another async tool
    print("\n[3] Testing async tool (fetch_external_data):")
    result = await agent.execute_tool("fetch_external_data", source="source_a")
    print(f"Result: {result.content}")

    print("\n" + "=" * 70)


async def example_concurrent_operations():
    """Example: Running multiple operations concurrently."""
    print("\nExample 2: Concurrent Async Operations")
    print("=" * 70)

    agent = AsyncDatabaseAgent()

    print("\nRunning 3 async operations concurrently:")

    # Run multiple async operations concurrently
    tasks = [
        agent.execute_tool("search_async", min_age=25),
        agent.execute_tool("fetch_external_data", source="source_a"),
        agent.execute_tool("fetch_external_data", source="source_b"),
    ]

    # Wait for all to complete
    results = await asyncio.gather(*tasks)

    for i, result in enumerate(results, 1):
        print(f"\n[{i}] {result.tool_name}:")
        if isinstance(result.content, BaseModel):
            print(result.content.model_dump_json(indent=2))
        else:
            print(result.content)

    print("\n" + "=" * 70)


async def example_agent_to_agent():
    """Example: Async agent-to-agent communication."""
    print("\nExample 3: Async Agent-to-Agent Communication")
    print("=" * 70)

    # Create two agents
    agent1 = AsyncDatabaseAgent()
    agent1.name = "Agent1"

    agent2 = AsyncDatabaseAgent()
    agent2.name = "Agent2"

    print(f"\nAgent 1: {agent1.name}")
    print(f"Agent 2: {agent2.name}")

    # Agent 1 calls Agent 2
    print("\nAgent1 calling Agent2...")
    result = await agent1.call_agent(agent2, "List available sources")

    print(f"\nResponse from Agent2:")
    print(f"Success: {result.success}")
    print(f"Content: {result.content}")

    print("\n" + "=" * 70)


async def example_performance_comparison():
    """Example: Compare sync vs async performance."""
    print("\nExample 4: Performance Comparison (Sync vs Async)")
    print("=" * 70)

    agent = AsyncDatabaseAgent()

    # Sequential async calls
    print("\n[1] Sequential async calls:")
    import time
    start = time.time()
    await agent.execute_tool("search_async", min_age=25)
    await agent.execute_tool("search_async", min_age=30)
    await agent.execute_tool("search_async", min_age=35)
    sequential_time = time.time() - start
    print(f"Time: {sequential_time:.3f}s")

    # Concurrent async calls
    print("\n[2] Concurrent async calls:")
    start = time.time()
    await asyncio.gather(
        agent.execute_tool("search_async", min_age=25),
        agent.execute_tool("search_async", min_age=30),
        agent.execute_tool("search_async", min_age=35),
    )
    concurrent_time = time.time() - start
    print(f"Time: {concurrent_time:.3f}s")

    print(f"\nSpeedup: {sequential_time / concurrent_time:.2f}x faster")

    print("\n" + "=" * 70)


async def main():
    """Run all async examples."""
    print("\n" + "=" * 70)
    print("Async Agent Examples")
    print("=" * 70 + "\n")

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY not set.")
        print("Using dummy API key for testing.\n")

    try:
        await example_async_tools()
        print("\n[OK] Async tools example completed!\n")
    except Exception as e:
        print(f"\n[ERROR] Error in async tools example: {e}\n")

    try:
        await example_concurrent_operations()
        print("\n[OK] Concurrent operations example completed!\n")
    except Exception as e:
        print(f"\n[ERROR] Error in concurrent example: {e}\n")

    try:
        await example_agent_to_agent()
        print("\n[OK] Agent-to-agent example completed!\n")
    except Exception as e:
        print(f"\n[ERROR] Error in agent-to-agent example: {e}\n")

    try:
        await example_performance_comparison()
        print("\n[OK] Performance comparison completed!\n")
    except Exception as e:
        print(f"\n[ERROR] Error in performance comparison: {e}\n")


if __name__ == "__main__":
    # Run async main
    asyncio.run(main())
