"""
Test script to verify OpenAI client parameter works correctly.
"""
import os
from openai import OpenAI
from fractal import BaseAgent, AgentToolkit
from pydantic import BaseModel

# Set dummy API key for testing (won't make actual API calls)
os.environ["OPENAI_API_KEY"] = "sk-test-dummy-key-for-testing"


class TestResult(BaseModel):
    """Test result model."""
    value: str


class TestAgent(BaseAgent):
    """Test agent with a simple tool."""

    def __init__(self, client=None):
        super().__init__(
            name="TestAgent",
            system_prompt="You are a test agent.",
            model="gpt-4o-mini",
            client=client if client is not None else OpenAI()
        )

    @AgentToolkit.register_as_tool
    def test_tool(self, message: str) -> TestResult:
        """
        A simple test tool.

        Args:
            message (str): Test message

        Returns:
            Test result
        """
        return TestResult(value=f"Received: {message}")


def test_default_client():
    """Test agent with default client."""
    print("Test 1: Agent with default client (client=None)")
    print("-" * 60)
    try:
        agent = TestAgent(client=None)
        print(f"[OK] Agent created: {agent.name}")
        print(f"[OK] Client type: {type(agent.client)}")
        print(f"[OK] Model: {agent.model}")
        print(f"[OK] Tools registered: {list(agent.get_tools().keys())}")
        return True
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_custom_client():
    """Test agent with custom client."""
    print("\nTest 2: Agent with custom client")
    print("-" * 60)
    try:
        # Create custom client
        custom_client = OpenAI()
        agent = TestAgent(client=custom_client)

        # Verify it's using the same client instance
        assert agent.client is custom_client, "Client instance mismatch"

        print(f"[OK] Agent created: {agent.name}")
        print(f"[OK] Client is custom instance: {agent.client is custom_client}")
        print(f"[OK] Model: {agent.model}")
        print(f"[OK] Tools registered: {list(agent.get_tools().keys())}")
        return True
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_agent_info():
    """Test agent info display."""
    print("\nTest 3: Agent info display")
    print("-" * 60)
    try:
        agent = TestAgent()
        print("\nAgent Info:")
        print(agent)
        return True
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Testing OpenAI Client Parameter")
    print("=" * 60 + "\n")

    results = []
    results.append(test_default_client())
    results.append(test_custom_client())
    results.append(test_agent_info())

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Passed: {sum(results)}/{len(results)}")

    if all(results):
        print("\n[OK] All tests passed!")
    else:
        print("\n[ERROR] Some tests failed")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
