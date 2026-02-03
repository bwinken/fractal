"""
Tool Namespacing Example

This example shows how to handle multiple agents with the same tool names
by adding namespace prefixes.

Scenario:
- Agent A has a "search" tool
- Agent B has a "search" tool
- Coordinator needs access to both

Solutions:
1. Use delegation (recommended) - no conflict
2. Use namespaced tool registration - adds prefix
"""
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
from fractal import BaseAgent, AgentToolkit

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

os.environ["OPENAI_API_KEY"] = "sk-test-dummy-key"


# ============================================================================
# Agents with Same Tool Names
# ============================================================================

class DatabaseAgent(BaseAgent):
    """Agent that searches databases."""

    def __init__(self):
        super().__init__(
            name="DatabaseAgent",
            system_prompt="You search databases.",
            model="gpt-4o-mini",
            client=AsyncOpenAI()
        )

    @AgentToolkit.register_as_tool
    def search(self, query: str) -> dict:
        """
        Search database.

        Args:
            query (str): Search query

        Returns:
            Database results
        """
        return {
            "source": "Database",
            "query": query,
            "results": [f"DB result for {query}"]
        }


class WebAgent(BaseAgent):
    """Agent that searches the web."""

    def __init__(self):
        super().__init__(
            name="WebAgent",
            system_prompt="You search the web.",
            model="gpt-4o-mini",
            client=AsyncOpenAI()
        )

    @AgentToolkit.register_as_tool
    def search(self, query: str) -> dict:
        """
        Search web.

        Args:
            query (str): Search query

        Returns:
            Web results
        """
        return {
            "source": "Web",
            "query": query,
            "results": [f"Web result for {query}"]
        }


# ============================================================================
# Solution 1: Delegation (Recommended)
# ============================================================================

class CoordinatorWithDelegation(BaseAgent):
    """Coordinator using delegation - no naming conflicts."""

    def __init__(self, db_agent, web_agent):
        super().__init__(
            name="CoordinatorDelegation",
            system_prompt="""You coordinate searches.
            Use ask_database for database searches.
            Use ask_web for web searches.""",
            model="gpt-4o-mini",
            client=AsyncOpenAI()
        )

        # Register agents as delegates - creates separate delegation tools
        self.register_delegate(
            db_agent,
            tool_name="ask_database",
            description="Search database using DatabaseAgent"
        )

        self.register_delegate(
            web_agent,
            tool_name="ask_web",
            description="Search web using WebAgent"
        )


# ============================================================================
# Solution 2: Namespaced Tool Registration
# ============================================================================

class CoordinatorWithNamespacing(BaseAgent):
    """Coordinator with namespaced tools."""

    def __init__(self, db_agent, web_agent):
        super().__init__(
            name="CoordinatorNamespaced",
            system_prompt="""You coordinate searches.
            Use db_search for database searches.
            Use web_search for web searches.""",
            model="gpt-4o-mini",
            client=AsyncOpenAI()
        )

        # Manually register tools with prefixes
        self._register_tools_with_prefix(db_agent, prefix="db_")
        self._register_tools_with_prefix(web_agent, prefix="web_")

    def _register_tools_with_prefix(self, agent: BaseAgent, prefix: str):
        """
        Register another agent's tools with a namespace prefix.

        Args:
            agent: Agent whose tools to register
            prefix: Prefix to add to tool names
        """
        # Get agent's tools
        agent_tools = agent.get_tools()

        # Register each tool with prefix
        for tool_name, tool_func in agent_tools.items():
            prefixed_name = f"{prefix}{tool_name}"

            # Create wrapper that preserves async/sync nature
            import inspect
            if inspect.iscoroutinefunction(tool_func._original_func):
                async def async_wrapper(*args, _func=tool_func, **kwargs):
                    return await _func(**kwargs)
                wrapper = async_wrapper
            else:
                def sync_wrapper(*args, _func=tool_func, **kwargs):
                    return _func(**kwargs)
                wrapper = sync_wrapper

            # Copy metadata
            wrapper._is_agent_tool = True
            wrapper._tool_name = prefixed_name
            wrapper._tool_terminate = getattr(tool_func, '_tool_terminate', False)
            wrapper._original_func = tool_func._original_func
            wrapper.__doc__ = tool_func._original_func.__doc__

            # Access toolkit's internal state (composition pattern)
            if not self.toolkit._tools:
                self.toolkit._discover_tools()

            self.toolkit._tools[prefixed_name] = wrapper

            # Generate schema
            from fractal.parser import function_to_tool_schema
            schema = function_to_tool_schema(wrapper._original_func)
            schema['function']['name'] = prefixed_name
            self.toolkit._tool_schemas[prefixed_name] = schema


# ============================================================================
# Examples
# ============================================================================

async def example_delegation():
    """Example 1: Using delegation (no conflicts)."""
    print("=" * 70)
    print("Example 1: Delegation (Recommended)")
    print("=" * 70)

    db_agent = DatabaseAgent()
    web_agent = WebAgent()
    coordinator = CoordinatorWithDelegation(db_agent, web_agent)

    print(f"\nDatabase Agent tools: {list(db_agent.get_tools().keys())}")
    print(f"Web Agent tools: {list(web_agent.get_tools().keys())}")
    print(f"Coordinator tools: {list(coordinator.get_tools().keys())}")

    # Both agents have "search", but coordinator has "ask_database" and "ask_web"
    assert "search" in db_agent.get_tools()
    assert "search" in web_agent.get_tools()
    assert "ask_database" in coordinator.get_tools()
    assert "ask_web" in coordinator.get_tools()
    assert "search" not in coordinator.get_tools()  # No conflict!

    print("\n✅ No naming conflicts with delegation!")

    # Test direct tool calls
    print("\n[Test] Direct tool calls:")
    db_result = await db_agent.execute_tool("search", query="test")
    print(f"  DB search: {db_result.content}")

    web_result = await web_agent.execute_tool("search", query="test")
    print(f"  Web search: {web_result.content}")

    print("\n" + "=" * 70)


async def example_namespacing():
    """Example 2: Using namespaced tools."""
    print("\nExample 2: Namespaced Tools")
    print("=" * 70)

    db_agent = DatabaseAgent()
    web_agent = WebAgent()
    coordinator = CoordinatorWithNamespacing(db_agent, web_agent)

    print(f"\nDatabase Agent tools: {list(db_agent.get_tools().keys())}")
    print(f"Web Agent tools: {list(web_agent.get_tools().keys())}")
    print(f"Coordinator tools: {list(coordinator.get_tools().keys())}")

    # Coordinator has both with prefixes
    assert "db_search" in coordinator.get_tools()
    assert "web_search" in coordinator.get_tools()

    print("\n✅ Tools namespaced with prefixes!")

    # Test namespaced tool calls
    print("\n[Test] Namespaced tool calls:")
    db_result = await coordinator.execute_tool("db_search", query="test")
    print(f"  db_search: {db_result.content}")

    web_result = await coordinator.execute_tool("web_search", query="test")
    print(f"  web_search: {web_result.content}")

    print("\n" + "=" * 70)


async def example_comparison():
    """Example 3: Compare both approaches."""
    print("\nExample 3: Comparison")
    print("=" * 70)

    db_agent = DatabaseAgent()
    web_agent = WebAgent()

    # Delegation approach
    coord_delegation = CoordinatorWithDelegation(db_agent, web_agent)
    delegation_tools = list(coord_delegation.get_tools().keys())

    # Namespacing approach
    coord_namespaced = CoordinatorWithNamespacing(db_agent, web_agent)
    namespaced_tools = list(coord_namespaced.get_tools().keys())

    print("\nDelegation approach tools:")
    for tool in delegation_tools:
        print(f"  - {tool}")

    print("\nNamespacing approach tools:")
    for tool in namespaced_tools:
        print(f"  - {tool}")

    print("\nComparison:")
    print("  Delegation:")
    print("    ✅ Agents stay independent")
    print("    ✅ Simple to implement")
    print("    ✅ Clear separation")
    print("    ⚠️  Requires LLM to delegate")
    print()
    print("  Namespacing:")
    print("    ✅ Direct tool access")
    print("    ✅ No delegation overhead")
    print("    ⚠️  More complex setup")
    print("    ⚠️  Tight coupling")

    print("\n" + "=" * 70)


async def example_hybrid():
    """Example 4: Hybrid approach."""
    print("\nExample 4: Hybrid Approach")
    print("=" * 70)

    class HybridCoordinator(BaseAgent):
        """Uses both delegation AND direct tools."""

        def __init__(self, db_agent, web_agent):
            super().__init__(
                name="HybridCoordinator",
                system_prompt="You have both delegation and direct tools.",
                model="gpt-4o-mini",
                client=AsyncOpenAI()
            )

            # Delegation for full agent capability
            self.register_delegate(db_agent, "delegate_to_db")
            self.register_delegate(web_agent, "delegate_to_web")

            # Direct tools for specific operations
            self._register_tools_with_prefix(db_agent, "db_")
            self._register_tools_with_prefix(web_agent, "web_")

        def _register_tools_with_prefix(self, agent, prefix):
            """Same as CoordinatorWithNamespacing."""
            agent_tools = agent.get_tools()
            for tool_name, tool_func in agent_tools.items():
                prefixed_name = f"{prefix}{tool_name}"
                import inspect
                if inspect.iscoroutinefunction(tool_func._original_func):
                    async def async_wrapper(*args, _func=tool_func, **kwargs):
                        return await _func(**kwargs)
                    wrapper = async_wrapper
                else:
                    def sync_wrapper(*args, _func=tool_func, **kwargs):
                        return _func(**kwargs)
                    wrapper = sync_wrapper

                wrapper._is_agent_tool = True
                wrapper._tool_name = prefixed_name
                wrapper._tool_terminate = getattr(tool_func, '_tool_terminate', False)
                wrapper._original_func = tool_func._original_func
                wrapper.__doc__ = tool_func._original_func.__doc__

                # Access toolkit's internal state (composition pattern)
                if not self.toolkit._tools:
                    self.toolkit._discover_tools()
                self.toolkit._tools[prefixed_name] = wrapper

                from fractal.parser import function_to_tool_schema
                schema = function_to_tool_schema(wrapper._original_func)
                schema['function']['name'] = prefixed_name
                self.toolkit._tool_schemas[prefixed_name] = schema

    db_agent = DatabaseAgent()
    web_agent = WebAgent()
    coordinator = HybridCoordinator(db_agent, web_agent)

    tools = list(coordinator.get_tools().keys())
    print(f"\nHybrid Coordinator has {len(tools)} tools:")
    for tool in tools:
        print(f"  - {tool}")

    print("\nHybrid approach:")
    print("  ✅ Delegation for complex workflows")
    print("  ✅ Direct access for simple operations")
    print("  ✅ Maximum flexibility")

    print("\n" + "=" * 70)


async def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("Tool Namespacing Examples")
    print("=" * 70 + "\n")

    examples = [
        ("Delegation", example_delegation),
        ("Namespacing", example_namespacing),
        ("Comparison", example_comparison),
        ("Hybrid", example_hybrid),
    ]

    for name, func in examples:
        try:
            await func()
            print(f"\n[OK] {name} completed\n")
        except Exception as e:
            print(f"\n[ERROR] {name}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
