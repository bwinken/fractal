"""
Functional Tool Pattern Example
===============================

This example demonstrates how to add standalone functions as tools to a
BaseAgent using the `add_tool()` method, without class inheritance.

OVERVIEW
--------
The functional pattern lets you register standalone functions as tools:

1. Create a BaseAgent instance
2. Define tools as regular functions decorated with @tool
3. Register them with `agent.add_tool(func)`

This pattern gives you:
- Simple, straightforward tool registration
- No class inheritance required
- Easy integration with existing functions

WHEN TO USE
-----------
- Quick prototyping and experimentation
- When tools are simple standalone functions
- When you don't need instance state in tools

COMPARISON WITH INHERITANCE PATTERN
-----------------------------------
Inheritance pattern (see inheritance_example.py):
    class MyAgent(BaseAgent):
        @AgentToolkit.register_as_tool
        def my_tool(self): ...

Functional pattern (this example):
    @tool
    def my_tool(query: str) -> str: ...

    agent = BaseAgent(...)
    agent.add_tool(my_tool)

Both patterns work well. Choose based on your needs.

NO API KEY REQUIRED
-------------------
This example demonstrates tool registration without making API calls.
Uncomment the agent.run() lines to test with a real OpenAI API key.

To run:
    python examples/basic_example.py
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from fractal import BaseAgent, tool

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Set dummy API key for demonstration (no API calls made)
os.environ.setdefault("OPENAI_API_KEY", "sk-demo-key-not-used")


# =============================================================================
# Pydantic Models for Structured Data
# =============================================================================

class WeatherData(BaseModel):
    """Weather information for a location."""
    location: str = Field(..., description="Location name")
    temperature: float = Field(..., description="Temperature in Celsius")
    condition: str = Field(..., description="Weather condition")


# =============================================================================
# Standalone Tool Functions
# =============================================================================

# Simulated weather database
WEATHER_DB = {
    "New York": WeatherData(location="New York", temperature=22.5, condition="Sunny"),
    "London": WeatherData(location="London", temperature=15.0, condition="Rainy"),
    "Tokyo": WeatherData(location="Tokyo", temperature=28.0, condition="Cloudy"),
}


@tool
def get_weather(location: str) -> WeatherData:
    """
    Get current weather information for a location.

    Args:
        location (str): The name of the city to get weather for

    Returns:
        WeatherData object containing temperature and condition
    """
    if location in WEATHER_DB:
        return WEATHER_DB[location]
    else:
        return WeatherData(
            location=location,
            temperature=20.0,
            condition="Unknown"
        )


@tool
def list_locations() -> list:
    """
    Get list of available locations.

    Returns:
        List of location names
    """
    return list(WEATHER_DB.keys())


# =============================================================================
# Main: Demonstrate Functional Tool Pattern
# =============================================================================

async def main():
    """Run the functional tool pattern example."""
    print("=" * 70)
    print("Functional Tool Pattern Example")
    print("=" * 70)

    # 1. Create agent
    print("\n[1] Create Agent")
    print("-" * 40)
    agent = BaseAgent(
        name="WeatherBot",
        system_prompt="You are a helpful weather assistant.",
        model="gpt-4o-mini"
    )
    print(f"Created agent '{agent.name}'")

    # 2. Add tools to agent
    print("\n[2] Add Tools with add_tool()")
    print("-" * 40)
    agent.add_tool(get_weather)
    agent.add_tool(list_locations)
    print(f"Agent now has tools: {list(agent.get_tools().keys())}")

    # 3. Direct tool execution (no LLM needed)
    print("\n[3] Direct Tool Execution")
    print("-" * 40)
    result = await agent.execute_tool("get_weather", location="Tokyo")
    print(f"get_weather('Tokyo'):")
    print(f"  {result.content.model_dump_json(indent=2)}")

    result = await agent.execute_tool("list_locations")
    print(f"\nlist_locations():")
    print(f"  {result.content}")

    # 4. Show tool schemas
    print("\n[4] Tool Schemas (for LLM)")
    print("-" * 40)
    for schema in agent.get_tool_schemas():
        func = schema['function']
        print(f"  - {func['name']}: {func['description'][:50]}...")

    # 5. Demonstrate termination tool
    print("\n[5] Termination Tool")
    print("-" * 40)

    @tool
    def final_answer(answer: str) -> str:
        """Return final answer and exit agent loop.

        Args:
            answer (str): The final answer

        Returns:
            The answer
        """
        return answer

    agent.add_tool(final_answer, terminate=True)
    print(f"Added 'final_answer' with terminate=True")
    print(f"All tools: {list(agent.get_tools().keys())}")

    # 6. Run with LLM (requires API key)
    print("\n[6] Run with LLM")
    print("-" * 40)
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and not api_key.startswith("sk-demo"):
        print("API key found! Running agent...")
        result = await agent.run("What's the weather in London?")
        print(f"Agent response: {result.content}")
    else:
        print("No OPENAI_API_KEY set.")
        print("To run with LLM, add your API key to .env file.")
        print("\nExample (commented out):")
        print('  # result = await agent.run("What\'s the weather in London?")')

    print("\n" + "=" * 70)
    print("[OK] Functional tool pattern example completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
