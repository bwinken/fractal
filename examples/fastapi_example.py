"""
FastAPI integration example for Fractal.

This example demonstrates how to integrate async agents with FastAPI
to build agentic backend services.

To run this example:
    pip install fastapi uvicorn
    python examples/fastapi_example.py

Then visit http://localhost:8000/docs for interactive API documentation.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from fractal import BaseAgent, AgentToolkit

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Set dummy API key for testing (comment out if using real API)
os.environ["OPENAI_API_KEY"] = "sk-test-dummy-key-for-testing"

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    import uvicorn
except ImportError:
    print("Error: FastAPI not installed. Install it with: pip install fastapi uvicorn")
    exit(1)


# Pydantic models for API requests/responses
class QueryRequest(BaseModel):
    """API request for querying data."""
    query: str = Field(..., description="Query string")
    max_iterations: int = Field(default=10, description="Maximum agent iterations")


class QueryResponse(BaseModel):
    """API response with agent result."""
    agent_name: str
    content: str
    success: bool
    metadata: dict


class DatabaseRecord(BaseModel):
    """Database record model."""
    id: int
    name: str
    age: int
    city: str


class SearchResult(BaseModel):
    """Search result model."""
    query: str
    results: list
    count: int


# Define the async agent
class DataAgent(BaseAgent):
    """Agent for handling data queries."""

    def __init__(self, client=None):
        super().__init__(
            name="DataAgent",
            system_prompt="""You are a data assistant that helps users query and analyze data.
            You have access to a database with user records.
            Always be helpful and provide clear, structured responses.""",
            model="gpt-4o-mini",
            client=client if client is not None else AsyncOpenAI()
        )
        # Sample data
        self.records = [
            {"id": 1, "name": "Alice", "age": 30, "city": "New York"},
            {"id": 2, "name": "Bob", "age": 25, "city": "San Francisco"},
            {"id": 3, "name": "Charlie", "age": 35, "city": "New York"},
            {"id": 4, "name": "Diana", "age": 28, "city": "Boston"},
            {"id": 5, "name": "Eve", "age": 32, "city": "San Francisco"},
        ]

    @AgentToolkit.register_as_tool
    async def search_by_name(self, name: str) -> SearchResult:
        """
        Search records by name.

        Args:
            name (str): Name to search for (case-insensitive)

        Returns:
            Search results
        """
        # Simulate async database query
        import asyncio
        await asyncio.sleep(0.05)

        results = [r for r in self.records if name.lower() in r["name"].lower()]
        return SearchResult(
            query=f"name contains '{name}'",
            results=results,
            count=len(results)
        )

    @AgentToolkit.register_as_tool
    async def search_by_city(self, city: str) -> SearchResult:
        """
        Search records by city.

        Args:
            city (str): City name

        Returns:
            Search results
        """
        import asyncio
        await asyncio.sleep(0.05)

        results = [r for r in self.records if city.lower() in r["city"].lower()]
        return SearchResult(
            query=f"city = '{city}'",
            results=results,
            count=len(results)
        )

    @AgentToolkit.register_as_tool
    async def search_by_age_range(self, min_age: int, max_age: int) -> SearchResult:
        """
        Search records by age range.

        Args:
            min_age (int): Minimum age
            max_age (int): Maximum age

        Returns:
            Search results
        """
        import asyncio
        await asyncio.sleep(0.05)

        results = [r for r in self.records if min_age <= r["age"] <= max_age]
        return SearchResult(
            query=f"age between {min_age} and {max_age}",
            results=results,
            count=len(results)
        )

    @AgentToolkit.register_as_tool
    def get_statistics(self) -> dict:
        """
        Get database statistics.

        Returns:
            Statistics about the data
        """
        cities = set(r["city"] for r in self.records)
        avg_age = sum(r["age"] for r in self.records) / len(self.records)

        return {
            "total_records": len(self.records),
            "unique_cities": len(cities),
            "cities": list(cities),
            "average_age": round(avg_age, 2)
        }


# Create FastAPI app
app = FastAPI(
    title="Agentic Framework FastAPI Example",
    description="Example API using async agents for data queries",
    version="1.0.0"
)

# Global agent instance (in production, consider using dependency injection)
agent = DataAgent()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Agentic Framework FastAPI Example",
        "docs": "/docs",
        "agent": agent.name,
        "tools": list(agent.get_tools().keys())
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "agent": agent.name}


@app.get("/tools")
async def list_tools():
    """List available tools."""
    tools = agent.get_tools()
    tool_schemas = agent.get_tool_schemas()

    return {
        "count": len(tools),
        "tools": [
            {
                "name": schema["function"]["name"],
                "description": schema["function"]["description"],
                "parameters": list(schema["function"]["parameters"]["properties"].keys())
            }
            for schema in tool_schemas
        ]
    }


@app.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    """
    Query the agent with natural language.

    The agent will use its tools to answer your question.
    """
    try:
        # Run the agent asynchronously
        result = await agent.run(
            user_input=request.query,
            max_iterations=request.max_iterations
        )

        # Convert content to string if needed
        content = result.content
        if not isinstance(content, str):
            import json
            if isinstance(content, BaseModel):
                content = content.model_dump_json(indent=2)
            else:
                content = json.dumps(content, indent=2)

        return QueryResponse(
            agent_name=result.agent_name,
            content=content,
            success=result.success,
            metadata=result.metadata or {}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/name")
async def search_by_name(name: str):
    """Direct tool call: Search by name."""
    try:
        result = await agent.execute_tool("search_by_name", name=name)
        if result.error:
            raise HTTPException(status_code=500, detail=result.error)
        return result.content.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/city")
async def search_by_city(city: str):
    """Direct tool call: Search by city."""
    try:
        result = await agent.execute_tool("search_by_city", city=city)
        if result.error:
            raise HTTPException(status_code=500, detail=result.error)
        return result.content.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/statistics")
async def get_statistics():
    """Direct tool call: Get statistics."""
    try:
        result = await agent.execute_tool("get_statistics")
        if result.error:
            raise HTTPException(status_code=500, detail=result.error)
        return result.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/info")
async def agent_info():
    """Get agent information."""
    return {
        "name": agent.name,
        "model": agent.model,
        "temperature": agent.temperature,
        "tools": list(agent.get_tools().keys()),
        "tool_count": len(agent.get_tools())
    }


def main():
    """Run the FastAPI server."""
    print("\n" + "=" * 70)
    print("FastAPI Agentic Backend Example")
    print("=" * 70)
    print(f"\nAgent: {agent.name}")
    print(f"Tools: {list(agent.get_tools().keys())}")
    print("\nStarting server...")
    print("  API docs: http://localhost:8000/docs")
    print("  Health: http://localhost:8000/health")
    print("=" * 70 + "\n")

    # Run server
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
