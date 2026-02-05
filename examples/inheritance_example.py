"""
Agent Inheritance Pattern Example
=================================

This example demonstrates how to create agents by subclassing BaseAgent
and using the @AgentToolkit.register_as_tool decorator.

OVERVIEW
--------
The inheritance pattern is the RECOMMENDED way to build agents in Fractal:

1. Create a class that inherits from BaseAgent
2. Define tools as methods decorated with @AgentToolkit.register_as_tool
3. Use Google-style docstrings for automatic tool schema generation
4. Access instance state (self.xxx) in your tools

This pattern gives you:
- Clean, object-oriented code structure
- Automatic tool discovery and registration
- Access to instance variables in tool methods
- Easy testing and mocking

WHEN TO USE
-----------
- Building agents with domain-specific functionality
- When you need stateful tools that access instance data
- Production agents with clear responsibilities

QUICK START
-----------
1. Subclass BaseAgent:

    class MyAgent(BaseAgent):
        def __init__(self):
            super().__init__(
                name="MyAgent",
                system_prompt="You are a helpful assistant.",
                model="gpt-4o-mini"
            )

2. Add tools with the decorator:

    @AgentToolkit.register_as_tool
    def my_tool(self, param: str) -> dict:
        '''
        Tool description for the LLM.

        Args:
            param (str): Description of parameter

        Returns:
            Description of return value
        '''
        return {"result": param}

3. Run the agent:

    agent = MyAgent()
    result = await agent.run("Do something")

NO API KEY REQUIRED
-------------------
This example includes a tool introspection demo that runs without an API key.
Uncomment the agent.run() lines to test with a real OpenAI API key.

To run:
    python examples/inheritance_example.py
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from fractal import BaseAgent, AgentToolkit

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


# =============================================================================
# Pydantic Models for Structured Return Types
# =============================================================================

class WeatherData(BaseModel):
    """Weather information for a location."""
    location: str
    temperature: float
    condition: str


# =============================================================================
# Example Agent: Weather Service
# =============================================================================

class WeatherAgent(BaseAgent):
    """
    An agent that provides weather information.

    This demonstrates:
    - Subclassing BaseAgent
    - Using @AgentToolkit.register_as_tool decorator
    - Accessing instance state (self.weather_db) in tools
    - Returning Pydantic models from tools
    """

    def __init__(self, client: OpenAI = None):
        super().__init__(
            name="WeatherAgent",
            system_prompt="""You are a helpful weather assistant.
            You can provide weather information for various cities.
            Always be friendly and informative.""",
            model="gpt-4o-mini",
            client=client if client is not None else OpenAI(),
            temperature=0.7
        )
        # Instance state - tools can access this via self
        self.weather_db = {
            "Tokyo": WeatherData(location="Tokyo", temperature=28.0, condition="Sunny"),
            "London": WeatherData(location="London", temperature=15.0, condition="Rainy"),
            "New York": WeatherData(location="New York", temperature=22.0, condition="Cloudy"),
        }

    @AgentToolkit.register_as_tool
    def get_weather(self, location: str) -> WeatherData:
        """
        Get current weather for a location.

        Args:
            location (str): City name to get weather for

        Returns:
            Weather data including temperature and conditions
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
    def list_cities(self) -> list:
        """
        Get list of available cities.

        Returns:
            List of city names with weather data
        """
        return list(self.weather_db.keys())


# =============================================================================
# Main: Demonstrate Tool Introspection
# =============================================================================

def main():
    """Run the inheritance pattern example."""
    print("=" * 70)
    print("Agent Inheritance Pattern Example")
    print("=" * 70)

    # Create the agent
    agent = WeatherAgent()

    # 1. Show registered tools
    print("\n[1] Registered Tools")
    print("-" * 40)
    tools = agent.get_tools()
    print(f"Agent '{agent.name}' has {len(tools)} tools:")
    for tool_name in tools.keys():
        print(f"  - {tool_name}")

    # 2. Show tool schemas (what the LLM sees)
    print("\n[2] Tool Schemas (for LLM)")
    print("-" * 40)
    schemas = agent.get_tool_schemas()
    for schema in schemas:
        func = schema['function']
        print(f"\nTool: {func['name']}")
        print(f"  Description: {func['description']}")
        params = func['parameters']['properties']
        if params:
            print(f"  Parameters:")
            for param_name, param_info in params.items():
                print(f"    - {param_name}: {param_info.get('type', 'any')}")
        else:
            print("  Parameters: (none)")

    # 3. Direct tool execution (no LLM needed)
    print("\n[3] Direct Tool Execution")
    print("-" * 40)
    result = agent.toolkit.execute_tool("get_weather", location="Tokyo")
    print(f"get_weather('Tokyo') returned:")
    print(f"  {result.content.model_dump_json(indent=2)}")

    result = agent.toolkit.execute_tool("list_cities")
    print(f"\nlist_cities() returned:")
    print(f"  {result.content}")

    # 4. Run with LLM (requires API key)
    print("\n[4] Run with LLM")
    print("-" * 40)
    if os.getenv("OPENAI_API_KEY"):
        print("API key found! Running agent...")
        result = agent.run("What's the weather like in Tokyo?")
        print(f"Agent response: {result.content}")
    else:
        print("No OPENAI_API_KEY set.")
        print("To run with LLM, add your API key to .env file.")
        print("\nExample (commented out):")
        print('  # result = agent.run("What\'s the weather like in Tokyo?")')

    print("\n" + "=" * 70)
    print("[OK] Inheritance pattern example completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
