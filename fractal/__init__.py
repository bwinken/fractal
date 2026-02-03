"""
Fractal - Self-similar agent decomposition

Build complex agent systems through elegant delegation patterns.
Just as fractals create complexity through repeated simple patterns,
Fractal creates powerful agent workflows through recursive delegation.
"""

from .agent import BaseAgent
from .toolkit import AgentToolkit
from .models import AgentReturnPart, ToolReturnPart
from .parser import parse_google_docstring, function_to_tool_schema
from .observability import TracingKit, TraceEvent

__version__ = "0.1.0"

__all__ = [
    "BaseAgent",
    "AgentToolkit",
    "AgentReturnPart",
    "ToolReturnPart",
    "parse_google_docstring",
    "function_to_tool_schema",
    "TracingKit",
    "TraceEvent",
]
