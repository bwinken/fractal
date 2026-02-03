"""
Basic example demonstrating the Fractal framework capabilities.

This example shows:
1. Creating a custom toolkit with registered tools
2. Using Google-style docstrings for tool descriptions
3. Passing Pydantic objects between tools and agents
4. Agent-to-agent communication
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field
from fractal import BaseAgent, AgentToolkit, AgentReturnPart

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


# Define Pydantic models for structured data exchange
class WeatherData(BaseModel):
    """Weather information for a location."""
    location: str = Field(..., description="Location name")
    temperature: float = Field(..., description="Temperature in Celsius")
    condition: str = Field(..., description="Weather condition")
    humidity: int = Field(..., description="Humidity percentage")


class TravelRecommendation(BaseModel):
    """Travel recommendation based on weather."""
    destination: str = Field(..., description="Recommended destination")
    reason: str = Field(..., description="Reason for recommendation")
    best_time: str = Field(..., description="Best time to visit")


# Create a custom toolkit
class WeatherToolkit(AgentToolkit):
    """Toolkit for weather-related operations."""

    def __init__(self):
        super().__init__()
        self.weather_db = {
            "New York": WeatherData(
                location="New York",
                temperature=22.5,
                condition="Sunny",
                humidity=65
            ),
            "London": WeatherData(
                location="London",
                temperature=15.0,
                condition="Rainy",
                humidity=80
            ),
            "Tokyo": WeatherData(
                location="Tokyo",
                temperature=28.0,
                condition="Cloudy",
                humidity=70
            )
        }

    @AgentToolkit.register_as_tool
    def get_weather(self, location: str) -> WeatherData:
        """
        Get current weather information for a location.

        Args:
            location (str): The name of the city to get weather for

        Returns:
            WeatherData object containing temperature, condition, and humidity
        """
        if location in self.weather_db:
            return self.weather_db[location]
        else:
            return WeatherData(
                location=location,
                temperature=20.0,
                condition="Unknown",
                humidity=50
            )

    @AgentToolkit.register_as_tool
    def compare_weather(self, location1: str, location2: str) -> dict:
        """
        Compare weather between two locations.

        Args:
            location1 (str): First location to compare
            location2 (str): Second location to compare

        Returns:
            Comparison result with temperature differences
        """
        weather1 = self.get_weather(location1)
        weather2 = self.get_weather(location2)

        temp_diff = weather1.temperature - weather2.temperature

        return {
            "location1": weather1.model_dump(),
            "location2": weather2.model_dump(),
            "temperature_difference": temp_diff,
            "warmer_location": location1 if temp_diff > 0 else location2
        }

    @AgentToolkit.register_as_tool
    def list_available_locations(self) -> list:
        """
        Get a list of all available locations in the weather database.

        Returns:
            List of location names
        """
        return list(self.weather_db.keys())


class TravelToolkit(AgentToolkit):
    """Toolkit for travel recommendations."""

    @AgentToolkit.register_as_tool
    def recommend_destination(self, weather_data: dict, preferences: str = "warm") -> TravelRecommendation:
        """
        Recommend a travel destination based on weather data.

        Args:
            weather_data (dict): Weather information for the location
            preferences (str): User preferences (warm, cool, any)

        Returns:
            TravelRecommendation with destination and reasoning
        """
        location = weather_data.get("location", "Unknown")
        temp = weather_data.get("temperature", 20)
        condition = weather_data.get("condition", "Unknown")

        if preferences == "warm" and temp > 25:
            return TravelRecommendation(
                destination=location,
                reason=f"Perfect warm weather with {temp}°C and {condition} conditions",
                best_time="Now!"
            )
        elif preferences == "cool" and temp < 20:
            return TravelRecommendation(
                destination=location,
                reason=f"Nice cool weather with {temp}°C and {condition} conditions",
                best_time="Now!"
            )
        else:
            return TravelRecommendation(
                destination=location,
                reason=f"Moderate weather with {temp}°C",
                best_time="Consider seasonal variations"
            )


def example_basic_agent():
    """
    Example 1: Basic agent with toolkit.
    """
    print("=" * 60)
    print("Example 1: Basic Agent with Weather Toolkit")
    print("=" * 60)

    # Create OpenAI client and agent
    client = OpenAI()
    weather_toolkit = WeatherToolkit()
    weather_agent = BaseAgent(
        name="WeatherBot",
        system_prompt="""You are a helpful weather assistant.
        You can provide weather information and compare weather between different locations.
        Always be concise and friendly in your responses.""",
        toolkit=weather_toolkit,
        model="gpt-4o-mini",  # Using cheaper model; change to gpt-4 for better quality
        client=client,
        temperature=0.7
    )

    # Run the agent
    result = weather_agent.run("What's the weather like in Tokyo?")

    print(f"\nAgent: {result.agent_name}")
    print(f"Success: {result.success}")
    print(f"Response:\n{result.content}")
    print(f"Metadata: {result.metadata}")


def example_agent_to_agent():
    """
    Example 2: Agent-to-agent communication with Pydantic objects.
    """
    print("\n" + "=" * 60)
    print("Example 2: Agent-to-Agent Communication")
    print("=" * 60)

    # Create OpenAI client
    client = OpenAI()

    # Create weather agent
    weather_toolkit = WeatherToolkit()
    weather_agent = BaseAgent(
        name="WeatherBot",
        system_prompt="You are a weather information provider. Return weather data in a structured format.",
        toolkit=weather_toolkit,
        model="gpt-4o-mini",
        client=client,
        temperature=0.5
    )

    # Create travel agent
    travel_toolkit = TravelToolkit()
    travel_agent = BaseAgent(
        name="TravelAdvisor",
        system_prompt="""You are a travel advisor. Based on weather information,
        recommend destinations and provide travel advice.""",
        toolkit=travel_toolkit,
        model="gpt-4o-mini",
        client=client,
        temperature=0.7
    )

    # Weather agent gets weather data
    weather_result = weather_agent.run("Get the weather for Tokyo")
    print(f"\n{weather_agent.name}: {weather_result.content}")

    # Travel agent uses weather data to make recommendations
    travel_result = travel_agent.run(
        f"Based on this weather data, recommend if I should visit Tokyo: {weather_result.content}"
    )
    print(f"\n{travel_agent.name}: {travel_result.content}")


def example_pydantic_passing():
    """
    Example 3: Direct Pydantic object passing.
    """
    print("\n" + "=" * 60)
    print("Example 3: Pydantic Object Passing")
    print("=" * 60)

    weather_toolkit = WeatherToolkit()

    # Create weather data
    weather = WeatherData(
        location="Paris",
        temperature=18.5,
        condition="Partly Cloudy",
        humidity=72
    )

    print(f"\nCreated WeatherData object:")
    print(weather.model_dump_json(indent=2))

    # Execute tool directly with Pydantic object
    tool_result = weather_toolkit.execute_tool(
        "get_weather",
        location="Tokyo"
    )

    print(f"\nTool: {tool_result.tool_name}")
    print(f"Success: {tool_result.error is None}")
    print(f"Result type: {type(tool_result.content)}")
    print(f"Result:\n{tool_result.content.model_dump_json(indent=2)}")


def main():
    """Run all examples."""
    print("\n🤖 Agentic Framework Examples\n")

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set. Agent examples may fail.")
        print("Please set it in the .env file or with: export OPENAI_API_KEY='your-key'\n")

    # Run examples
    try:
        example_pydantic_passing()
        print("\n✅ Pydantic object passing example completed!\n")
    except Exception as e:
        print(f"\n❌ Error in pydantic example: {e}\n")

    # Uncomment to run agent examples (requires API key)
    # try:
    #     example_basic_agent()
    #     print("\n✅ Basic agent example completed!\n")
    # except Exception as e:
    #     print(f"\n❌ Error in basic agent example: {e}\n")

    # try:
    #     example_agent_to_agent()
    #     print("\n✅ Agent-to-agent example completed!\n")
    # except Exception as e:
    #     print(f"\n❌ Error in agent-to-agent example: {e}\n")


if __name__ == "__main__":
    main()
