"""
Multi-Agent FastAPI Example

This example demonstrates how to build a multi-agent system in FastAPI
where agents can collaborate and delegate tasks to each other.

Architecture:
- Router Agent: Main agent that routes queries to specialists
- Research Agent: Handles research and data gathering
- Analysis Agent: Handles data analysis and insights
- Report Agent: Generates formatted reports

To run:
    pip install fastapi uvicorn
    python examples/fastapi_multiagent.py

Visit http://localhost:8000/docs for API documentation
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from fractal import BaseAgent, AgentToolkit

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

try:
    from fastapi import FastAPI, HTTPException
    import uvicorn
except ImportError:
    print("Error: FastAPI not installed. Install with: pip install fastapi uvicorn")
    exit(1)


# ============================================================================
# Pydantic Models for API
# ============================================================================

class QueryRequest(BaseModel):
    """Request model for queries."""
    query: str = Field(..., description="Query to process")
    max_iterations: int = Field(default=10, description="Max iterations")


class QueryResponse(BaseModel):
    """Response model with agent result."""
    agent_name: str
    content: str
    success: bool
    metadata: dict


# ============================================================================
# Specialist Agents
# ============================================================================

class ResearchAgent(BaseAgent):
    """Agent specialized in research and data gathering."""

    def __init__(self, client=None):
        super().__init__(
            name="ResearchAgent",
            system_prompt="""You are a research specialist.
            Your job is to gather and organize information about topics.
            Be thorough and cite sources when possible.""",
            model="gpt-4o-mini",
            client=client if client is not None else AsyncOpenAI()
        )

    @AgentToolkit.register_as_tool
    async def search_database(self, topic: str) -> dict:
        """
        Search internal database for information.

        Args:
            topic (str): Topic to search for

        Returns:
            Search results
        """
        # Simulate database search
        import asyncio
        await asyncio.sleep(0.1)

        # Mock data
        return {
            "topic": topic,
            "results": [
                f"Research paper about {topic}",
                f"Recent developments in {topic}",
                f"Expert opinions on {topic}"
            ],
            "source": "Internal Database"
        }

    @AgentToolkit.register_as_tool
    def get_facts(self, topic: str) -> list:
        """
        Get key facts about a topic.

        Args:
            topic (str): Topic to get facts about

        Returns:
            List of facts
        """
        return [
            f"Fact 1 about {topic}",
            f"Fact 2 about {topic}",
            f"Fact 3 about {topic}"
        ]


class AnalysisAgent(BaseAgent):
    """Agent specialized in data analysis."""

    def __init__(self, client=None):
        super().__init__(
            name="AnalysisAgent",
            system_prompt="""You are an analysis specialist.
            Your job is to analyze data, identify patterns, and provide insights.
            Be analytical and data-driven.""",
            model="gpt-4o-mini",
            client=client if client is not None else AsyncOpenAI()
        )

    @AgentToolkit.register_as_tool
    async def analyze_data(self, data: str) -> dict:
        """
        Analyze provided data.

        Args:
            data (str): Data to analyze

        Returns:
            Analysis results
        """
        import asyncio
        await asyncio.sleep(0.1)

        return {
            "data_summary": f"Analyzed: {data[:50]}...",
            "insights": [
                "Key insight 1 from the data",
                "Key insight 2 from the data",
                "Recommendation based on analysis"
            ],
            "confidence": 0.85
        }

    @AgentToolkit.register_as_tool
    def calculate_metrics(self, data_points: int) -> dict:
        """
        Calculate key metrics.

        Args:
            data_points (int): Number of data points

        Returns:
            Calculated metrics
        """
        return {
            "total_points": data_points,
            "average": data_points / 2,
            "trend": "increasing"
        }


class ReportAgent(BaseAgent):
    """Agent specialized in generating reports."""

    def __init__(self, client=None):
        super().__init__(
            name="ReportAgent",
            system_prompt="""You are a report generation specialist.
            Your job is to take information and create well-formatted reports.
            Be clear, concise, and professional.""",
            model="gpt-4o-mini",
            client=client if client is not None else AsyncOpenAI()
        )

    @AgentToolkit.register_as_tool
    def format_report(self, title: str, content: str) -> str:
        """
        Format content into a professional report.

        Args:
            title (str): Report title
            content (str): Report content

        Returns:
            Formatted report
        """
        return f"""
# {title}

## Executive Summary
{content[:200]}...

## Detailed Findings
{content}

## Conclusion
Based on the analysis above, we recommend further action.

---
*Report generated by ReportAgent*
        """.strip()


# ============================================================================
# Router Agent (Main Coordinator)
# ============================================================================

class RouterAgent(BaseAgent):
    """Main agent that routes tasks to specialists."""

    def __init__(self, research_agent, analysis_agent, report_agent, client=None):
        super().__init__(
            name="RouterAgent",
            system_prompt="""You are the main coordinator agent.
            Your job is to understand user queries and delegate to specialist agents:
            - Use ResearchAgent for information gathering and research
            - Use AnalysisAgent for data analysis and insights
            - Use ReportAgent for generating formatted reports

            Coordinate between agents to provide comprehensive answers.
            Always explain what you're doing and why.""",
            model="gpt-4o-mini",
            client=client if client is not None else AsyncOpenAI()
        )

        # Register specialist agents as delegates (subordinates)
        self.register_delegate(
            research_agent,
            tool_name="delegate_to_research",
            description="Delegate research and information gathering tasks to ResearchAgent"
        )

        self.register_delegate(
            analysis_agent,
            tool_name="delegate_to_analysis",
            description="Delegate data analysis tasks to AnalysisAgent"
        )

        self.register_delegate(
            report_agent,
            tool_name="delegate_to_report",
            description="Delegate report generation tasks to ReportAgent"
        )

    @AgentToolkit.register_as_tool
    def route_query(self, query: str, target: str) -> str:
        """
        Route a query to a specific specialist.

        Args:
            query (str): Query to route
            target (str): Target agent (research/analysis/report)

        Returns:
            Routing confirmation
        """
        return f"Routing '{query}' to {target} agent..."


# ============================================================================
# FastAPI Application with Multi-Agent System
# ============================================================================

# Global agent instances
agents = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize agents on startup."""
    print("🚀 Initializing multi-agent system...")

    # Create specialist agents
    research_agent = ResearchAgent()
    analysis_agent = AnalysisAgent()
    report_agent = ReportAgent()

    # Create router agent with access to specialists
    router_agent = RouterAgent(
        research_agent=research_agent,
        analysis_agent=analysis_agent,
        report_agent=report_agent
    )

    # Store in global dict
    agents['router'] = router_agent
    agents['research'] = research_agent
    agents['analysis'] = analysis_agent
    agents['report'] = report_agent

    print(f"✅ Router Agent: {len(router_agent.get_tools())} tools")
    print(f"✅ Research Agent: {len(research_agent.get_tools())} tools")
    print(f"✅ Analysis Agent: {len(analysis_agent.get_tools())} tools")
    print(f"✅ Report Agent: {len(report_agent.get_tools())} tools")
    print("🎉 Multi-agent system ready!\n")

    yield

    # Cleanup
    print("🛑 Shutting down multi-agent system...")


app = FastAPI(
    title="Multi-Agent System API",
    description="FastAPI application with collaborative AI agents",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint with system info."""
    return {
        "message": "Multi-Agent System API",
        "agents": {
            name: {
                "tools": len(agent.get_tools()),
                "model": agent.model
            }
            for name, agent in agents.items()
        },
        "docs": "/docs"
    }


@app.get("/agents")
async def list_agents():
    """List all available agents."""
    return {
        "agents": [
            {
                "name": name,
                "type": agent.name,
                "tools": list(agent.get_tools().keys()),
                "tool_count": len(agent.get_tools())
            }
            for name, agent in agents.items()
        ]
    }


@app.post("/query", response_model=QueryResponse)
async def query_router(request: QueryRequest):
    """
    Send a query to the router agent.

    The router will automatically delegate to specialist agents as needed.
    """
    try:
        router = agents['router']
        result = await router.run(
            user_input=request.query,
            max_iterations=request.max_iterations
        )

        # Convert content to string
        content = result.content
        if not isinstance(content, str):
            import json
            from pydantic import BaseModel
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


@app.post("/direct/{agent_name}")
async def query_direct(agent_name: str, request: QueryRequest):
    """
    Query a specific agent directly (bypassing router).
    """
    if agent_name not in agents:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_name}' not found. Available: {list(agents.keys())}"
        )

    try:
        agent = agents[agent_name]
        result = await agent.run(
            user_input=request.query,
            max_iterations=request.max_iterations
        )

        content = result.content
        if not isinstance(content, str):
            import json
            from pydantic import BaseModel
            if isinstance(content, BaseModel):
                content = content.model_dump_json(indent=2)
            else:
                content = json.dumps(content, indent=2)

        return {
            "agent_name": result.agent_name,
            "content": content,
            "success": result.success,
            "metadata": result.metadata
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "agents": len(agents),
        "agent_names": list(agents.keys())
    }


def main():
    """Run the server."""
    print("\n" + "=" * 70)
    print("Multi-Agent FastAPI System")
    print("=" * 70)
    print("\nArchitecture:")
    print("  - RouterAgent: Main coordinator")
    print("  - ResearchAgent: Information gathering")
    print("  - AnalysisAgent: Data analysis")
    print("  - ReportAgent: Report generation")
    print("\nStarting server...")
    print("  API docs: http://localhost:8000/docs")
    print("  Agents: http://localhost:8000/agents")
    print("=" * 70 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
