"""
Fractal - Self-similar agent decomposition

Build complex agent systems through elegant delegation patterns.
Just as fractals create complexity through repeated simple patterns,
Fractal creates powerful agent workflows through recursive delegation.
"""

from .agent import BaseAgent
from .toolkit import AgentToolkit
from .models import AgentResult, ToolResult, AgentReturnPart, ToolReturnPart
from .observability import TracingKit, TraceEvent

# Convenient alias: @tool instead of @AgentToolkit.register_as_tool
tool = AgentToolkit.register_as_tool

__version__ = "0.1.0"

__all__ = [
    "BaseAgent",
    "AgentToolkit",
    "AgentResult",
    "ToolResult",
    "TracingKit",
    "TraceEvent",
    "tool",
    # Backwards-compatible aliases
    "AgentReturnPart",
    "ToolReturnPart",
]
