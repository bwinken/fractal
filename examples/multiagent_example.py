"""
Multi-Agent Delegation Example
==============================

This example demonstrates how to build multi-agent systems where a coordinator
agent delegates tasks to specialist agents using the `register_delegate()` API.

OVERVIEW
--------
Multi-agent systems in Fractal follow a delegation pattern:

1. Create specialist agents with domain-specific tools
2. Create a coordinator agent that registers specialists as delegates
3. The coordinator can now "call" specialists as tools

This creates a tree-shaped workflow: Coordinator -> Specialists.

KEY API
-------
coordinator.register_delegate(
    agent,              # The specialist agent to register
    tool_name="...",    # Tool name for delegation (e.g., "ask_researcher")
    description="..."   # Description shown to the LLM
)

HOW IT WORKS
------------
1. Coordinator receives user query
2. LLM decides to delegate (calls the delegation tool)
3. Specialist agent.run() is called with the delegated query
4. Specialist's response returns to coordinator
5. Coordinator can delegate to more agents or respond

BENEFITS
--------
- Separation of concerns (each agent has clear responsibility)
- Scalable (add more specialists as needed)
- Composable (specialists can have their own delegates)
- Traceable (delegation chains are tracked in traces)

To run:
    python examples/multiagent_example.py
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
# Specialist Agents
# =============================================================================

class ResearcherAgent(BaseAgent):
    """Specialist agent for research and information gathering."""

    def __init__(self):
        super().__init__(
            name="Researcher",
            system_prompt="You are a research specialist. Gather and organize information.",
            model="gpt-4o-mini",
            client=AsyncOpenAI()
        )

    @AgentToolkit.register_as_tool
    def gather_facts(self, topic: str) -> list:
        """
        Gather facts about a topic.

        Args:
            topic (str): Topic to research

        Returns:
            List of facts
        """
        return [
            f"Fact 1: {topic} is widely studied",
            f"Fact 2: Recent advances in {topic}",
            f"Fact 3: Future trends in {topic}"
        ]


class WriterAgent(BaseAgent):
    """Specialist agent for content creation."""

    def __init__(self):
        super().__init__(
            name="Writer",
            system_prompt="You are a professional writer. Create clear content.",
            model="gpt-4o-mini",
            client=AsyncOpenAI()
        )

    @AgentToolkit.register_as_tool
    def format_article(self, title: str, content: str) -> str:
        """
        Format content as an article.

        Args:
            title (str): Article title
            content (str): Article body

        Returns:
            Formatted article
        """
        return f"# {title}\n\n{content}\n\n---\n*By WriterAgent*"


# =============================================================================
# Coordinator Agent
# =============================================================================

class ManagerAgent(BaseAgent):
    """
    Coordinator agent that delegates to specialists.

    The manager can:
    1. Receive complex tasks from users
    2. Delegate sub-tasks to Researcher and Writer
    3. Combine results and respond
    """

    def __init__(self, researcher: BaseAgent, writer: BaseAgent):
        super().__init__(
            name="Manager",
            system_prompt="""You are a project manager coordinating a team.
            - Use ask_researcher for information gathering
            - Use ask_writer for content creation
            Delegate appropriately based on the task.""",
            model="gpt-4o-mini",
            client=AsyncOpenAI()
        )

        # Register specialists as delegates
        # This creates tools that the LLM can call to delegate work
        self.register_delegate(
            researcher,
            tool_name="ask_researcher",
            description="Delegate research tasks to the Researcher"
        )

        self.register_delegate(
            writer,
            tool_name="ask_writer",
            description="Delegate writing tasks to the Writer"
        )


# =============================================================================
# Main: Demonstrate Delegation
# =============================================================================

async def main():
    """Run the multi-agent delegation example."""
    print("=" * 70)
    print("Multi-Agent Delegation Example")
    print("=" * 70)

    # 1. Create specialist agents
    print("\n[1] Creating Agents")
    print("-" * 40)
    researcher = ResearcherAgent()
    writer = WriterAgent()

    print(f"  Researcher tools: {list(researcher.get_tools().keys())}")
    print(f"  Writer tools: {list(writer.get_tools().keys())}")

    # 2. Create coordinator with delegates
    print("\n[2] Create Coordinator with Delegates")
    print("-" * 40)
    manager = ManagerAgent(researcher, writer)

    print(f"  Manager tools: {list(manager.get_tools().keys())}")
    print("  (Includes delegation tools: ask_researcher, ask_writer)")

    # 3. Show delegation hierarchy
    print("\n[3] Delegation Hierarchy")
    print("-" * 40)
    print("""
    ManagerAgent (Coordinator)
    |
    +-- ask_researcher --> ResearcherAgent
    |                      +-- gather_facts
    |
    +-- ask_writer ------> WriterAgent
                           +-- format_article
    """)

    # 4. Test individual agents
    print("[4] Test Individual Agents (Direct)")
    print("-" * 40)

    result = researcher.toolkit.execute_tool("gather_facts", topic="Python")
    print(f"  Researcher.gather_facts('Python'):")
    print(f"    {result.content}")

    result = writer.toolkit.execute_tool("format_article", title="Test", content="Hello")
    print(f"\n  Writer.format_article('Test', 'Hello'):")
    print(f"    {result.content[:50]}...")

    # 5. Run coordinator with delegation
    print("\n[5] Run with LLM (Delegation)")
    print("-" * 40)
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and not api_key.startswith("sk-test"):
        print("Running manager with real API...")
        result = await manager.run(
            "Ask the researcher to gather facts about AI, then ask the writer to format it as an article.",
            max_iterations=10
        )
        print(f"Result: {result.content[:200]}...")
    else:
        print("Using dummy API key - LLM delegation skipped.")
        print("Set real OPENAI_API_KEY to test full delegation.")
        print("\nExample workflow (with real API):")
        print("  1. User: 'Research AI and write an article'")
        print("  2. Manager calls ask_researcher('gather facts about AI')")
        print("  3. Researcher runs, returns facts")
        print("  4. Manager calls ask_writer('format as article')")
        print("  5. Writer runs, returns formatted article")
        print("  6. Manager responds with final result")

    print("\n" + "=" * 70)
    print("[OK] Multi-agent delegation example completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
