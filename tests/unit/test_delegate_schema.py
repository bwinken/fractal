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


def test_register_delegate_parameters_validation():
    """Test that register_delegate validates the parameters dict structure."""
    print("\n" + "=" * 70)
    print("Testing register_delegate parameters validation")
    print("=" * 70)

    specialist = SpecialistAgent()

    # --- TypeError cases ---

    # parameters is not a dict
    try:
        toolkit = AgentToolkit()
        toolkit.register_delegate(specialist, tool_name="t1", parameters="bad")
        assert False, "Should have raised TypeError"
    except TypeError as e:
        assert "'parameters' must be a dict" in str(e)
        print(f"[OK] non-dict parameters: {e}")

    # parameter spec is not a dict (e.g. {"sql": "str"})
    try:
        toolkit = AgentToolkit()
        toolkit.register_delegate(specialist, tool_name="t2", parameters={"sql": "str"})
        assert False, "Should have raised TypeError"
    except TypeError as e:
        assert "spec must be a dict" in str(e)
        print(f"[OK] non-dict spec: {e}")

    # missing 'type' key
    try:
        toolkit = AgentToolkit()
        toolkit.register_delegate(specialist, tool_name="t3", parameters={
            "sql": {"description": "query"}
        })
        assert False, "Should have raised TypeError"
    except TypeError as e:
        assert "missing required key 'type'" in str(e)
        print(f"[OK] missing type: {e}")

    # missing 'description' key
    try:
        toolkit = AgentToolkit()
        toolkit.register_delegate(specialist, tool_name="t4", parameters={
            "sql": {"type": "str"}
        })
        assert False, "Should have raised TypeError"
    except TypeError as e:
        assert "missing required key 'description'" in str(e)
        print(f"[OK] missing description: {e}")

    # unknown key (typo)
    try:
        toolkit = AgentToolkit()
        toolkit.register_delegate(specialist, tool_name="t5", parameters={
            "sql": {"type": "str", "description": "query", "decription": "typo"}
        })
        assert False, "Should have raised TypeError"
    except TypeError as e:
        assert "unknown keys" in str(e)
        print(f"[OK] unknown key: {e}")

    # unsupported type
    try:
        toolkit = AgentToolkit()
        toolkit.register_delegate(specialist, tool_name="t6", parameters={
            "sql": {"type": "tuple", "description": "bad type"}
        })
        assert False, "Should have raised TypeError"
    except TypeError as e:
        assert "unsupported type" in str(e)
        print(f"[OK] unsupported type: {e}")

    # 'type' is not a string
    try:
        toolkit = AgentToolkit()
        toolkit.register_delegate(specialist, tool_name="t7", parameters={
            "sql": {"type": 123, "description": "bad"}
        })
        assert False, "Should have raised TypeError"
    except TypeError as e:
        assert "unsupported type" in str(e)
        print(f"[OK] type not a string: {e}")

    # 'required' is not a bool
    try:
        toolkit = AgentToolkit()
        toolkit.register_delegate(specialist, tool_name="t8", parameters={
            "sql": {"type": "str", "description": "query", "required": "yes"}
        })
        assert False, "Should have raised TypeError"
    except TypeError as e:
        assert "'required' must be a bool" in str(e)
        print(f"[OK] required not bool: {e}")

    # --- Valid cases ---

    # Valid full spec
    toolkit = AgentToolkit()
    toolkit.register_delegate(specialist, tool_name="t_valid", parameters={
        "sql": {"type": "str", "description": "SQL query"},
        "limit": {"type": "int", "description": "Max rows", "required": False},
    })
    schemas = toolkit.get_tool_schemas()
    schema = [s for s in schemas if s['function']['name'] == 't_valid'][0]
    props = schema['function']['parameters']['properties']
    required = schema['function']['parameters']['required']
    assert 'sql' in props
    assert 'limit' in props
    assert 'sql' in required
    assert 'limit' not in required
    print("[OK] valid structured parameters accepted")

    # Valid with no parameters (default mode)
    toolkit2 = AgentToolkit()
    toolkit2.register_delegate(specialist, tool_name="t_default")
    schemas2 = toolkit2.get_tool_schemas()
    schema2 = [s for s in schemas2 if s['function']['name'] == 't_default'][0]
    assert 'query' in schema2['function']['parameters']['properties']
    print("[OK] default mode (no parameters) works")

    print("\n[OK] All parameter validation tests passed!")
    print("=" * 70)


async def main():
    """Run all tests."""
    test_tool_schemas()
    await test_tool_execution()
    test_register_delegate_parameters_validation()


if __name__ == "__main__":
    asyncio.run(main())
