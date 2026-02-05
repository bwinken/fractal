"""
Tool Namespacing Example
========================

This example demonstrates how to handle multiple agents that have tools
with the SAME NAME (e.g., both have a "search" tool).

THE PROBLEM
-----------
When two agents have tools with the same name:

    class DatabaseAgent(BaseAgent):
        @AgentToolkit.register_as_tool
        def search(self, query): ...  # "search" tool

    class WebAgent(BaseAgent):
        @AgentToolkit.register_as_tool
        def search(self, query): ...  # Also "search" tool

A coordinator that needs BOTH will have a naming conflict.

THE SOLUTION: DELEGATION (Recommended)
--------------------------------------
Use `register_delegate()` to expose agents as delegation tools:

    coordinator.register_delegate(db_agent, tool_name="ask_database")
    coordinator.register_delegate(web_agent, tool_name="ask_web")

Now the coordinator has:
- "ask_database" -> delegates to DatabaseAgent
- "ask_web" -> delegates to WebAgent

No conflict! Each agent keeps its own "search" tool internally.

WHY DELEGATION WORKS
--------------------
1. Each agent is encapsulated - tools stay internal
2. Coordinator only sees delegation tools (ask_database, ask_web)
3. Simple to implement (just register_delegate)
4. Clean separation of concerns
5. Agents remain independently testable

ALTERNATIVE: NAMESPACING
------------------------
You CAN manually namespace tools (db_search, web_search), but:
- More complex setup
- Tight coupling
- Harder to maintain

Delegation is recommended in most cases.

To run:
    python examples/tool_namespacing_example.py
"""
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
from fractal import BaseAgent, AgentToolkit

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Set dummy key for testing (remove if using real API)
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-key")


# =============================================================================
# Two Agents with the SAME Tool Name
# =============================================================================

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
        return {"source": "Database", "query": query, "results": [f"DB: {query}"]}


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
        return {"source": "Web", "query": query, "results": [f"Web: {query}"]}


# =============================================================================
# Coordinator Using Delegation (No Conflicts)
# =============================================================================

class SearchCoordinator(BaseAgent):
    """Coordinator that uses delegation to avoid tool name conflicts."""

    def __init__(self, db_agent: BaseAgent, web_agent: BaseAgent):
        super().__init__(
            name="SearchCoordinator",
            system_prompt="""You coordinate searches across multiple sources.
            - Use ask_database for database searches
            - Use ask_web for web searches""",
            model="gpt-4o-mini",
            client=AsyncOpenAI()
        )

        # Register agents as delegates with DISTINCT tool names
        # This avoids the naming conflict!
        self.register_delegate(
            db_agent,
            tool_name="ask_database",  # NOT "search"
            description="Search the database for information"
        )

        self.register_delegate(
            web_agent,
            tool_name="ask_web",  # NOT "search"
            description="Search the web for information"
        )


# =============================================================================
# Main: Demonstrate the Solution
# =============================================================================

async def main():
    """Run the tool namespacing example."""
    print("=" * 70)
    print("Tool Namespacing Example")
    print("=" * 70)

    # 1. Show the conflict scenario
    print("\n[1] The Problem: Same Tool Name")
    print("-" * 40)
    db_agent = DatabaseAgent()
    web_agent = WebAgent()

    print(f"  DatabaseAgent tools: {list(db_agent.get_tools().keys())}")
    print(f"  WebAgent tools: {list(web_agent.get_tools().keys())}")
    print("\n  Both have 'search' -> Conflict if we combine them!")

    # 2. Show the delegation solution
    print("\n[2] The Solution: Delegation")
    print("-" * 40)
    coordinator = SearchCoordinator(db_agent, web_agent)

    print(f"  Coordinator tools: {list(coordinator.get_tools().keys())}")
    print("\n  Coordinator has 'ask_database' and 'ask_web' -> No conflict!")

    # 3. Verify no conflict
    print("\n[3] Verification")
    print("-" * 40)
    coord_tools = list(coordinator.get_tools().keys())

    assert "search" not in coord_tools, "Coordinator should NOT have 'search'"
    assert "ask_database" in coord_tools, "Should have 'ask_database'"
    assert "ask_web" in coord_tools, "Should have 'ask_web'"

    print("  [OK] 'search' NOT in coordinator tools")
    print("  [OK] 'ask_database' in coordinator tools")
    print("  [OK] 'ask_web' in coordinator tools")

    # 4. Test individual agents (they still have their own 'search')
    print("\n[4] Individual Agents Still Work")
    print("-" * 40)

    db_result = await db_agent.execute_tool("search", query="test")
    print(f"  db_agent.search('test'): {db_result.content}")

    web_result = await web_agent.execute_tool("search", query="test")
    print(f"  web_agent.search('test'): {web_result.content}")

    # 5. Show the workflow
    print("\n[5] How It Works")
    print("-" * 40)
    print("""
    User: "Search both database and web for 'AI'"

    Coordinator:
      1. Calls ask_database("search for AI")
         -> DatabaseAgent.run() -> uses search() tool internally
         <- Returns database results

      2. Calls ask_web("search for AI")
         -> WebAgent.run() -> uses search() tool internally
         <- Returns web results

      3. Combines and responds

    Each agent's "search" stays internal - no conflict!
    """)

    print("=" * 70)
    print("[OK] Tool namespacing example completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
