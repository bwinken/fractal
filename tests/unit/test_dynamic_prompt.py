"""
Test dynamic system prompt functionality.
"""
import os

# Set dummy API key for tests (agent init requires it but we don't make API calls)
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-key-for-unit-tests")

from fractal import BaseAgent


def test_static_prompt():
    """Static string prompt should work as before."""
    agent = BaseAgent(
        name="Test",
        system_prompt="You are a helpful assistant."
    )
    assert agent.system_prompt == "You are a helpful assistant."


def test_template_prompt_with_context():
    """Template prompt with {placeholders} should be resolved."""
    agent = BaseAgent(
        name="Test",
        system_prompt="You are helping {user_name}. Preference: {pref}.",
        system_context={"user_name": "Alice", "pref": "concise"}
    )
    assert agent.system_prompt == "You are helping Alice. Preference: concise."


def test_template_prompt_missing_context():
    """Template prompt with missing context should return as-is."""
    agent = BaseAgent(
        name="Test",
        system_prompt="Hello {name}!",
        system_context={}  # No context provided
    )
    # Should return the template as-is since context is empty
    assert agent.system_prompt == "Hello {name}!"


def test_callable_prompt():
    """Callable prompt should be invoked each time system_prompt is accessed."""
    call_count = [0]

    def dynamic_prompt():
        call_count[0] += 1
        return f"Dynamic prompt #{call_count[0]}"

    agent = BaseAgent(
        name="Test",
        system_prompt=dynamic_prompt
    )

    # Note: callable may be invoked during init (e.g., by __repr__ or toolkit)
    init_count = call_count[0]

    # Each access invokes the callable again
    first_prompt = agent.system_prompt
    assert call_count[0] == init_count + 1

    second_prompt = agent.system_prompt
    assert call_count[0] == init_count + 2

    # Each call returns fresh result
    assert first_prompt != second_prompt


def test_callable_prompt_with_closure():
    """Callable prompt can capture state via closure."""
    state = {"user": "Alice"}

    agent = BaseAgent(
        name="Test",
        system_prompt=lambda: f"Helping {state['user']}"
    )

    assert agent.system_prompt == "Helping Alice"

    # Update state
    state["user"] = "Bob"
    assert agent.system_prompt == "Helping Bob"


def test_update_system_context():
    """update_system_context() should merge new values."""
    agent = BaseAgent(
        name="Test",
        system_prompt="User: {name}, Plan: {plan}",
        system_context={"name": "Alice", "plan": "free"}
    )

    assert "Alice" in agent.system_prompt
    assert "free" in agent.system_prompt

    # Update one field
    agent.update_system_context(name="Bob")
    assert "Bob" in agent.system_prompt
    assert "free" in agent.system_prompt  # plan unchanged

    # Update another field
    agent.update_system_context(plan="pro")
    assert "Bob" in agent.system_prompt
    assert "pro" in agent.system_prompt


def test_system_context_default_empty():
    """system_context should default to empty dict."""
    agent = BaseAgent(
        name="Test",
        system_prompt="Static prompt"
    )
    assert agent.system_context == {}


def test_callable_with_instance_method():
    """Callable prompt can be a bound method."""
    class MyAgent(BaseAgent):
        def __init__(self):
            self.mode = "friendly"
            super().__init__(
                name="MyAgent",
                system_prompt=self._get_prompt
            )

        def _get_prompt(self):
            return f"You are a {self.mode} assistant."

    agent = MyAgent()
    assert agent.system_prompt == "You are a friendly assistant."

    agent.mode = "formal"
    assert agent.system_prompt == "You are a formal assistant."


if __name__ == "__main__":
    test_static_prompt()
    test_template_prompt_with_context()
    test_template_prompt_missing_context()
    test_callable_prompt()
    test_callable_prompt_with_closure()
    test_update_system_context()
    test_system_context_default_empty()
    test_callable_with_instance_method()
    print("All dynamic prompt tests passed!")
