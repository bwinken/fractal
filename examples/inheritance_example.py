"""
Example demonstrating agent inheritance pattern.

This example shows how to create custom agents by inheriting from BaseAgent
and using the @AgentToolkit.register_as_tool decorator on member methods.
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


# Define data models
class WeatherData(BaseModel):
    """Weather information."""
    location: str
    temperature: float
    condition: str


class MathResult(BaseModel):
    """Math calculation result."""
    expression: str
    result: float


# Example 1: Weather Agent with member function tools
class WeatherAgent(BaseAgent):
    """Agent that provides weather information."""

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
        # Initialize weather database
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
            location (str): City name

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


# Example 2: Math Agent with calculation tools
class MathAgent(BaseAgent):
    """Agent that performs mathematical calculations."""

    def __init__(self, client: OpenAI = None):
        super().__init__(
            name="MathAgent",
            system_prompt="""You are a mathematical assistant.
            You can perform various calculations and provide mathematical insights.""",
            model="gpt-4o-mini",
            client=client if client is not None else OpenAI(),
            temperature=0.3
        )

    @AgentToolkit.register_as_tool
    def add(self, a: float, b: float) -> MathResult:
        """
        Add two numbers.

        Args:
            a (float): First number
            b (float): Second number

        Returns:
            Calculation result
        """
        result = a + b
        return MathResult(expression=f"{a} + {b}", result=result)

    @AgentToolkit.register_as_tool
    def multiply(self, a: float, b: float) -> MathResult:
        """
        Multiply two numbers.

        Args:
            a (float): First number
            b (float): Second number

        Returns:
            Calculation result
        """
        result = a * b
        return MathResult(expression=f"{a} × {b}", result=result)

    @AgentToolkit.register_as_tool
    def power(self, base: float, exponent: float) -> MathResult:
        """
        Calculate base raised to exponent.

        Args:
            base (float): Base number
            exponent (float): Exponent

        Returns:
            Calculation result
        """
        result = base ** exponent
        return MathResult(expression=f"{base}^{exponent}", result=result)


def example_weather_agent():
    """Example using WeatherAgent."""
    print("=" * 60)
    print("Example 1: Weather Agent with Inherited Tools")
    print("=" * 60)

    agent = WeatherAgent()

    # Check what tools are registered
    tools = agent.get_tools()
    print(f"\nRegistered tools: {list(tools.keys())}")

    # Run the agent
    result = agent.run("What's the weather like in Tokyo?")
    print(f"\nAgent Response:\n{result.content}")

    print("\n" + "=" * 60)


def example_math_agent():
    """Example using MathAgent."""
    print("\nExample 2: Math Agent with Calculation Tools")
    print("=" * 60)

    agent = MathAgent()

    # Check registered tools
    tools = agent.get_tools()
    print(f"\nRegistered tools: {list(tools.keys())}")

    # Run the agent
    result = agent.run("Calculate 5 to the power of 3, then add 10 to the result")
    print(f"\nAgent Response:\n{result.content}")

    print("\n" + "=" * 60)


def example_tool_introspection():
    """Example showing tool introspection."""
    print("\nExample 3: Tool Introspection")
    print("=" * 60)

    agent = WeatherAgent()

    # Get tool schemas (what the LLM sees)
    schemas = agent.get_tool_schemas()
    print(f"\nNumber of tools: {len(schemas)}")

    for schema in schemas:
        func = schema['function']
        print(f"\nTool: {func['name']}")
        print(f"Description: {func['description']}")
        print(f"Parameters: {list(func['parameters']['properties'].keys())}")

    print("\n" + "=" * 60)


def main():
    """Run all examples."""
    print("\nAgent Inheritance Pattern Examples\n")

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("WARNING:  Warning: OPENAI_API_KEY not set.")
        print("Set it in the .env file to run agent examples.\n")

    # Run introspection example (doesn't need API key)
    try:
        example_tool_introspection()
        print("\n[OK] Introspection example completed!\n")
    except Exception as e:
        print(f"\n[ERROR] Error in introspection example: {e}\n")

    # Uncomment to run agent examples (requires API key)
    # try:
    #     example_weather_agent()
    #     print("\n[OK] Weather agent example completed!\n")
    # except Exception as e:
    #     print(f"\n[ERROR] Error in weather agent example: {e}\n")

    # try:
    #     example_math_agent()
    #     print("\n[OK] Math agent example completed!\n")
    # except Exception as e:
    #     print(f"\n[ERROR] Error in math agent example: {e}\n")


if __name__ == "__main__":
    main()
