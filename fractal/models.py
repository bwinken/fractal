"""
Pydantic models for agent communication and data exchange.
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class ToolResult(BaseModel):
    """
    Wrapper for tool execution output.

    Contains the return value from a tool execution,
    along with metadata and error information.
    """
    content: Union[str, dict, list, List[BaseModel], BaseModel] = Field(
        ...,
        description="Tool output: str, dict, list, List[BaseModel], or BaseModel"
    )
    tool_name: str = Field(..., description="Name of the tool that generated this output")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata about the tool execution")
    error: Optional[str] = Field(default=None, description="Error message if tool execution failed")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AgentResult(BaseModel):
    """
    Wrapper for an agent's final response.

    Returned by agent.run(), contains the agent's output along with
    execution metadata and success status.
    """
    content: Union[str, dict, list, List[BaseModel], BaseModel] = Field(
        ...,
        description="Agent output: str, dict, list, List[BaseModel], or BaseModel"
    )
    agent_name: str = Field(..., description="Name of the agent that generated this output")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata about the agent's response")
    success: bool = Field(default=True, description="Whether the agent execution was successful")

    model_config = ConfigDict(arbitrary_types_allowed=True)


# Backwards-compatible aliases
ToolReturnPart = ToolResult
AgentReturnPart = AgentResult
