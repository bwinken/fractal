"""
Standalone Toolkit Pattern Example
==================================

This example demonstrates how to create a standalone AgentToolkit and attach
it to a BaseAgent instance, without using class inheritance.

OVERVIEW
--------
The standalone toolkit pattern separates tool definitions from the agent:

1. Create a custom AgentToolkit subclass
2. Define tools as methods with @AgentToolkit.register_as_tool
3. Pass the toolkit instance to BaseAgent via the `toolkit=` parameter

This pattern gives you:
- Reusable toolkits across multiple agents
- Separation between agent personality and capabilities
- Flexible composition of tools

WHEN TO USE
-----------
- When you want to share tools across multiple agents
- When separating concerns between agent logic and tools
- When building modular, reusable components

COMPARISON WITH INHERITANCE PATTERN
-----------------------------------
Inheritance pattern (see inheritance_example.py):
    class MyAgent(BaseAgent):
        @AgentToolkit.register_as_tool
        def my_tool(self): ...

Standalone toolkit pattern (this example):
    class MyToolkit(AgentToolkit):
        @AgentToolkit.register_as_tool
        def my_tool(self): ...

    agent = BaseAgent(toolkit=MyToolkit())

Both patterns work well. Choose based on your architecture needs.

To run:
    python examples/basic_example.py
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field
from fractal import BaseAgent, AgentToolkit

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


# =============================================================================
# Pydantic Models for Structured Data
# =============================================================================

class WeatherData(BaseModel):
    """Weather information for a location."""
    location: str = Field(..., description="Location name")
    temperature: float = Field(..., description="Temperature in Celsius")
    condition: str = Field(..., description="Weather condition")


# =============================================================================
# Standalone Toolkit: Weather Operations
# =============================================================================

class WeatherToolkit(AgentToolkit):
    """
    A standalone toolkit for weather-related operations.

    This toolkit can be attached to any BaseAgent to give it weather capabilities.
    The same toolkit instance can be shared or different instances created.
    """

    def __init__(self):
        super().__init__()
        # Toolkit-owned data
        self.weather_db = {
            "New York": WeatherData(location="New York", temperature=22.5, condition="Sunny"),
            "London": WeatherData(location="London", temperature=15.0, condition="Rainy"),
            "Tokyo": WeatherData(location="Tokyo", temperature=28.0, condition="Cloudy"),
        }

    @AgentToolkit.register_as_tool
    def get_weather(self, location: str) -> WeatherData:
        """
        Get current weather information for a location.

        Args:
            location (str): The name of the city to get weather for

        Returns:
            WeatherData object containing temperature and condition
        """
        if location in self.weather_db:
            return self.weather_db[location]
        else:
            return WeatherData(
                location=location,
                temperature=20.0,
                condition="Unknown"
            )

    @AgentToolkit.register_as_tool
    def list_locations(self) -> list:
        """
        Get list of available locations.

        Returns:
            List of location names
        """
        return list(self.weather_db.keys())


# =============================================================================
# Main: Demonstrate Standalone Toolkit
# =============================================================================

def main():
    """Run the standalone toolkit example."""
    print("=" * 70)
    print("Standalone Toolkit Pattern Example")
    print("=" * 70)

    # 1. Create the toolkit
    print("\n[1] Create Standalone Toolkit")
    print("-" * 40)
    toolkit = WeatherToolkit()
    print(f"Created WeatherToolkit with {len(toolkit._tools or {})} tools")

    # 2. Attach toolkit to an agent
    print("\n[2] Attach Toolkit to Agent")
    print("-" * 40)
    agent = BaseAgent(
        name="WeatherBot",
        system_prompt="You are a helpful weather assistant.",
        toolkit=toolkit,  # <-- Pass toolkit here
        model="gpt-4o-mini"
    )
    print(f"Agent '{agent.name}' now has tools: {list(agent.get_tools().keys())}")

    # 3. Direct tool execution (no LLM needed)
    print("\n[3] Direct Tool Execution")
    print("-" * 40)
    result = toolkit.execute_tool("get_weather", location="Tokyo")
    print(f"get_weather('Tokyo'):")
    print(f"  {result.content.model_dump_json(indent=2)}")

    # 4. Show tool schemas
    print("\n[4] Tool Schemas (for LLM)")
    print("-" * 40)
    for schema in agent.get_tool_schemas():
        func = schema['function']
        print(f"  - {func['name']}: {func['description'][:50]}...")

    # 5. Demonstrate toolkit reuse
    print("\n[5] Toolkit Reuse")
    print("-" * 40)
    another_agent = BaseAgent(
        name="TravelBot",
        system_prompt="You are a travel assistant who uses weather data.",
        toolkit=WeatherToolkit(),  # Same toolkit class, different instance
        model="gpt-4o-mini"
    )
    print(f"Another agent '{another_agent.name}' also has: {list(another_agent.get_tools().keys())}")
    print("Both agents share the same toolkit capabilities!")

    # 6. Run with LLM (requires API key)
    print("\n[6] Run with LLM")
    print("-" * 40)
    if os.getenv("OPENAI_API_KEY"):
        print("API key found! Running agent...")
        result = agent.run("What's the weather in London?")
        print(f"Agent response: {result.content}")
    else:
        print("No OPENAI_API_KEY set.")
        print("To run with LLM, add your API key to .env file.")

    print("\n" + "=" * 70)
    print("[OK] Standalone toolkit example completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
