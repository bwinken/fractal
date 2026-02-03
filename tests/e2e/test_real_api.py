"""
Real API test - uses actual OpenAI API to verify everything works.
Make sure you have set OPENAI_API_KEY in your .env file.
"""
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
from fractal import BaseAgent, AgentToolkit
from pydantic import BaseModel

# Load .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class WeatherData(BaseModel):
    """Weather data model."""
    location: str
    temperature: float
    condition: str
    description: str


class RealWorldAgent(BaseAgent):
    """Agent for real-world testing with actual API."""

    def __init__(self):
        # Check API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key.startswith("sk-test-"):
            raise ValueError("Please set a real OPENAI_API_KEY in .env file")

        super().__init__(
            name="RealWorldAgent",
            system_prompt="""You are a helpful assistant that provides weather information.
            When asked about weather, use the get_weather tool to get the data.
            Always be friendly and provide complete information.""",
            model="gpt-4o-mini",
            client=AsyncOpenAI(),
            temperature=0.7
        )

        # Sample data
        self.weather_db = {
            "Tokyo": WeatherData(
                location="Tokyo",
                temperature=28.0,
                condition="Sunny",
                description="Clear skies with light breeze"
            ),
            "London": WeatherData(
                location="London",
                temperature=15.0,
                condition="Rainy",
                description="Light rain throughout the day"
            ),
            "New York": WeatherData(
                location="New York",
                temperature=22.0,
                condition="Cloudy",
                description="Partly cloudy with occasional sunshine"
            ),
        }

    @AgentToolkit.register_as_tool
    def get_weather(self, location: str) -> WeatherData:
        """
        Get current weather for a location.

        Args:
            location (str): City name

        Returns:
            Weather information including temperature and conditions
        """
        # Sync tool
        location_key = location.title()
        if location_key in self.weather_db:
            return self.weather_db[location_key]
        else:
            return WeatherData(
                location=location,
                temperature=20.0,
                condition="Unknown",
                description="Weather data not available for this location"
            )

    @AgentToolkit.register_as_tool
    async def get_forecast(self, location: str, days: int = 3) -> dict:
        """
        Get weather forecast for multiple days.

        Args:
            location (str): City name
            days (int): Number of days to forecast

        Returns:
            Forecast data
        """
        # Async tool with simulated I/O
        await asyncio.sleep(0.05)

        return {
            "location": location,
            "days": days,
            "forecast": [
                {"day": i + 1, "temp": 20 + i, "condition": "Sunny"}
                for i in range(days)
            ]
        }

    @AgentToolkit.register_as_tool
    def list_cities(self) -> list:
        """
        List all available cities.

        Returns:
            List of city names
        """
        return list(self.weather_db.keys())


async def test_basic_query():
    """Test 1: Basic query with tool calling."""
    print("=" * 70)
    print("Test 1: Basic Query with Tool Calling")
    print("=" * 70)

    try:
        agent = RealWorldAgent()

        print(f"\nAgent: {agent.name}")
        print(f"Model: {agent.model}")
        print(f"Tools: {list(agent.get_tools().keys())}")

        print("\n[Query] What's the weather like in Tokyo?")

        result = await agent.run(
            "What's the weather like in Tokyo?",
            max_iterations=5
        )

        print(f"\n[Response]")
        print(f"Success: {result.success}")
        print(f"Agent: {result.agent_name}")
        print(f"Content: {result.content}")
        print(f"Metadata: {result.metadata}")

        assert result.success, "Query should succeed"
        assert "Tokyo" in result.content or "28" in result.content, "Should mention Tokyo weather"

        print("\n[OK] Basic query works!")
        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multiple_tool_calls():
    """Test 2: Query that requires multiple tool calls."""
    print("\n" + "=" * 70)
    print("Test 2: Multiple Tool Calls")
    print("=" * 70)

    try:
        agent = RealWorldAgent()

        print("\n[Query] Compare the weather in Tokyo and London")

        result = await agent.run(
            "Compare the weather in Tokyo and London. Which is warmer?",
            max_iterations=10
        )

        print(f"\n[Response]")
        print(f"Success: {result.success}")
        print(f"Content: {result.content}")
        print(f"Iterations: {result.metadata.get('iterations', 'N/A')}")

        assert result.success, "Query should succeed"

        print("\n[OK] Multiple tool calls work!")
        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_async_tool():
    """Test 3: Using async tool."""
    print("\n" + "=" * 70)
    print("Test 3: Async Tool Usage")
    print("=" * 70)

    try:
        agent = RealWorldAgent()

        print("\n[Query] Get a 5-day forecast for New York")

        result = await agent.run(
            "Can you give me a 5-day weather forecast for New York?",
            max_iterations=5
        )

        print(f"\n[Response]")
        print(f"Success: {result.success}")
        print(f"Content: {result.content}")

        assert result.success, "Query should succeed"

        print("\n[OK] Async tool works!")
        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_list_cities():
    """Test 4: List tool returning array."""
    print("\n" + "=" * 70)
    print("Test 4: Tool Returning List")
    print("=" * 70)

    try:
        agent = RealWorldAgent()

        print("\n[Query] What cities do you have weather data for?")

        result = await agent.run(
            "What cities do you have weather data for?",
            max_iterations=5
        )

        print(f"\n[Response]")
        print(f"Success: {result.success}")
        print(f"Content: {result.content}")

        assert result.success, "Query should succeed"

        print("\n[OK] List return works!")
        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_pydantic_model_return():
    """Test 5: Tool returning Pydantic model."""
    print("\n" + "=" * 70)
    print("Test 5: Pydantic Model Return")
    print("=" * 70)

    try:
        agent = RealWorldAgent()

        # Direct tool call to verify Pydantic return
        print("\n[Direct Tool Call] get_weather(location='London')")

        result = await agent.execute_tool("get_weather", location="London")

        print(f"\nTool Result:")
        print(f"Type: {type(result.content)}")
        print(f"Content: {result.content}")

        assert isinstance(result.content, WeatherData), "Should return WeatherData model"
        assert result.content.location == "London"

        print("\n[OK] Pydantic model return works!")
        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_handling():
    """Test 6: Error handling."""
    print("\n" + "=" * 70)
    print("Test 6: Error Handling")
    print("=" * 70)

    try:
        agent = RealWorldAgent()

        print("\n[Query] What's the weather in NonExistentCity?")

        result = await agent.run(
            "What's the weather in NonExistentCity?",
            max_iterations=5
        )

        print(f"\n[Response]")
        print(f"Success: {result.success}")
        print(f"Content: {result.content}")

        # Should still succeed but return "Unknown" weather
        print("\n[OK] Error handling works!")
        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all real API tests."""
    print("\n" + "=" * 70)
    print("Real API Test Suite")
    print("=" * 70)

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n[ERROR] OPENAI_API_KEY not found in .env file")
        print("Please set your API key in .env file")
        return

    if api_key.startswith("sk-test-"):
        print("\n[ERROR] Found test API key")
        print("Please set a real OPENAI_API_KEY in .env file")
        return

    print(f"\nAPI Key: {api_key[:8]}...{api_key[-4:]}")
    print(f"Model: gpt-4o-mini")
    print("\n" + "=" * 70 + "\n")

    results = []

    # Run tests
    tests = [
        ("Basic Query", test_basic_query),
        ("Multiple Tool Calls", test_multiple_tool_calls),
        ("Async Tool", test_async_tool),
        ("List Return", test_list_cities),
        ("Pydantic Model", test_pydantic_model_return),
        ("Error Handling", test_error_handling),
    ]

    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n[CRITICAL ERROR in {name}] {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")

    print(f"\nTotal: {passed}/{total} passed")

    if passed == total:
        print("\n[SUCCESS] All real API tests passed!")
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
