"""
Test that register_delegate creates correct tool schemas.
"""
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
from fractal import BaseAgent, AgentToolkit
import json

# Load environment
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Set dummy key for testing
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "sk-test-dummy-key"


class SpecialistAgent(BaseAgent):
    """A specialist agent with some tools."""

    def __init__(self):
        super().__init__(
            name="Specialist",
            system_prompt="You are a specialist.",
            model="gpt-4o-mini",
            client=AsyncOpenAI()
        )

    @AgentToolkit.register_as_tool
    def analyze(self, data: str) -> dict:
        """
        Analyze data.

        Args:
            data (str): Data to analyze

        Returns:
            Analysis results
        """
        return {"analysis": f"Analyzed: {data}"}


class CoordinatorAgent(BaseAgent):
    """A coordinator agent that delegates to specialists."""

    def __init__(self, specialist):
        super().__init__(
            name="Coordinator",
            system_prompt="You coordinate tasks.",
            model="gpt-4o-mini",
            client=AsyncOpenAI()
        )

        # Register with custom name
        self.register_delegate(
            specialist,
            tool_name="ask_specialist",
            description="Delegate complex queries to the specialist"
        )

        # Register with default name
        self.register_delegate(specialist)


def test_tool_schemas():
    """Test that tool schemas are correct."""
    print("=" * 70)
    print("Testing register_delegate Tool Schemas")
    print("=" * 70)

    specialist = SpecialistAgent()
    coordinator = CoordinatorAgent(specialist)

    print(f"\nSpecialist has {len(specialist.get_tools())} tool(s):")
    for tool_name in specialist.get_tools().keys():
        print(f"  - {tool_name}")

    print(f"\nCoordinator has {len(coordinator.get_tools())} tool(s):")
    for tool_name in coordinator.get_tools().keys():
        print(f"  - {tool_name}")

    print("\n" + "-" * 70)
    print("Detailed Tool Schemas:")
    print("-" * 70)

    schemas = coordinator.get_tool_schemas()
    for schema in schemas:
        func = schema['function']
        print(f"\nTool: {func['name']}")
        print(f"Description: {func.get('description', 'N/A')}")

        params = func.get('parameters', {})
        props = params.get('properties', {})
        required = params.get('required', [])

        print("Parameters:")
        if not props:
            print("  (none)")
        else:
            for param_name, param_info in props.items():
                param_type = param_info.get('type', 'unknown')
                param_desc = param_info.get('description', 'N/A')
                is_required = param_name in required
                req_marker = " (required)" if is_required else ""
                print(f"  - {param_name}: {param_type}{req_marker}")
                print(f"    Description: {param_desc}")

    print("\n" + "=" * 70)
    print("Validation:")
    print("=" * 70)

    # Validate
    assert len(coordinator.get_tools()) == 2, "Should have 2 tools"

    tool_names = list(coordinator.get_tools().keys())
    assert "ask_specialist" in tool_names, "Should have ask_specialist"
    assert "delegate_to_specialist" in tool_names, "Should have delegate_to_specialist"

    # Check schema details
    for schema in schemas:
        func = schema['function']
        name = func['name']

        # Check that tool name in schema matches registered name
        assert name in tool_names, f"Schema name {name} should be in registered tools"

        # Check parameters
        params = func.get('parameters', {})
        props = params.get('properties', {})
        required = params.get('required', [])

        # Should have 'query' parameter
        assert 'query' in props, f"Tool {name} should have 'query' parameter"
        assert props['query']['type'] == 'string', f"Tool {name} query should be string"
        assert 'query' in required, f"Tool {name} query should be required"

        print(f"[OK] {name}: Correct schema")

    print("\n[OK] All validations passed!")
    print("=" * 70)


async def test_tool_execution():
    """Test that delegated tools can be executed."""
    print("\n" + "=" * 70)
    print("Testing Tool Execution")
    print("=" * 70)

    specialist = SpecialistAgent()
    coordinator = CoordinatorAgent(specialist)

    # Test direct tool execution
    print("\nTesting direct tool execution...")

    result = await coordinator.execute_tool(
        "ask_specialist",
        query="Test query for specialist"
    )

    print(f"Tool: ask_specialist")
    print(f"Result type: {type(result.content)}")
    print(f"Success: {result.error is None}")

    if result.error:
        print(f"Error: {result.error}")
    else:
        print(f"Content type: {type(result.content).__name__}")

    print("\n[OK] Tool execution test completed")
    print("=" * 70)


async def main():
    """Run all tests."""
    test_tool_schemas()
    await test_tool_execution()


if __name__ == "__main__":
    asyncio.run(main())
