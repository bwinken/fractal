"""
Agent toolkit for registering and managing tools.
"""
import inspect
from typing import Any, Callable, Dict, List, Optional
from functools import wraps
from .parser import function_to_tool_schema
from .models import ToolReturnPart


class AgentToolkit:
    """
    Toolkit for managing agent tools.

    Member functions can be registered as tools using the @register_as_tool decorator.
    The docstring (Google format) of the member function will be parsed to generate
    tool descriptions and argument specifications for the AI agent.

    Can be used standalone or with a target object (composition pattern).
    """

    def __init__(self, target: Optional[Any] = None):
        """
        Initialize the toolkit.

        Args:
            target: Optional target object to discover tools from (e.g., an Agent instance)
        """
        self._tools: Dict[str, Callable] = {}
        self._tool_schemas: Dict[str, Dict] = {}
        self._tool_terminate: Dict[str, bool] = {}  # Track which tools terminate agent loop
        self._target = target  # Store reference to target object

        # Auto-discover tools if target is provided
        if target is not None:
            self._discover_tools()

    @staticmethod
    def register_as_tool(
        func: Optional[Callable] = None,
        *,
        name: Optional[str] = None,
        terminate: bool = False
    ) -> Callable:
        """
        Decorator to register a member function as an agent tool.

        The function's docstring (Google format) will be parsed to generate:
        - Tool description
        - Parameter descriptions and types
        - Return value description

        Args:
            func: The function to register (when used without arguments)
            name: Optional custom name for the tool (defaults to function name)
            terminate: If True, agent will exit loop and return this tool's result

        Returns:
            Decorated function with tool registration metadata

        Example::

            class MyToolkit(AgentToolkit):
                @AgentToolkit.register_as_tool
                def search_database(self, query: str, limit: int = 10):
                    # Search the database for matching records.
                    return [...]

                @AgentToolkit.register_as_tool(terminate=True)
                def final_answer(self, answer: str) -> str:
                    # Return final answer and exit agent loop.
                    return answer
        """
        def decorator(f: Callable) -> Callable:
            tool_name = name or f.__name__

            # Create appropriate wrapper based on whether function is async
            if inspect.iscoroutinefunction(f):
                @wraps(f)
                async def async_wrapper(*args, **kwargs):
                    return await f(*args, **kwargs)
                wrapper = async_wrapper
            else:
                @wraps(f)
                def sync_wrapper(*args, **kwargs):
                    return f(*args, **kwargs)
                wrapper = sync_wrapper

            # Mark function as a tool
            wrapper._is_agent_tool = True
            wrapper._tool_name = tool_name
            wrapper._tool_terminate = terminate
            wrapper._original_func = f

            return wrapper

        if func is None:
            # Called with arguments: @register_as_tool(name="custom_name")
            return decorator
        else:
            # Called without arguments: @register_as_tool
            return decorator(func)

    def register_delegate(self, agent: 'BaseAgent', tool_name: Optional[str] = None, description: Optional[str] = None):
        """
        Register another agent as a delegate for task delegation.

        This allows the current agent to delegate tasks to a subordinate/specialist agent.
        The subordinate agent will be registered as a callable tool.

        Args:
            agent (BaseAgent): The subordinate agent to register for delegation
            tool_name (str): Optional name for the delegation tool (defaults to "delegate_to_{agent.name}")
            description (str): Optional description for the tool

        Example::

            # In coordinator agent's __init__:
            specialist = SpecialistAgent()
            self.register_delegate(
                specialist,
                tool_name="ask_specialist",
                description="Delegate complex queries to the specialist agent"
            )
        """
        # Import here to avoid circular dependency
        from .models import AgentReturnPart

        # Generate tool name if not provided
        if tool_name is None:
            agent_name = getattr(agent, 'name', 'agent')
            tool_name = f"delegate_to_{agent_name.lower().replace(' ', '_')}"

        # Generate description if not provided
        if description is None:
            agent_name = getattr(agent, 'name', 'another agent')
            description = f"Delegate tasks to {agent_name} (subordinate agent)"

        # Create async wrapper that calls the other agent
        async def agent_caller(query: str) -> AgentReturnPart:
            """
            Call another agent with a query.

            Args:
                query (str): Query to send to the agent

            Returns:
                Agent's response
            """
            # Get the calling agent (if available through target)
            calling_agent = self._target

            # Check if the calling agent has tracing enabled
            if calling_agent and hasattr(calling_agent, 'tracing') and calling_agent.tracing:
                # Propagate tracing to the delegated agent ("infection" pattern)
                original_tracing = agent.tracing  # Save original tracing state
                agent.tracing = calling_agent.tracing  # Use the same TracingKit instance

                # Record delegation start
                calling_agent.tracing.start_delegation(
                    from_agent=calling_agent.name,
                    to_agent=agent.name,
                    query=query,
                    metadata={'tool_name': tool_name}
                )

                try:
                    # Execute the delegated agent
                    result = await agent.run(query)

                    # Record successful delegation end
                    calling_agent.tracing.end_delegation(
                        from_agent=calling_agent.name,
                        to_agent=agent.name,
                        result=result,
                        success=result.success if hasattr(result, 'success') else True
                    )

                    return result
                except Exception as e:
                    # Record failed delegation
                    calling_agent.tracing.end_delegation(
                        from_agent=calling_agent.name,
                        to_agent=agent.name,
                        result=None,
                        success=False,
                        metadata={'error': str(e)}
                    )
                    raise
                finally:
                    # Restore original tracing state
                    agent.tracing = original_tracing
            else:
                # No tracing - just run normally
                result = await agent.run(query)
                return result

        # Set the docstring for schema generation
        agent_caller.__doc__ = f"""{description}

        Args:
            query (str): Query or task to delegate to the agent

        Returns:
            Response from the agent
        """

        # Mark as tool and register
        agent_caller._is_agent_tool = True
        agent_caller._tool_name = tool_name
        agent_caller._tool_terminate = False
        agent_caller._original_func = agent_caller

        # Manually add to tools dict
        if not self._tools:
            self._discover_tools()

        self._tools[tool_name] = agent_caller

        # Generate and store schema
        from .parser import function_to_tool_schema
        schema = function_to_tool_schema(agent_caller)
        # Override the function name in schema with our custom tool_name
        schema['function']['name'] = tool_name
        self._tool_schemas[tool_name] = schema

    def register_agent(self, agent: 'BaseAgent', tool_name: Optional[str] = None, description: Optional[str] = None):
        """
        Deprecated: Use register_delegate() instead.

        Register another agent as a delegate for task delegation.
        This method is kept for backwards compatibility.

        Args:
            agent (BaseAgent): The subordinate agent to register for delegation
            tool_name (str): Optional name for the delegation tool
            description (str): Optional description for the tool
        """
        self.register_delegate(agent, tool_name, description)

    def get_tools(self) -> Dict[str, Callable]:
        """
        Get all registered tools in this toolkit.

        Returns:
            Dictionary mapping tool names to their callable functions
        """
        if not self._tools:
            self._discover_tools()
        return self._tools

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Get OpenAI-compatible tool schemas for all registered tools.

        Returns:
            List of tool schema dictionaries in OpenAI format
        """
        if not self._tool_schemas:
            self._discover_tools()
        return list(self._tool_schemas.values())

    def _discover_tools(self):
        """
        Discover and register all tools marked with @register_as_tool decorator.

        If a target object was provided (composition pattern), discover from target.
        Otherwise, discover from self (inheritance pattern for backwards compatibility).
        """
        # Determine which object to scan for tools
        scan_target = self._target if self._target is not None else self

        for attr_name in dir(scan_target):
            if attr_name.startswith('_'):
                continue

            attr = getattr(scan_target, attr_name)
            if callable(attr) and hasattr(attr, '_is_agent_tool'):
                tool_name = attr._tool_name
                self._tools[tool_name] = attr

                # Store termination flag
                self._tool_terminate[tool_name] = getattr(attr, '_tool_terminate', False)

                # Generate schema from the original unbound function
                schema = function_to_tool_schema(attr._original_func)
                self._tool_schemas[tool_name] = schema

    async def execute_tool(self, tool_name: str, **kwargs) -> ToolReturnPart:
        """
        Execute a registered tool by name (supports both sync and async tools).

        Args:
            tool_name (str): Name of the tool to execute
            **kwargs: Arguments to pass to the tool

        Returns:
            ToolReturnPart containing the tool's output
        """
        tools = self.get_tools()

        if tool_name not in tools:
            return ToolReturnPart(
                content="",  # Empty string instead of None
                tool_name=tool_name,
                error=f"Tool '{tool_name}' not found in toolkit"
            )

        try:
            tool_func = tools[tool_name]

            # Check if the tool is async
            if inspect.iscoroutinefunction(tool_func._original_func):
                # Async tool - await it
                result = await tool_func(**kwargs)
            else:
                # Sync tool - call it normally
                result = tool_func(**kwargs)

            should_terminate = self._tool_terminate.get(tool_name, False)
            return ToolReturnPart(
                content=result,
                tool_name=tool_name,
                metadata={
                    "arguments": kwargs,
                    "terminate": should_terminate
                }
            )
        except Exception as e:
            return ToolReturnPart(
                content="",  # Empty string instead of None
                tool_name=tool_name,
                error=str(e),
                metadata={"arguments": kwargs}
            )
