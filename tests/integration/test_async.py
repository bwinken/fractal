"""
Test async functionality of the Fractal framework.
"""
import os
import asyncio
from openai import AsyncOpenAI
from fractal import BaseAgent, AgentToolkit
from pydantic import BaseModel

# Set dummy API key for testing
os.environ["OPENAI_API_KEY"] = "sk-test-dummy-key-for-testing"


class TestData(BaseModel):
    """Test data model."""
    value: str
    count: int


class AsyncTestAgent(BaseAgent):
    """Test agent with both sync and async tools."""

    def __init__(self, client=None):
        super().__init__(
            name="AsyncTestAgent",
            system_prompt="You are a test agent.",
            model="gpt-4o-mini",
            client=client if client is not None else AsyncOpenAI()
        )

    @AgentToolkit.register_as_tool
    def sync_tool(self, message: str) -> TestData:
        """
        Synchronous tool.

        Args:
            message (str): Test message

        Returns:
            Test data
        """
        return TestData(value=f"sync:{message}", count=1)

    @AgentToolkit.register_as_tool
    async def async_tool(self, message: str) -> TestData:
        """
        Asynchronous tool.

        Args:
            message (str): Test message

        Returns:
            Test data
        """
        await asyncio.sleep(0.1)
        return TestData(value=f"async:{message}", count=2)

    @AgentToolkit.register_as_tool
    async def async_list_tool(self) -> list:
        """
        Async tool that returns a list.

        Returns:
            List of test data
        """
        await asyncio.sleep(0.05)
        return ["item1", "item2", "item3"]

    @AgentToolkit.register_as_tool
    async def async_dict_tool(self) -> dict:
        """
        Async tool that returns a dict.

        Returns:
            Dictionary of test data
        """
        await asyncio.sleep(0.05)
        return {"key": "value", "number": 42}


async def test_sync_tool_execution():
    """Test executing sync tools in async context."""
    print("=" * 70)
    print("Test 1: Sync Tool Execution in Async Context")
    print("=" * 70)

    agent = AsyncTestAgent()

    try:
        result = await agent.execute_tool("sync_tool", message="test")
        print(f"Result type: {type(result.content)}")
        print(f"Result: {result.content.model_dump_json(indent=2)}")
        assert result.content.value == "sync:test"
        assert result.content.count == 1
        print("[OK] Sync tool works in async context")
        return True
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


async def test_async_tool_execution():
    """Test executing async tools."""
    print("\n" + "=" * 70)
    print("Test 2: Async Tool Execution")
    print("=" * 70)

    agent = AsyncTestAgent()

    try:
        result = await agent.execute_tool("async_tool", message="test")
        print(f"Result type: {type(result.content)}")
        print(f"Result: {result.content.model_dump_json(indent=2)}")
        assert result.content.value == "async:test"
        assert result.content.count == 2
        print("[OK] Async tool works")
        return True
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


async def test_concurrent_tool_execution():
    """Test concurrent execution of multiple tools."""
    print("\n" + "=" * 70)
    print("Test 3: Concurrent Tool Execution")
    print("=" * 70)

    agent = AsyncTestAgent()

    try:
        import time
        start = time.time()

        # Run 3 async tools concurrently
        results = await asyncio.gather(
            agent.execute_tool("async_tool", message="test1"),
            agent.execute_tool("async_tool", message="test2"),
            agent.execute_tool("async_tool", message="test3"),
        )

        elapsed = time.time() - start

        print(f"Executed 3 async tools in {elapsed:.3f}s")
        print(f"Results: {[r.content.value for r in results]}")

        # With 0.1s sleep each, concurrent should be ~0.1s, sequential would be ~0.3s
        assert elapsed < 0.25, "Concurrent execution should be faster than sequential"
        assert len(results) == 3
        print("[OK] Concurrent execution works")
        return True
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


async def test_async_return_types():
    """Test async tools with different return types."""
    print("\n" + "=" * 70)
    print("Test 4: Async Tools with Different Return Types")
    print("=" * 70)

    agent = AsyncTestAgent()

    results = []

    # Test BaseModel return
    try:
        result = await agent.execute_tool("async_tool", message="test")
        print(f"[1] BaseModel return: {type(result.content)}")
        assert isinstance(result.content, BaseModel)
        print("    [OK] BaseModel")
        results.append(True)
    except Exception as e:
        print(f"    [ERROR] {e}")
        results.append(False)

    # Test list return
    try:
        result = await agent.execute_tool("async_list_tool")
        print(f"[2] List return: {type(result.content)}")
        assert isinstance(result.content, list)
        print("    [OK] List")
        results.append(True)
    except Exception as e:
        print(f"    [ERROR] {e}")
        results.append(False)

    # Test dict return
    try:
        result = await agent.execute_tool("async_dict_tool")
        print(f"[3] Dict return: {type(result.content)}")
        assert isinstance(result.content, dict)
        print("    [OK] Dict")
        results.append(True)
    except Exception as e:
        print(f"    [ERROR] {e}")
        results.append(False)

    return all(results)


async def test_agent_info():
    """Test that agent info works with async agent."""
    print("\n" + "=" * 70)
    print("Test 5: Agent Info Display")
    print("=" * 70)

    try:
        agent = AsyncTestAgent()
        info = str(agent)
        print(info)

        assert "AsyncTestAgent" in info
        assert "gpt-4o-mini" in info
        print("[OK] Agent info works")
        return True
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


async def main():
    """Run all async tests."""
    print("\n" + "=" * 70)
    print("Async Functionality Test Suite")
    print("=" * 70 + "\n")

    results = []

    # Run tests
    results.append(await test_sync_tool_execution())
    results.append(await test_async_tool_execution())
    results.append(await test_concurrent_tool_execution())
    results.append(await test_async_return_types())
    results.append(await test_agent_info())

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Total tests: {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")

    if all(results):
        print("\n[OK] All async tests passed!")
    else:
        print("\n[ERROR] Some async tests failed")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
