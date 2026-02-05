"""
Base Agent implementation with OpenAI integration.
"""
import asyncio
import json
import os
from typing import Any, Callable, Dict, List, Optional, Union
from openai import OpenAI, AsyncOpenAI
from pydantic import BaseModel

from .toolkit import AgentToolkit
from .models import AgentResult, ToolResult
from .observability import TracingKit


class BaseAgent:
    """
    Base Agent class that uses OpenAI-compatible API for AI-driven behavior.

    Inherit from this class to create custom agents. Decorate your agent's methods
    with @AgentToolkit.register_as_tool to automatically register them as tools.

    The agent uses composition pattern - it HAS a toolkit rather than IS a toolkit.

    Example::

        class WeatherAgent(BaseAgent):
            def __init__(self):
                super().__init__(
                    name="WeatherBot",
                    system_prompt="You are a weather assistant."
                )

            @AgentToolkit.register_as_tool
            def get_weather(self, location: str) -> str:
                # Get weather for a location.
                # Args:
                #     location (str): City name
                # Returns:
                #     Weather information
                return f"Weather in {location}"
    """

    def __init__(
        self,
        name: str,
        system_prompt: Union[str, Callable[[], str]],
        model: Optional[str] = None,
        client: Optional[Union[OpenAI, AsyncOpenAI]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        enable_tracing: bool = False,
        tracing_output_file: Optional[str] = None,
        context_window: Optional[int] = None,
        system_context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the Base Agent.

        Args:
            name (str): Name of the agent
            system_prompt (Union[str, Callable[[], str]]): System prompt that defines the agent's behavior.
                Can be a static string, a template string with ``{placeholders}``, or a callable
                that returns the prompt dynamically. Templates are resolved using ``system_context``.
            model (str): OpenAI model to use (falls back to OPENAI_MODEL env var, then "gpt-4o-mini")
            client (Union[OpenAI, AsyncOpenAI]): OpenAI client instance (sync or async, if None creates AsyncOpenAI).
                When omitted, AsyncOpenAI() is created automatically, which reads OPENAI_API_KEY
                and OPENAI_BASE_URL from environment variables.
            temperature (float): Sampling temperature (0-2)
            max_tokens (int): Maximum tokens in response
            enable_tracing (bool): Enable execution tracing for observability
            tracing_output_file (str): Optional file path pattern for trace output. Supports placeholders:
                ``{run_id}`` — unique ID for this run (e.g., ``trace_{run_id}.jsonl``)
                ``{timestamp}`` — ISO timestamp (e.g., ``trace_{timestamp}.jsonl``)
                When a pattern contains placeholders, each ``run()`` creates a new file.
                Without placeholders, all runs append to the same file.
            context_window (int): Maximum token budget for API calls (falls back to CONTEXT_WINDOW env var).
                When set, automatically trims old conversation history to fit within the limit.
                The full history is preserved in self.messages; only the API call receives a trimmed view.
            system_context (dict): Context variables for template substitution in system_prompt.
                Use ``{key}`` placeholders in the prompt and provide values here. Can be updated
                later with ``update_system_context()``.
        """
        self.name = name
        self._system_prompt_source = system_prompt  # Store original (str or Callable)
        self.system_context: Dict[str, Any] = system_context or {}
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Create toolkit with this agent as target (composition pattern)
        self.toolkit = AgentToolkit(target=self)

        # Create tracing kit if enabled (composition pattern)
        self.tracing = TracingKit(output_file=tracing_output_file) if enable_tracing else None

        # Context window management (opt-in)
        _cw = context_window or int(os.environ.get("CONTEXT_WINDOW", "0")) or None
        self.context_window: Optional[int] = _cw
        self._tiktoken_enc = None  # Lazy-initialized tiktoken encoder

        # Use provided client or create default async one
        self.client = client if client is not None else AsyncOpenAI()

        # Conversation history (use resolved system_prompt)
        self.messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt}
        ]

    @property
    def system_prompt(self) -> str:
        """
        Get the resolved system prompt.

        If ``_system_prompt_source`` is a callable, it is invoked to get the current prompt.
        If it's a string with ``{placeholders}``, they are substituted using ``system_context``.
        Otherwise, the string is returned as-is.

        Returns:
            The resolved system prompt string.
        """
        if callable(self._system_prompt_source):
            return self._system_prompt_source()
        elif self.system_context:
            try:
                return self._system_prompt_source.format(**self.system_context)
            except KeyError:
                # If placeholders don't match context, return as-is
                return self._system_prompt_source
        return self._system_prompt_source

    def update_system_context(self, **kwargs) -> None:
        """
        Update the system context for template substitution.

        New values are merged into the existing context. Use this to change
        dynamic parts of the system prompt before the next ``run()`` call.

        Args:
            **kwargs: Key-value pairs to merge into the system context.

        Example::

            agent = BaseAgent(
                name="Assistant",
                system_prompt="Helping {user_name}. Preference: {pref}",
                system_context={"user_name": "Alice", "pref": "concise"}
            )
            agent.update_system_context(user_name="Bob")
            # Next run() will use "Helping Bob. Preference: concise"
        """
        self.system_context.update(kwargs)

    async def run(
        self,
        user_input: Union[str, dict, list, BaseModel],
        max_iterations: int = 10,
        max_retries: int = 3
    ) -> AgentResult:
        """
        Run the agent with a user input (async).

        Args:
            user_input (Union[str, dict, list, BaseModel]): User input as string, dict, list, or Pydantic object
            max_iterations (int): Maximum number of tool-calling iterations
            max_retries (int): Maximum number of retries for API errors

        Returns:
            AgentResult containing the agent's final response
        """
        # Refresh system prompt (handles dynamic prompts via Callable or template)
        self.messages[0]["content"] = self.system_prompt

        # Convert input to string if necessary
        if isinstance(user_input, str):
            content = user_input
        elif isinstance(user_input, BaseModel):
            json_data = user_input.model_dump_json(indent=2)
            content = f"Input data:\n{json_data}"
        elif isinstance(user_input, (dict, list)):
            json_data = json.dumps(user_input, indent=2, ensure_ascii=False)
            content = f"Input data:\n{json_data}"
        else:
            content = str(user_input)

        # Add user message
        self.messages.append({"role": "user", "content": content})

        # Start tracing
        # Only start a new run if no run is active (i.e., this is the top-level agent).
        # Delegated agents inherit the parent's TracingKit with an active run_id,
        # so they should NOT call start_run() which would clear the parent's events.
        if self.tracing:
            if self.tracing.run_id is None:
                # Top-level agent: start a new run (clears previous events, generates run_id)
                self.tracing.start_run()
            self.tracing.start_agent(self.name, content, metadata={'model': self.model})

        iteration = 0
        while iteration < max_iterations:
            iteration += 1

            # Retry loop for API calls
            retry_count = 0
            last_error = None

            while retry_count < max_retries:
                try:
                    # Prepare API call parameters
                    api_params = {
                        "model": self.model,
                        "messages": self._prepare_messages(),
                        "temperature": self.temperature,
                    }

                    if self.max_tokens:
                        api_params["max_tokens"] = self.max_tokens

                    # Add tools if agent has any registered
                    tool_schemas = self.get_tool_schemas()
                    if tool_schemas:
                        api_params["tools"] = tool_schemas
                        api_params["tool_choice"] = "auto"

                    # Make API call (async)
                    response = await self.client.chat.completions.create(**api_params)

                    # Validate response
                    if not response.choices or len(response.choices) == 0:
                        raise ValueError("API returned empty response")

                    message = response.choices[0].message

                    # Check for reasoning-only response (no actual content)
                    if not message.content and not message.tool_calls:
                        # Try to extract from refusal if present
                        if hasattr(message, 'refusal') and message.refusal:
                            result = AgentResult(
                                content=f"Request refused: {message.refusal}",
                                agent_name=self.name,
                                success=False,
                                metadata={
                                    "iterations": iteration,
                                    "reason": "refusal"
                                }
                            )
                            # End tracing
                            if self.tracing:
                                self.tracing.end_agent(self.name, result.content, success=False, metadata={'reason': 'refusal'})
                                self.tracing.end_run()
                            return result

                        # Otherwise, this is likely a reasoning-only response - retry
                        retry_count += 1
                        if retry_count < max_retries:
                            # Add a prompt to request actual content
                            self.messages.append({
                                "role": "user",
                                "content": "Please provide your actual response or use a tool."
                            })
                            continue
                        else:
                            result = AgentResult(
                                content="Agent failed to provide a valid response after retries",
                                agent_name=self.name,
                                success=False,
                                metadata={
                                    "iterations": iteration,
                                    "reason": "no_content_after_retries"
                                }
                            )
                            # End tracing
                            if self.tracing:
                                self.tracing.end_agent(self.name, result.content, success=False, metadata={'reason': 'no_content_after_retries'})
                                self.tracing.end_run()
                            return result

                    # Check for empty content when no tool calls
                    if message.content is None and not message.tool_calls:
                        message.content = ""

                    # Successfully got valid response - break retry loop
                    break

                except json.JSONDecodeError as e:
                    # Malformed tool call arguments
                    last_error = f"Invalid tool call JSON: {str(e)}"
                    retry_count += 1
                    if retry_count >= max_retries:
                        result = AgentResult(
                            content=last_error,
                            agent_name=self.name,
                            success=False,
                            metadata={
                                "iterations": iteration,
                                "error": last_error,
                                "error_type": "json_decode_error"
                            }
                        )
                        # End tracing
                        if self.tracing:
                            self.tracing.record_error(self.name, last_error, metadata={'error_type': 'json_decode_error'})
                            self.tracing.end_agent(self.name, result.content, success=False, metadata={'error_type': 'json_decode_error'})
                            self.tracing.end_run()
                        return result
                    # Wait before retry
                    import asyncio
                    await asyncio.sleep(0.5 * retry_count)

                except Exception as e:
                    error_str = str(e)
                    last_error = error_str

                    # Check if it's a rate limit error
                    if "rate_limit" in error_str.lower() or "429" in error_str:
                        retry_count += 1
                        if retry_count < max_retries:
                            # Exponential backoff
                            import asyncio
                            wait_time = (2 ** retry_count) * 0.5
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            result = AgentResult(
                                content=f"Rate limit exceeded: {error_str}",
                                agent_name=self.name,
                                success=False,
                                metadata={
                                    "iterations": iteration,
                                    "error": error_str,
                                    "error_type": "rate_limit"
                                }
                            )
                            # End tracing
                            if self.tracing:
                                self.tracing.record_error(self.name, error_str, metadata={'error_type': 'rate_limit'})
                                self.tracing.end_agent(self.name, result.content, success=False, metadata={'error_type': 'rate_limit'})
                                self.tracing.end_run()
                            return result

                    # Check if it's a timeout error
                    elif "timeout" in error_str.lower():
                        retry_count += 1
                        if retry_count < max_retries:
                            import asyncio
                            await asyncio.sleep(1.0 * retry_count)
                            continue
                        else:
                            result = AgentResult(
                                content=f"Request timeout: {error_str}",
                                agent_name=self.name,
                                success=False,
                                metadata={
                                    "iterations": iteration,
                                    "error": error_str,
                                    "error_type": "timeout"
                                }
                            )
                            # End tracing
                            if self.tracing:
                                self.tracing.record_error(self.name, error_str, metadata={'error_type': 'timeout'})
                                self.tracing.end_agent(self.name, result.content, success=False, metadata={'error_type': 'timeout'})
                                self.tracing.end_run()
                            return result

                    # Other errors - fail immediately
                    result = AgentResult(
                        content=error_str,
                        agent_name=self.name,
                        success=False,
                        metadata={
                            "iterations": iteration,
                            "error": error_str,
                            "error_type": "api_error"
                        }
                    )
                    # End tracing
                    if self.tracing:
                        self.tracing.record_error(self.name, error_str, metadata={'error_type': 'api_error'})
                        self.tracing.end_agent(self.name, result.content, success=False, metadata={'error_type': 'api_error'})
                        self.tracing.end_run()
                    return result

            # After retry loop - continue with normal processing
            try:

                # Add assistant message to history
                assistant_message = {"role": "assistant", "content": message.content}

                if message.tool_calls:
                    assistant_message["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in message.tool_calls
                    ]

                self.messages.append(assistant_message)

                # Check if agent wants to call tools
                if message.tool_calls:
                    # Generate parallel_group_id if multiple tools
                    parallel_group_id = None
                    if len(message.tool_calls) > 1:
                        import uuid as uuid_mod
                        parallel_group_id = uuid_mod.uuid4().hex[:8]

                    # Phase 1: Parse all tool arguments and prepare execution tasks
                    valid_tool_calls = []
                    for tool_call in message.tool_calls:
                        function_name = tool_call.function.name

                        # Parse tool arguments with error handling
                        try:
                            function_args = json.loads(tool_call.function.arguments)
                            valid_tool_calls.append({
                                'tool_call': tool_call,
                                'function_name': function_name,
                                'function_args': function_args
                            })
                        except json.JSONDecodeError as e:
                            # Add error message for invalid tool arguments immediately
                            self.messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": function_name,
                                "content": f"Error: Invalid tool arguments - {str(e)}"
                            })

                    if valid_tool_calls:
                        # Phase 2: Trace all tool call starts
                        if self.tracing:
                            for tc_info in valid_tool_calls:
                                self.tracing.start_tool_call(
                                    self.name,
                                    tc_info['function_name'],
                                    tc_info['function_args'],
                                    tool_call_id=tc_info['tool_call'].id,
                                    parallel_group_id=parallel_group_id
                                )

                        # Phase 3: Execute all tools in parallel
                        async def execute_single_tool(tc_info):
                            return await self.execute_tool(
                                tc_info['function_name'],
                                **tc_info['function_args']
                            )

                        tool_results = await asyncio.gather(
                            *[execute_single_tool(tc_info) for tc_info in valid_tool_calls],
                            return_exceptions=True
                        )

                        # Phase 4: Process results and trace tool call ends
                        termination_result = None
                        for tc_info, tool_result in zip(valid_tool_calls, tool_results):
                            tool_call = tc_info['tool_call']
                            function_name = tc_info['function_name']

                            # Handle exceptions from gather
                            if isinstance(tool_result, Exception):
                                error_msg = str(tool_result)
                                if self.tracing:
                                    self.tracing.end_tool_call(
                                        self.name,
                                        function_name,
                                        None,
                                        error=error_msg,
                                        tool_call_id=tool_call.id,
                                        parallel_group_id=parallel_group_id
                                    )
                                self.messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "name": function_name,
                                    "content": f"Error: {error_msg}"
                                })
                                continue

                            # Trace tool call end
                            if self.tracing:
                                self.tracing.end_tool_call(
                                    self.name,
                                    function_name,
                                    tool_result.content,
                                    error=tool_result.error,
                                    metadata={'terminate': tool_result.metadata and tool_result.metadata.get('terminate', False)},
                                    tool_call_id=tool_call.id,
                                    parallel_group_id=parallel_group_id
                                )

                            # Check if this is a termination tool (save for later, process all first)
                            should_terminate = tool_result.metadata and tool_result.metadata.get('terminate', False)
                            if should_terminate and not tool_result.error and termination_result is None:
                                termination_result = (function_name, tool_result)

                            # Prepare tool response
                            if tool_result.error:
                                tool_response = f"Error: {tool_result.error}"
                            else:
                                # Serialize tool result content for LLM
                                if isinstance(tool_result.content, str):
                                    tool_response = tool_result.content
                                elif isinstance(tool_result.content, BaseModel):
                                    tool_response = tool_result.content.model_dump_json(indent=2)
                                elif isinstance(tool_result.content, list):
                                    # Handle list of Pydantic models or primitives
                                    if tool_result.content and isinstance(tool_result.content[0], BaseModel):
                                        serialized_list = [item.model_dump() for item in tool_result.content]
                                        tool_response = json.dumps(serialized_list, indent=2, ensure_ascii=False)
                                    else:
                                        tool_response = json.dumps(tool_result.content, indent=2, ensure_ascii=False)
                                elif isinstance(tool_result.content, dict):
                                    tool_response = json.dumps(tool_result.content, indent=2, ensure_ascii=False)
                                else:
                                    tool_response = str(tool_result.content)

                            # Add tool result to messages
                            self.messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": function_name,
                                "content": tool_response
                            })

                        # Phase 5: Handle termination after all tools processed
                        if termination_result:
                            function_name, tool_result = termination_result
                            result = AgentResult(
                                content=tool_result.content,
                                agent_name=self.name,
                                success=True,
                                metadata={
                                    "iterations": iteration,
                                    "model": self.model,
                                    "terminated_by_tool": function_name
                                }
                            )
                            # End tracing
                            if self.tracing:
                                self.tracing.end_agent(self.name, result.content, success=True, metadata={'terminated_by_tool': function_name})
                                self.tracing.end_run()
                            return result

                    # Continue loop to get next response
                    continue

                # No tool calls, return final response
                result = AgentResult(
                    content=message.content or "",
                    agent_name=self.name,
                    success=True,
                    metadata={
                        "iterations": iteration,
                        "model": self.model
                    }
                )

                # End tracing
                if self.tracing:
                    self.tracing.end_agent(self.name, result.content, success=True, metadata={'iterations': iteration})
                    self.tracing.end_run()

                return result

            except Exception as e:
                # Catch any unexpected errors in tool processing
                result = AgentResult(
                    content=f"Unexpected error in agent execution: {str(e)}",
                    agent_name=self.name,
                    success=False,
                    metadata={
                        "iterations": iteration,
                        "error": str(e),
                        "error_type": "unexpected_error"
                    }
                )
                # End tracing
                if self.tracing:
                    self.tracing.record_error(self.name, str(e), metadata={'error_type': 'unexpected_error'})
                    self.tracing.end_agent(self.name, result.content, success=False, metadata={'error_type': 'unexpected_error'})
                    self.tracing.end_run()
                return result

        # Max iterations reached
        result = AgentResult(
            content="Max iterations reached without completion",
            agent_name=self.name,
            success=False,
            metadata={
                "iterations": iteration,
                "reason": "max_iterations_reached"
            }
        )
        # End tracing
        if self.tracing:
            self.tracing.end_agent(self.name, result.content, success=False, metadata={'reason': 'max_iterations_reached'})
            self.tracing.end_run()
        return result

    def __str__(self) -> str:
        """
        Return a human-readable string representation of the agent.

        Returns:
            Formatted string with agent information including tools
        """
        lines = []
        lines.append("=" * 70)
        lines.append(f"Agent: {self.name}")
        lines.append("=" * 70)
        lines.append(f"Model: {self.model}")
        lines.append(f"Temperature: {self.temperature}")
        if self.max_tokens:
            lines.append(f"Max Tokens: {self.max_tokens}")
        if self.context_window:
            lines.append(f"Context Window: {self.context_window}")

        # System prompt (truncated if too long)
        prompt_preview = self.system_prompt[:100] + "..." if len(self.system_prompt) > 100 else self.system_prompt
        lines.append(f"\nSystem Prompt:\n  {prompt_preview}")

        # List tools
        schemas = self.get_tool_schemas()
        lines.append(f"\nTools ({len(schemas)}):")

        if not schemas:
            lines.append("  No tools registered")
        else:
            for idx, schema in enumerate(schemas, 1):
                func = schema['function']
                name = func['name']
                description = func.get('description', 'No description')
                parameters = func.get('parameters', {}).get('properties', {})
                required = func.get('parameters', {}).get('required', [])

                lines.append(f"\n  {idx}. {name}")
                lines.append(f"     {description}")

                if parameters:
                    param_parts = []
                    for param_name, param_info in parameters.items():
                        param_type = param_info.get('type', 'any')
                        is_required = param_name in required
                        marker = "*" if is_required else ""
                        param_parts.append(f"{param_name}{marker}: {param_type}")

                    lines.append(f"     Parameters: {', '.join(param_parts)}")
                    if any(p in required for p in parameters):
                        lines.append("     (* = required)")

        lines.append("\n" + "=" * 70)
        return "\n".join(lines)

    def __repr__(self) -> str:
        """
        Return a developer-friendly representation of the agent.

        Returns:
            String representation for debugging
        """
        tool_count = len(self.get_tool_schemas())
        return f"<{self.__class__.__name__}(name='{self.name}', model='{self.model}', tools={tool_count})>"

    def reset(self):
        """
        Reset the agent's conversation history.
        """
        self.messages = [
            {"role": "system", "content": self.system_prompt}
        ]

    # ========================================================================
    # Context window management
    # ========================================================================

    def _get_tiktoken_enc(self):
        """Lazily initialize and cache a tiktoken encoder."""
        if self._tiktoken_enc is None:
            try:
                import tiktoken
                try:
                    self._tiktoken_enc = tiktoken.encoding_for_model(self.model)
                except KeyError:
                    self._tiktoken_enc = tiktoken.get_encoding("cl100k_base")
            except ImportError:
                return None
        return self._tiktoken_enc

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for a string.

        Uses tiktoken if available, otherwise falls back to len // 4.
        """
        enc = self._get_tiktoken_enc()
        if enc is not None:
            return len(enc.encode(text))
        return len(text) // 4 + 1

    def _estimate_message_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """Estimate token count for a list of chat messages.

        Each message has ~4 tokens of overhead (role, delimiters).
        An additional 2 tokens are added for reply priming.
        """
        total = 0
        for msg in messages:
            total += 4  # per-message overhead
            for key, value in msg.items():
                if isinstance(value, str):
                    total += self._estimate_tokens(value)
                elif isinstance(value, list):
                    total += self._estimate_tokens(json.dumps(value))
                total += 1  # key name
        total += 2  # reply priming
        return total

    def _group_messages(
        self, messages: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """Group messages into atomic units that must be kept or removed together.

        Groups:
        - A standalone user or assistant message (no tool_calls)
        - An assistant message with tool_calls + all subsequent tool responses
        """
        groups: List[List[Dict[str, Any]]] = []
        i = 0
        while i < len(messages):
            msg = messages[i]
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                group = [msg]
                j = i + 1
                while j < len(messages) and messages[j].get("role") == "tool":
                    group.append(messages[j])
                    j += 1
                groups.append(group)
                i = j
            else:
                groups.append([msg])
                i += 1
        return groups

    def _prepare_messages(self) -> List[Dict[str, Any]]:
        """Prepare messages for an API call, trimming if context_window is set.

        When context_window is None, returns self.messages as-is.
        Otherwise, trims the oldest conversation turns to fit within the token
        budget while preserving:
        - The system message (always first)
        - The most recent messages (current turn)
        - Atomic tool-call groups (never split)

        The internal self.messages list is never mutated.
        """
        if self.context_window is None:
            return self.messages

        # Fixed costs
        system_messages = [self.messages[0]]
        system_tokens = self._estimate_message_tokens(system_messages)

        tool_schema_tokens = 0
        tool_schemas = self.get_tool_schemas()
        if tool_schemas:
            tool_schema_tokens = self._estimate_tokens(json.dumps(tool_schemas))

        response_reserve = self.max_tokens or 4096

        available = self.context_window - system_tokens - tool_schema_tokens - response_reserve
        if available <= 0:
            return self.messages

        # Group conversation messages into atomic units
        conversation = self.messages[1:]
        groups = self._group_messages(conversation)

        # Walk from newest to oldest, keep as many groups as fit
        kept_groups: List[List[Dict[str, Any]]] = []
        kept_tokens = 0

        for group in reversed(groups):
            group_tokens = self._estimate_message_tokens(group)
            if kept_tokens + group_tokens <= available:
                kept_groups.insert(0, group)
                kept_tokens += group_tokens
            else:
                break

        # Flatten
        trimmed: List[Dict[str, Any]] = []
        for group in kept_groups:
            trimmed.extend(group)

        return system_messages + trimmed

    # ========================================================================
    # Toolkit delegation methods
    # ========================================================================

    def get_tools(self) -> Dict[str, Any]:
        """
        Get all registered tools.

        Delegates to the internal toolkit.

        Returns:
            Dictionary mapping tool names to callable functions
        """
        return self.toolkit.get_tools()

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Get OpenAI-compatible tool schemas.

        Delegates to the internal toolkit.

        Returns:
            List of tool schema dictionaries in OpenAI format
        """
        return self.toolkit.get_tool_schemas()

    async def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Execute a registered tool by name.

        Delegates to the internal toolkit.

        Args:
            tool_name (str): Name of the tool to execute
            **kwargs: Arguments to pass to the tool

        Returns:
            ToolResult containing the tool's output
        """
        return await self.toolkit.execute_tool(tool_name, **kwargs)

    def add_tool(self, func, *, name: Optional[str] = None, terminate: bool = False):
        """
        Register a standalone function as a tool.

        Accepts either a plain function or one already decorated with @tool.
        Delegates to the internal toolkit.

        Args:
            func: The function to register as a tool
            name (str): Optional custom name (defaults to function name)
            terminate (bool): If True, agent will exit loop and return this tool's result

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
        self.toolkit.add_tool(func, name=name, terminate=terminate)

    def register_delegate(
        self,
        agent: 'BaseAgent',
        tool_name: Optional[str] = None,
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ):
        """
        Register a subordinate agent for task delegation.

        This allows the current agent to delegate tasks to specialist/subordinate agents.
        The subordinate agent will be registered as a callable tool.

        Delegates to the internal toolkit.

        Args:
            agent (BaseAgent): The subordinate agent to register for delegation
            tool_name (str): Optional name for the delegation tool (defaults to "delegate_to_{agent.name}")
            description (str): Optional description for the tool
            parameters (dict): Optional custom parameters for the delegate tool.
                When omitted, the tool accepts a single ``query`` string.
                When provided, the LLM sees the specified parameters and the
                delegated agent receives the full dict via ``agent.run(dict)``.

        Example::

            # Simple delegation (single query string)
            self.register_delegate(specialist, tool_name="ask_specialist")

            # Structured delegation (custom parameters)
            self.register_delegate(
                data_agent,
                tool_name="query_data",
                description="Query the data warehouse",
                parameters={
                    "sql": {"type": "str", "description": "SQL query to execute"},
                    "limit": {"type": "int", "description": "Max rows", "required": False},
                }
            )
        """
        self.toolkit.register_delegate(agent, tool_name, description, parameters)

