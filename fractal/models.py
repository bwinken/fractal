"""
Pydantic models for agent communication and data exchange.
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ToolReturnPart(BaseModel):
    """
    Wrapper for tool output within an agent.

    This is used to wrap the return value from a tool execution,
    allowing for structured data passing with metadata.
    """
    content: Union[str, dict, list, BaseModel] = Field(..., description="The actual content returned by the tool (string, dict, list, or Pydantic model)")
    tool_name: str = Field(..., description="Name of the tool that generated this output")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata about the tool execution")
    error: Optional[str] = Field(default=None, description="Error message if tool execution failed")

    class Config:
        arbitrary_types_allowed = True


class AgentReturnPart(BaseModel):
    """
    Wrapper for data being returned from one agent to another.

    This enables agents to communicate and pass structured Pydantic objects
    between each other in a standardized way.
    """
    content: Union[str, dict, list, BaseModel] = Field(..., description="The actual content being returned to another agent (string, dict, list, or Pydantic model)")
    agent_name: str = Field(..., description="Name of the agent that generated this output")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata about the agent's response")
    success: bool = Field(default=True, description="Whether the agent execution was successful")

    class Config:
        arbitrary_types_allowed = True
