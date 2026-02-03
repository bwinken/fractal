"""
Multi-Agent Collaboration Example

This example shows how agents can collaborate and delegate tasks to each other.

Scenario:
- Manager Agent: Coordinates tasks
- Researcher Agent: Gathers information
- Writer Agent: Creates content

The Manager delegates to specialists based on the task.
"""
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
from fractal import BaseAgent, AgentToolkit
from pydantic import BaseModel

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Set dummy key for testing
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "sk-test-dummy-key"


# ============================================================================
# Specialist Agents
# ============================================================================

class ResearcherAgent(BaseAgent):
    """Agent that gathers information."""

    def __init__(self):
        super().__init__(
            name="Researcher",
            system_prompt="You are a researcher. Gather and organize information thoroughly.",
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
        # Simulate research
        return [
            f"Fact 1: {topic} is widely studied",
            f"Fact 2: Recent advances in {topic}",
            f"Fact 3: Future trends in {topic}"
        ]

    @AgentToolkit.register_as_tool
    async def search_sources(self, topic: str, count: int = 3) -> dict:
        """
        Search for sources about a topic.

        Args:
            topic (str): Topic to search
            count (int): Number of sources

        Returns:
            Search results
        """
        await asyncio.sleep(0.1)
        return {
            "topic": topic,
            "sources": [f"Source {i+1} about {topic}" for i in range(count)],
            "total": count
        }


class WriterAgent(BaseAgent):
    """Agent that creates written content."""

    def __init__(self):
        super().__init__(
            name="Writer",
            system_prompt="You are a professional writer. Create clear, engaging content.",
            model="gpt-4o-mini",
            client=AsyncOpenAI()
        )

    @AgentToolkit.register_as_tool
    def write_summary(self, content: str, max_words: int = 100) -> str:
        """
        Write a summary of content.

        Args:
            content (str): Content to summarize
            max_words (int): Maximum words

        Returns:
            Summary
        """
        # Simulate writing
        words = content.split()[:max_words]
        return f"Summary: {' '.join(words)}..."

    @AgentToolkit.register_as_tool
    def format_article(self, title: str, content: str) -> str:
        """
        Format content as an article.

        Args:
            title (str): Article title
            content (str): Article content

        Returns:
            Formatted article
        """
        return f"""
# {title}

{content}

---
*Article by WriterAgent*
        """.strip()


class ManagerAgent(BaseAgent):
    """Manager agent that delegates to specialists."""

    def __init__(self, researcher: BaseAgent, writer: BaseAgent):
        super().__init__(
            name="Manager",
            system_prompt="""You are a project manager coordinating a team.
            You have access to:
            - Researcher: for gathering information
            - Writer: for creating content

            Delegate tasks appropriately and coordinate the work.""",
            model="gpt-4o-mini",
            client=AsyncOpenAI()
        )

        # Store references
        self.researcher = researcher
        self.writer = writer

        # Register specialists as delegates (subordinate agents)
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

    @AgentToolkit.register_as_tool
    def coordinate_task(self, task: str, agents: str) -> str:
        """
        Coordinate a task across agents.

        Args:
            task (str): Task description
            agents (str): Comma-separated list of agents to coordinate

        Returns:
            Coordination plan
        """
        return f"Coordinating '{task}' with agents: {agents}"


# ============================================================================
# Examples
# ============================================================================

async def example_basic_delegation():
    """Example 1: Basic delegation from Manager to Researcher."""
    print("=" * 70)
    print("Example 1: Basic Delegation")
    print("=" * 70)

    # Create agents
    researcher = ResearcherAgent()
    writer = WriterAgent()
    manager = ManagerAgent(researcher, writer)

    print(f"\nManager has {len(manager.get_tools())} tools:")
    for tool_name in manager.get_tools().keys():
        print(f"  - {tool_name}")

    # Manager delegates to researcher
    print("\n[Manager] Asking researcher about AI...")
    result = await manager.run(
        "Ask the researcher to gather facts about Artificial Intelligence",
        max_iterations=5
    )

    print(f"\n[Result]")
    print(f"Success: {result.success}")
    print(f"Content: {result.content}")

    print("\n" + "=" * 70)


async def example_multi_agent_workflow():
    """Example 2: Complex workflow with multiple agents."""
    print("\nExample 2: Multi-Agent Workflow")
    print("=" * 70)

    # Create agents
    researcher = ResearcherAgent()
    writer = WriterAgent()
    manager = ManagerAgent(researcher, writer)

    print("\n[Manager] Creating an article about Python...")
    result = await manager.run(
        """Create an article about Python programming:
        1. Ask researcher to gather facts about Python
        2. Ask writer to format it as an article titled 'Python Programming'""",
        max_iterations=10
    )

    print(f"\n[Result]")
    print(f"Success: {result.success}")
    print(f"Content preview: {str(result.content)[:200]}...")

    print("\n" + "=" * 70)


async def example_direct_agent_call():
    """Example 3: Direct agent-to-agent communication."""
    print("\nExample 3: Direct Agent Communication")
    print("=" * 70)

    researcher = ResearcherAgent()
    writer = WriterAgent()

    # Researcher does research
    print("\n[Researcher] Gathering facts...")
    research_result = await researcher.run(
        "Gather facts about machine learning",
        max_iterations=3
    )

    print(f"Research: {research_result.content}")

    # Writer uses researcher's output
    print("\n[Writer] Creating article from research...")
    writer_result = await writer.run(
        f"Format this as an article titled 'ML Overview': {research_result.content}",
        max_iterations=3
    )

    print(f"Article preview: {str(writer_result.content)[:200]}...")

    print("\n" + "=" * 70)


async def example_concurrent_delegation():
    """Example 4: Concurrent delegation to multiple agents."""
    print("\nExample 4: Concurrent Delegation")
    print("=" * 70)

    researcher = ResearcherAgent()
    writer = WriterAgent()
    manager = ManagerAgent(researcher, writer)

    print("\n[Manager] Delegating to both agents concurrently...")

    # Run multiple delegations concurrently
    tasks = [
        researcher.run("Research topic A", max_iterations=3),
        writer.run("Write about topic B", max_iterations=3),
    ]

    results = await asyncio.gather(*tasks)

    for i, result in enumerate(results, 1):
        print(f"\nAgent {i} ({result.agent_name}):")
        print(f"  Success: {result.success}")
        print(f"  Content preview: {str(result.content)[:100]}...")

    print("\n" + "=" * 70)


async def example_inspect_delegation():
    """Example 5: Inspect agent delegation setup."""
    print("\nExample 5: Inspect Agent Setup")
    print("=" * 70)

    researcher = ResearcherAgent()
    writer = WriterAgent()
    manager = ManagerAgent(researcher, writer)

    print(f"\n{manager}\n")

    print("Manager's specialist agents:")
    print(f"  - Researcher: {researcher.name}")
    print(f"    Tools: {list(researcher.get_tools().keys())}")
    print(f"  - Writer: {writer.name}")
    print(f"    Tools: {list(writer.get_tools().keys())}")

    print("\nManager can delegate via:")
    delegation_tools = [t for t in manager.get_tools().keys() if 'ask_' in t or 'delegate_' in t]
    for tool in delegation_tools:
        print(f"  - {tool}")

    print("\n" + "=" * 70)


async def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("Multi-Agent Collaboration Examples")
    print("=" * 70 + "\n")

    examples = [
        ("Basic Delegation", example_basic_delegation),
        ("Multi-Agent Workflow", example_multi_agent_workflow),
        ("Direct Communication", example_direct_agent_call),
        ("Concurrent Delegation", example_concurrent_delegation),
        ("Inspect Setup", example_inspect_delegation),
    ]

    for name, example_func in examples:
        try:
            await example_func()
            print(f"\n[OK] {name} completed\n")
        except Exception as e:
            print(f"\n[ERROR] {name}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
