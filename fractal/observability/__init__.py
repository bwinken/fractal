"""
Observability module for agent execution monitoring and visualization.

This module provides:
- TracingKit: Execution tracing and monitoring
- HTML Visualizer: Interactive web-based visualization
- Terminal Viewer: ASCII art terminal visualization
"""

from .tracing import TracingKit, TraceEvent

__all__ = [
    'TracingKit',
    'TraceEvent',
]
