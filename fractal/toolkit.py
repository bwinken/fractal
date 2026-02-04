"""
Agent toolkit for registering and managing tools.
"""
import inspect
import typing
import warnings
from typing import Any, Callable, Dict, List, Optional
from functools import wraps
from .parser import function_to_tool_schema, parse_google_docstring
from .models import ToolResult

# Types that map cleanly to JSON Schema
_SUPPORTED_TYPES = {str, int, float, bool, list, dict}

# Mapping from Python type -> expected JSON Schema type (for mismatch detection)
_TYPE_TO_JSON_SCHEMA = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


def _unwrap_type(annotation: Any) -> Any:
    """Unwrap Optional / Union / generic aliases to the base type."""
    origin = typing.get_origin(annotation)

    # Optional[X] is Union[X, None]
    if origin is typing.Union:
        args = [a for a in typing.get_args(annotation) if a is not type(None)]
        if len(args) == 1:
            return _unwrap_type(args[0])
        return None  # multi-type Union — skip validation

    # list[X], dict[X, Y], typing.List[X], typing.Dict[X, Y]
    if origin in (list, dict):
        return origin

    return annotation


def _validate_tool_function(func: Callable, tool_name: str) -> None:
    """Validate a tool function at registration time.

    Raises TypeError for:
    - Unsupported parameter type annotations (tuple, set, BaseModel, etc.)

    Issues warnings for:
    - Missing docstring (LLM gets no tool description)
    - Parameters without docstring entries (LLM gets no param description)
    - Type annotation vs docstring type mismatch
    """
    # 1. Docstring presence
    doc = inspect.getdoc(func)
    if not doc:
        warnings.warn(
            f"Tool '{tool_name}': missing docstring. "
            f"The LLM will receive no description for this tool.",
            UserWarning,
            stacklevel=4,
        )
        return  # can't check params without docstring

    # 2. Parse docstring to see which params are documented
    parsed = parse_google_docstring(func)
    sig = inspect.signature(func)

    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue

        # Undocumented parameter
        if param_name not in parsed["parameters"]:
            warnings.warn(
                f"Tool '{tool_name}': parameter '{param_name}' has no description "
                f"in the docstring Args section. The LLM will not know what this "
                f"parameter is for.",
                UserWarning,
                stacklevel=4,
            )

        # Type annotation checks
        annotation = param.annotation
        if annotation is inspect.Parameter.empty:
            continue

        base = _unwrap_type(annotation)
        if base is None:
            continue  # multi-type Union, skip

        # Unsupported type → raise TypeError
        if base not in _SUPPORTED_TYPES:
            type_name = getattr(base, "__name__", str(base))
            raise TypeError(
                f"Tool '{tool_name}': parameter '{param_name}' has unsupported "
                f"type annotation '{type_name}'. "
                f"Supported types: str, int, float, bool, list, dict."
            )

        # Type hint vs docstring type mismatch → warning
        if param_name in parsed["parameters"]:
            docstring_json_type = parsed["parameters"][param_name].get("type")
            hint_json_type = _TYPE_TO_JSON_SCHEMA.get(base)
            if docstring_json_type and hint_json_type and docstring_json_type != hint_json_type:
                warnings.warn(
                    f"Tool '{tool_name}': parameter '{param_name}' type mismatch — "
                    f"annotation says '{base.__name__}' (→ {hint_json_type}) "
                    f"but docstring says '{docstring_json_type}'. "
                    f"The docstring type will be used in the tool schema.",
                    UserWarning,
                    stacklevel=4,
                )


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

    def add_tool(
        self,
        func: Callable,
        *,
        name: Optional[str] = None,
        terminate: bool = False
    ):
        """
        Register a standalone function as a tool.

        Accepts either a plain function or one already decorated with @tool.

        Args:
            func: The function to register as a tool
            name: Optional custom name (defaults to function name)
            terminate: If True, agent will exit loop and return this tool's result

        Example::

            from fractal import BaseAgent, tool

            agent = BaseAgent(name="Assistant", system_prompt="You help users.")

            @tool
            def search(query: str) -> str:
                \"\"\"Search for information.

                Args:
                    query (str): Search query

                Returns:
                    Search results
                \"\"\"
                return f"Results for {query}"

            agent.add_tool(search)
        """
        # Determine if already decorated with @tool / @register_as_tool
        is_decorated = getattr(func, '_is_agent_tool', False)

        if is_decorated:
            tool_name = name or func._tool_name
            original_func = func._original_func
            should_terminate = terminate or getattr(func, '_tool_terminate', False)
        else:
            tool_name = name or func.__name__
            original_func = func
            should_terminate = terminate

        # Ensure tools dict is initialized
        if not self._tools:
            self._discover_tools()

        # Register the callable
        self._tools[tool_name] = func
        self._tool_terminate[tool_name] = should_terminate

        # If not decorated, attach metadata so execute_tool can detect async
        if not is_decorated:
            func._is_agent_tool = True
            func._tool_name = tool_name
            func._tool_terminate = should_terminate
            func._original_func = func

        # Validate before registering
        _validate_tool_function(original_func, tool_name)

        # Generate and store schema
        schema = function_to_tool_schema(original_func)
        schema['function']['name'] = tool_name
        self._tool_schemas[tool_name] = schema

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
        # Generate tool name if not provided
        if tool_name is None:
            agent_name = getattr(agent, 'name', 'agent')
            tool_name = f"delegate_to_{agent_name.lower().replace(' ', '_')}"

        # Generate description if not provided
        if description is None:
            agent_name = getattr(agent, 'name', 'another agent')
            description = f"Delegate tasks to {agent_name} (subordinate agent)"

        # Create async wrapper that calls the other agent
        async def agent_caller(query: str) -> str:
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
                        result=result.content,
                        success=result.success if hasattr(result, 'success') else True
                    )

                    return result.content
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
                return result.content

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

                # Validate at registration time
                _validate_tool_function(attr._original_func, tool_name)

                # Generate schema from the original unbound function
                schema = function_to_tool_schema(attr._original_func)
                self._tool_schemas[tool_name] = schema

    async def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Execute a registered tool by name (supports both sync and async tools).

        Args:
            tool_name (str): Name of the tool to execute
            **kwargs: Arguments to pass to the tool

        Returns:
            ToolResult containing the tool's output
        """
        tools = self.get_tools()

        if tool_name not in tools:
            return ToolResult(
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
            return ToolResult(
                content=result,
                tool_name=tool_name,
                metadata={
                    "arguments": kwargs,
                    "terminate": should_terminate
                }
            )
        except Exception as e:
            return ToolResult(
                content="",  # Empty string instead of None
                tool_name=tool_name,
                error=str(e),
                metadata={"arguments": kwargs}
            )
