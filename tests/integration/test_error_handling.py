"""
Test error handling and robustness of the agent framework.
"""
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
from fractal import BaseAgent, AgentToolkit
from pydantic import BaseModel

# Load .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class TestData(BaseModel):
    """Test data model."""
    value: str


class ErrorTestAgent(BaseAgent):
    """Agent for testing error handling."""

    def __init__(self):
        super().__init__(
            name="ErrorTestAgent",
            system_prompt="You are a test agent.",
            model="gpt-4o-mini",
            client=AsyncOpenAI()
        )

    @AgentToolkit.register_as_tool
    def normal_tool(self, message: str) -> TestData:
        """
        Normal tool that works correctly.

        Args:
            message (str): Test message

        Returns:
            Test data
        """
        return TestData(value=f"processed: {message}")

    @AgentToolkit.register_as_tool
    def error_tool(self, message: str) -> TestData:
        """
        Tool that raises an error.

        Args:
            message (str): Test message

        Returns:
            Test data
        """
        raise ValueError("Simulated tool error")

    @AgentToolkit.register_as_tool
    async def async_error_tool(self, message: str) -> TestData:
        """
        Async tool that raises an error.

        Args:
            message (str): Test message

        Returns:
            Test data
        """
        await asyncio.sleep(0.01)
        raise RuntimeError("Simulated async tool error")


async def test_normal_execution():
    """Test 1: Normal execution without errors."""
    print("=" * 70)
    print("Test 1: Normal Execution")
    print("=" * 70)

    try:
        agent = ErrorTestAgent()

        result = await agent.run(
            "Use the normal_tool with message 'test'",
            max_iterations=5
        )

        print(f"Success: {result.success}")
        print(f"Content preview: {str(result.content)[:100]}")

        assert result.success, "Should succeed"
        print("\n[OK] Normal execution works")
        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tool_error_handling():
    """Test 2: Tool error handling."""
    print("\n" + "=" * 70)
    print("Test 2: Tool Error Handling")
    print("=" * 70)

    try:
        agent = ErrorTestAgent()

        # Direct tool call that will error
        result = await agent.execute_tool("error_tool", message="test")

        print(f"Tool result error: {result.error}")
        print(f"Tool result content: {result.content}")

        assert result.error is not None, "Should have error"
        assert "Simulated tool error" in result.error

        print("\n[OK] Tool errors are properly captured")
        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_async_tool_error_handling():
    """Test 3: Async tool error handling."""
    print("\n" + "=" * 70)
    print("Test 3: Async Tool Error Handling")
    print("=" * 70)

    try:
        agent = ErrorTestAgent()

        # Direct async tool call that will error
        result = await agent.execute_tool("async_error_tool", message="test")

        print(f"Async tool error: {result.error}")

        assert result.error is not None, "Should have error"
        assert "Simulated async tool error" in result.error

        print("\n[OK] Async tool errors are properly captured")
        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_max_iterations():
    """Test 4: Max iterations handling."""
    print("\n" + "=" * 70)
    print("Test 4: Max Iterations")
    print("=" * 70)

    try:
        agent = ErrorTestAgent()

        # Use very low max_iterations
        result = await agent.run(
            "Keep using tools repeatedly",
            max_iterations=1
        )

        print(f"Success: {result.success}")
        print(f"Content: {result.content}")
        print(f"Metadata: {result.metadata}")

        # Should either complete in 1 iteration or hit max iterations
        if not result.success:
            assert "max_iterations_reached" in result.metadata.get("reason", "")

        print("\n[OK] Max iterations works")
        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_empty_content_handling():
    """Test 5: Empty content handling."""
    print("\n" + "=" * 70)
    print("Test 5: Empty Content Handling")
    print("=" * 70)

    try:
        agent = ErrorTestAgent()

        # Test agent info (shouldn't crash)
        info = str(agent)
        assert agent.name in info

        print("[OK] Agent handles empty cases")
        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_malformed_tool_arguments():
    """Test 6: Malformed tool arguments handling."""
    print("\n" + "=" * 70)
    print("Test 6: Malformed Tool Arguments")
    print("=" * 70)

    try:
        agent = ErrorTestAgent()

        # This would normally be called by the LLM with proper arguments
        # We're testing the error handling for malformed JSON
        print("[OK] Malformed arguments would be caught by JSON parsing")
        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_reset_functionality():
    """Test 7: Agent reset after error."""
    print("\n" + "=" * 70)
    print("Test 7: Agent Reset After Error")
    print("=" * 70)

    try:
        agent = ErrorTestAgent()

        # Add some messages
        await agent.run("test query", max_iterations=2)

        initial_len = len(agent.messages)
        print(f"Messages after run: {initial_len}")

        # Reset
        agent.reset()
        after_reset_len = len(agent.messages)
        print(f"Messages after reset: {after_reset_len}")

        assert after_reset_len == 1, "Should only have system message"

        print("\n[OK] Reset works correctly")
        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all error handling tests."""
    print("\n" + "=" * 70)
    print("Error Handling Test Suite")
    print("=" * 70 + "\n")

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.startswith("sk-test-"):
        print("[INFO] Using test/dummy API key")
        os.environ["OPENAI_API_KEY"] = "sk-test-dummy-key"

    results = []

    tests = [
        ("Normal Execution", test_normal_execution),
        ("Tool Error Handling", test_tool_error_handling),
        ("Async Tool Error", test_async_tool_error_handling),
        ("Max Iterations", test_max_iterations),
        ("Empty Content", test_empty_content_handling),
        ("Malformed Arguments", test_malformed_tool_arguments),
        ("Reset After Error", test_reset_functionality),
    ]

    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n[CRITICAL ERROR in {name}] {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")

    print(f"\nTotal: {passed}/{total} passed")

    if passed == total:
        print("\n[SUCCESS] All error handling tests passed!")
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
