"""
Unit tests for context window management.

Tests token estimation, message grouping, and automatic trimming
without requiring an API key or network access.
"""
import os
import json
import pytest
from unittest.mock import patch
from openai import OpenAI
from fractal import BaseAgent, AgentToolkit

# Set dummy API key for testing
os.environ["OPENAI_API_KEY"] = "sk-test-dummy-key-for-testing"


class SimpleAgent(BaseAgent):
    """Minimal agent for testing context window behavior."""

    def __init__(self, **kwargs):
        super().__init__(
            name="TestAgent",
            system_prompt="You are a test agent.",
            model="gpt-4o-mini",
            client=OpenAI(),
            **kwargs
        )

    @AgentToolkit.register_as_tool
    def dummy_tool(self, query: str) -> str:
        """A dummy tool.

        Args:
            query (str): Input query

        Returns:
            Result string
        """
        return f"result: {query}"


# ========================================================================
# Constructor
# ========================================================================

class TestConstructor:
    """Test context_window parameter handling."""

    def test_default_disabled(self):
        agent = SimpleAgent()
        assert agent.context_window is None

    def test_explicit_value(self):
        agent = SimpleAgent(context_window=128000)
        assert agent.context_window == 128000

    def test_env_var_fallback(self):
        with patch.dict(os.environ, {"CONTEXT_WINDOW": "64000"}):
            agent = SimpleAgent()
            assert agent.context_window == 64000

    def test_explicit_overrides_env(self):
        with patch.dict(os.environ, {"CONTEXT_WINDOW": "64000"}):
            agent = SimpleAgent(context_window=128000)
            assert agent.context_window == 128000

    def test_env_var_zero_means_disabled(self):
        with patch.dict(os.environ, {"CONTEXT_WINDOW": "0"}):
            agent = SimpleAgent()
            assert agent.context_window is None


# ========================================================================
# Token estimation
# ========================================================================

class TestTokenEstimation:
    """Test token counting with fallback (no tiktoken dependency assumed)."""

    def test_estimate_tokens_nonempty(self):
        agent = SimpleAgent()
        # Force fallback by clearing cache
        agent._tiktoken_enc = None
        with patch.dict("sys.modules", {"tiktoken": None}):
            agent._tiktoken_enc = None
            tokens = agent._estimate_tokens("Hello world")
            assert tokens > 0

    def test_estimate_tokens_empty(self):
        agent = SimpleAgent()
        tokens = agent._estimate_tokens("")
        assert tokens >= 0

    def test_estimate_message_tokens(self):
        agent = SimpleAgent()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        tokens = agent._estimate_message_tokens(messages)
        # Should be positive and include overhead
        assert tokens > 0

    def test_message_overhead_included(self):
        agent = SimpleAgent()
        single = [{"role": "user", "content": "Hi"}]
        double = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hi"},
        ]
        # Two messages should cost more than one
        assert agent._estimate_message_tokens(double) > agent._estimate_message_tokens(single)


# ========================================================================
# Message grouping
# ========================================================================

class TestMessageGrouping:
    """Test _group_messages atomic grouping logic."""

    def test_simple_messages(self):
        agent = SimpleAgent()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "Bye"},
        ]
        groups = agent._group_messages(messages)
        assert len(groups) == 3
        assert all(len(g) == 1 for g in groups)

    def test_tool_call_group(self):
        agent = SimpleAgent()
        messages = [
            {"role": "user", "content": "Do something"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "call_1", "type": "function", "function": {"name": "dummy_tool", "arguments": '{"query": "test"}'}}
                ]
            },
            {"role": "tool", "tool_call_id": "call_1", "name": "dummy_tool", "content": "result: test"},
            {"role": "assistant", "content": "Done!"},
        ]
        groups = agent._group_messages(messages)
        # user | (assistant+tool) | assistant
        assert len(groups) == 3
        assert len(groups[0]) == 1  # user
        assert len(groups[1]) == 2  # assistant with tool_calls + tool response
        assert len(groups[2]) == 1  # final assistant

    def test_multiple_tool_calls(self):
        agent = SimpleAgent()
        messages = [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "call_1", "type": "function", "function": {"name": "a", "arguments": "{}"}},
                    {"id": "call_2", "type": "function", "function": {"name": "b", "arguments": "{}"}},
                ]
            },
            {"role": "tool", "tool_call_id": "call_1", "name": "a", "content": "r1"},
            {"role": "tool", "tool_call_id": "call_2", "name": "b", "content": "r2"},
        ]
        groups = agent._group_messages(messages)
        # Single group: assistant + 2 tool responses
        assert len(groups) == 1
        assert len(groups[0]) == 3

    def test_empty_messages(self):
        agent = SimpleAgent()
        groups = agent._group_messages([])
        assert groups == []


# ========================================================================
# Message preparation (trimming)
# ========================================================================

class TestPrepareMessages:
    """Test _prepare_messages context window trimming."""

    def test_disabled_returns_all(self):
        """When context_window is None, all messages returned."""
        agent = SimpleAgent()
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]
        result = agent._prepare_messages(messages)
        assert result is messages  # Same object, not a copy

    def test_system_message_always_kept(self):
        """System message is always the first message after trimming."""
        agent = SimpleAgent(context_window=500)
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "old message " * 50},
            {"role": "assistant", "content": "old response " * 50},
            {"role": "user", "content": "new message"},
            {"role": "assistant", "content": "new response"},
        ]
        result = agent._prepare_messages(messages)
        assert result[0]["role"] == "system"
        assert result[0]["content"] == "System prompt"

    def test_newest_messages_preserved(self):
        """The most recent messages are kept, old ones trimmed."""
        agent = SimpleAgent(context_window=500)
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "very old " * 100},
            {"role": "assistant", "content": "very old response " * 100},
            {"role": "user", "content": "recent"},
            {"role": "assistant", "content": "recent response"},
        ]
        result = agent._prepare_messages(messages)
        # System + at least the recent messages
        assert result[0]["content"] == "System"
        contents = [m["content"] for m in result]
        assert "recent" in contents
        assert "recent response" in contents

    def test_oldest_trimmed_first(self):
        """Older conversation turns are trimmed before newer ones."""
        # Budget must exceed response_reserve (4096) + system + tool schemas,
        # but be too small to fit all conversation messages.
        agent = SimpleAgent(context_window=4400)
        messages = [
            {"role": "system", "content": "S"},
            {"role": "user", "content": "turn1 " * 500},
            {"role": "assistant", "content": "resp1 " * 500},
            {"role": "user", "content": "turn2"},
            {"role": "assistant", "content": "resp2"},
            {"role": "user", "content": "turn3"},
            {"role": "assistant", "content": "resp3"},
        ]
        result = agent._prepare_messages(messages)
        contents = [m.get("content", "") for m in result]
        # turn1/resp1 are large (~1000 tokens), should be trimmed
        assert not any("turn1" in c for c in contents)
        assert any("turn3" in c for c in contents)

    def test_tool_calls_not_split(self):
        """Tool call groups are kept or removed as a unit."""
        agent = SimpleAgent(context_window=600)
        tool_call_msg = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {"id": "call_1", "type": "function", "function": {"name": "t", "arguments": "{}"}}
            ]
        }
        tool_response_msg = {
            "role": "tool", "tool_call_id": "call_1", "name": "t", "content": "result"
        }
        messages = [
            {"role": "system", "content": "S"},
            {"role": "user", "content": "old " * 50},
            tool_call_msg,
            tool_response_msg,
            {"role": "user", "content": "new"},
            {"role": "assistant", "content": "new response"},
        ]
        result = agent._prepare_messages(messages)
        # If tool group is present, both assistant and tool response must be there
        roles = [m["role"] for m in result]
        if "tool" in roles:
            tool_idx = roles.index("tool")
            assert roles[tool_idx - 1] == "assistant"
            assert result[tool_idx - 1].get("tool_calls") is not None

    def test_does_not_mutate_original(self):
        """Original messages list is never modified by trimming."""
        agent = SimpleAgent(context_window=300)
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "padding " * 100},
            {"role": "assistant", "content": "padding " * 100},
            {"role": "user", "content": "latest"},
        ]
        original_len = len(messages)
        result = agent._prepare_messages(messages)
        # Original unchanged
        assert len(messages) == original_len
        # Result may be shorter
        assert len(result) <= original_len

    def test_large_budget_keeps_all(self):
        """When context_window is very large, all messages are kept."""
        agent = SimpleAgent(context_window=1_000_000)
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "Bye"},
            {"role": "assistant", "content": "Goodbye"},
        ]
        result = agent._prepare_messages(messages)
        assert len(result) == len(messages)


# ========================================================================
# __str__ display
# ========================================================================

class TestStrDisplay:
    """Test that __str__ shows context_window when set."""

    def test_str_without_context_window(self):
        agent = SimpleAgent()
        output = str(agent)
        assert "Context Window" not in output

    def test_str_with_context_window(self):
        agent = SimpleAgent(context_window=128000)
        output = str(agent)
        assert "Context Window: 128000" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
