"""
Test script to verify all content types are handled correctly.
Tests: str, dict, list, BaseModel, list of BaseModel
"""
import os
import json
from openai import OpenAI
from fractal import BaseAgent, AgentToolkit, ToolResult
from pydantic import BaseModel

# Set dummy API key for testing
os.environ["OPENAI_API_KEY"] = "sk-test-dummy-key-for-testing"


class PersonData(BaseModel):
    """Person data model."""
    name: str
    age: int


class TestTypesAgent(BaseAgent):
    """Test agent with tools that return different types."""

    def __init__(self, client=None):
        super().__init__(
            name="TestTypesAgent",
            system_prompt="You are a test agent.",
            model="gpt-4o-mini",
            client=client if client is not None else OpenAI()
        )

    @AgentToolkit.register_as_tool
    def return_string(self) -> str:
        """
        Return a simple string.

        Returns:
            A test string
        """
        return "Hello, World!"

    @AgentToolkit.register_as_tool
    def return_dict(self) -> dict:
        """
        Return a dictionary.

        Returns:
            A test dictionary
        """
        return {"key": "value", "number": 42, "nested": {"data": "test"}}

    @AgentToolkit.register_as_tool
    def return_list(self) -> list:
        """
        Return a list of primitives.

        Returns:
            A test list
        """
        return ["item1", "item2", "item3", 123, True]

    @AgentToolkit.register_as_tool
    def return_basemodel(self) -> PersonData:
        """
        Return a Pydantic BaseModel.

        Returns:
            A test PersonData object
        """
        return PersonData(name="Alice", age=30)

    @AgentToolkit.register_as_tool
    def return_list_of_basemodels(self) -> list:
        """
        Return a list of Pydantic BaseModels.

        Returns:
            A test list of PersonData objects
        """
        return [
            PersonData(name="Alice", age=30),
            PersonData(name="Bob", age=25),
            PersonData(name="Charlie", age=35)
        ]

    @AgentToolkit.register_as_tool
    def return_empty_list(self) -> list:
        """
        Return an empty list.

        Returns:
            An empty list
        """
        return []


async def test_tool_return_types():
    """Test that all tool return types are handled correctly."""
    print("=" * 70)
    print("Testing Tool Return Types")
    print("=" * 70)

    agent = TestTypesAgent()
    toolkit = agent  # Agent has toolkit methods via delegation

    results = []

    # Test 1: String return
    print("\nTest 1: Tool returns string")
    print("-" * 70)
    try:
        result = await toolkit.execute_tool("return_string")
        print(f"Result type: {type(result.content)}")
        print(f"Result content: {result.content}")
        assert isinstance(result.content, str), "Content should be str"
        assert result.content == "Hello, World!"
        print("[OK] String return works")
        results.append(True)
    except Exception as e:
        print(f"[ERROR] {e}")
        results.append(False)

    # Test 2: Dict return
    print("\nTest 2: Tool returns dict")
    print("-" * 70)
    try:
        result = await toolkit.execute_tool("return_dict")
        print(f"Result type: {type(result.content)}")
        print(f"Result content: {json.dumps(result.content, indent=2)}")
        assert isinstance(result.content, dict), "Content should be dict"
        assert result.content["key"] == "value"
        print("[OK] Dict return works")
        results.append(True)
    except Exception as e:
        print(f"[ERROR] {e}")
        results.append(False)

    # Test 3: List return
    print("\nTest 3: Tool returns list")
    print("-" * 70)
    try:
        result = await toolkit.execute_tool("return_list")
        print(f"Result type: {type(result.content)}")
        print(f"Result content: {json.dumps(result.content, indent=2)}")
        assert isinstance(result.content, list), "Content should be list"
        assert len(result.content) == 5
        print("[OK] List return works")
        results.append(True)
    except Exception as e:
        print(f"[ERROR] {e}")
        results.append(False)

    # Test 4: BaseModel return
    print("\nTest 4: Tool returns BaseModel")
    print("-" * 70)
    try:
        result = await toolkit.execute_tool("return_basemodel")
        print(f"Result type: {type(result.content)}")
        print(f"Result content: {result.content.model_dump_json(indent=2)}")
        assert isinstance(result.content, BaseModel), "Content should be BaseModel"
        assert result.content.name == "Alice"
        print("[OK] BaseModel return works")
        results.append(True)
    except Exception as e:
        print(f"[ERROR] {e}")
        results.append(False)

    # Test 5: List of BaseModels return
    print("\nTest 5: Tool returns list of BaseModels")
    print("-" * 70)
    try:
        result = await toolkit.execute_tool("return_list_of_basemodels")
        print(f"Result type: {type(result.content)}")
        print(f"Result is list: {isinstance(result.content, list)}")
        print(f"List length: {len(result.content)}")
        print(f"First item type: {type(result.content[0])}")

        # Serialize for display
        serialized = [item.model_dump() for item in result.content]
        print(f"Result content: {json.dumps(serialized, indent=2)}")

        assert isinstance(result.content, list), "Content should be list"
        assert len(result.content) == 3
        assert all(isinstance(item, PersonData) for item in result.content)
        print("[OK] List of BaseModels return works")
        results.append(True)
    except Exception as e:
        print(f"[ERROR] {e}")
        results.append(False)

    # Test 6: Empty list return
    print("\nTest 6: Tool returns empty list")
    print("-" * 70)
    try:
        result = await toolkit.execute_tool("return_empty_list")
        print(f"Result type: {type(result.content)}")
        print(f"Result content: {result.content}")
        assert isinstance(result.content, list), "Content should be list"
        assert len(result.content) == 0, "List should be empty"
        print("[OK] Empty list return works")
        results.append(True)
    except Exception as e:
        print(f"[ERROR] {e}")
        results.append(False)

    return results


def test_agent_serialization():
    """Test that agent properly serializes tool results for LLM."""
    print("\n" + "=" * 70)
    print("Testing Agent Serialization (for LLM)")
    print("=" * 70)

    agent = TestTypesAgent()

    # Mock the serialization logic from agent.py
    def serialize_content(content):
        """Simulate the serialization logic in agent.py"""
        if isinstance(content, str):
            return content
        elif isinstance(content, BaseModel):
            return content.model_dump_json(indent=2)
        elif isinstance(content, list):
            if content and isinstance(content[0], BaseModel):
                serialized_list = [item.model_dump() for item in content]
                return json.dumps(serialized_list, indent=2, ensure_ascii=False)
            else:
                return json.dumps(content, indent=2, ensure_ascii=False)
        elif isinstance(content, dict):
            return json.dumps(content, indent=2, ensure_ascii=False)
        else:
            return str(content)

    test_cases = [
        ("String", "Hello"),
        ("Dict", {"key": "value"}),
        ("List", [1, 2, 3]),
        ("Empty List", []),
        ("BaseModel", PersonData(name="Alice", age=30)),
        ("List of BaseModel", [PersonData(name="Bob", age=25)]),
    ]

    results = []
    for name, content in test_cases:
        print(f"\nTest: Serialize {name}")
        print("-" * 70)
        try:
            serialized = serialize_content(content)
            print(f"Input type: {type(content)}")
            print(f"Output type: {type(serialized)}")
            print(f"Output (first 200 chars): {serialized[:200]}")

            # All serialized outputs should be strings
            assert isinstance(serialized, str), f"Serialized {name} should be string"

            print(f"[OK] {name} serialization works")
            results.append(True)
        except Exception as e:
            print(f"[ERROR] {e}")
            results.append(False)

    return results


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("Content Types Test Suite")
    print("=" * 70 + "\n")

    all_results = []

    # Run tool return types test
    tool_results = await test_tool_return_types()
    all_results.extend(tool_results)

    # Run serialization test
    serialization_results = test_agent_serialization()
    all_results.extend(serialization_results)

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Total tests: {len(all_results)}")
    print(f"Passed: {sum(all_results)}")
    print(f"Failed: {len(all_results) - sum(all_results)}")

    if all(all_results):
        print("\n[OK] All tests passed!")
    else:
        print("\n[ERROR] Some tests failed")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
