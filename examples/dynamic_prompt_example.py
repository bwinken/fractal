"""
Dynamic System Prompt Example

Demonstrates how to use dynamic system prompts that can change between runs:
1. Template substitution with {placeholders} and system_context
2. Callable prompts for full dynamic control
3. FastAPI integration patterns

No API key required - this example only demonstrates prompt construction.

To run:
    python examples/dynamic_prompt_example.py
"""
import os

# Set dummy API key for demonstration (we don't make actual API calls)
os.environ.setdefault("OPENAI_API_KEY", "sk-demo-key-not-used")

from fractal import BaseAgent
from fractal.toolkit import AgentToolkit


# =============================================================================
# Example 1: Template-based dynamic prompts
# =============================================================================

def example_template_prompt():
    """Template prompts with {placeholders} resolved from system_context."""
    print("=" * 60)
    print("Example 1: Template-based Dynamic Prompts")
    print("=" * 60)

    agent = BaseAgent(
        name="SupportAgent",
        system_prompt=(
            "You are a support assistant for {company_name}. "
            "The user's subscription plan is {plan}. "
            "Respond in a {tone} manner."
        ),
        system_context={
            "company_name": "Acme Corp",
            "plan": "free",
            "tone": "friendly"
        }
    )

    print(f"Initial prompt:\n  {agent.system_prompt}\n")

    # Update context for a different user
    agent.update_system_context(company_name="TechStart Inc", plan="enterprise")
    print(f"After update_system_context():\n  {agent.system_prompt}\n")

    # Update tone for escalated issue
    agent.update_system_context(tone="formal and professional")
    print(f"After changing tone:\n  {agent.system_prompt}\n")


# =============================================================================
# Example 2: Callable prompts for full dynamic control
# =============================================================================

def example_callable_prompt():
    """Callable prompts can capture external state and compute prompts dynamically."""
    print("=" * 60)
    print("Example 2: Callable Dynamic Prompts")
    print("=" * 60)

    # External state (could come from database, config, etc.)
    app_state = {
        "current_user": "Alice",
        "user_tier": "premium",
        "feature_flags": {"new_ui": True, "beta_features": False}
    }

    def get_prompt():
        features = []
        if app_state["feature_flags"]["new_ui"]:
            features.append("new UI")
        if app_state["feature_flags"]["beta_features"]:
            features.append("beta features")

        feature_str = ", ".join(features) if features else "standard features"

        return (
            f"You are assisting {app_state['current_user']} "
            f"({app_state['user_tier']} tier). "
            f"They have access to: {feature_str}."
        )

    agent = BaseAgent(
        name="FeatureAgent",
        system_prompt=get_prompt  # Pass the callable, not the result
    )

    print(f"Initial prompt:\n  {agent.system_prompt}\n")

    # Update external state
    app_state["current_user"] = "Bob"
    app_state["user_tier"] = "free"
    app_state["feature_flags"]["beta_features"] = True

    print(f"After state change:\n  {agent.system_prompt}\n")


# =============================================================================
# Example 3: Class-based agent with instance method prompt
# =============================================================================

class ContextAwareAgent(BaseAgent):
    """Agent that adapts its prompt based on instance state."""

    def __init__(self, default_language: str = "English"):
        self.language = default_language
        self.expertise_level = "beginner"
        self.context_docs = []

        super().__init__(
            name="ContextAwareAgent",
            system_prompt=self._build_prompt
        )

    def _build_prompt(self) -> str:
        """Build prompt from current instance state."""
        prompt = f"Respond in {self.language}. "
        prompt += f"The user is a {self.expertise_level}. "

        if self.context_docs:
            prompt += f"Reference these documents: {', '.join(self.context_docs)}."
        else:
            prompt += "No specific documents loaded."

        return prompt

    def set_expertise(self, level: str):
        """Update user's expertise level."""
        self.expertise_level = level

    def load_documents(self, docs: list):
        """Load context documents."""
        self.context_docs = docs


def example_instance_method_prompt():
    """Instance method prompts allow full OOP patterns."""
    print("=" * 60)
    print("Example 3: Instance Method Prompts")
    print("=" * 60)

    agent = ContextAwareAgent(default_language="English")
    print(f"Initial prompt:\n  {agent.system_prompt}\n")

    agent.language = "Spanish"
    agent.set_expertise("advanced")
    print(f"After language and expertise change:\n  {agent.system_prompt}\n")

    agent.load_documents(["API Reference", "Architecture Guide"])
    print(f"After loading documents:\n  {agent.system_prompt}\n")


# =============================================================================
# Example 4: FastAPI integration pattern (simulated)
# =============================================================================

def example_fastapi_pattern():
    """
    Simulates how dynamic prompts work in a FastAPI backend.

    In a real FastAPI app, you would:
    1. Create a fresh agent per request (or use a pool)
    2. Inject user-specific context from the request
    3. Run the agent with the personalized prompt
    """
    print("=" * 60)
    print("Example 4: FastAPI Integration Pattern (simulated)")
    print("=" * 60)

    # Simulated request data
    requests = [
        {"user_id": "user_123", "name": "Alice", "plan": "pro", "locale": "en-US"},
        {"user_id": "user_456", "name": "Tanaka", "plan": "free", "locale": "ja-JP"},
        {"user_id": "user_789", "name": "Bob", "plan": "enterprise", "locale": "en-GB"},
    ]

    # Simulated database lookup
    def get_user_preferences(user_id: str) -> dict:
        """Simulate database lookup for user preferences."""
        prefs = {
            "user_123": {"verbose": True, "format": "markdown"},
            "user_456": {"verbose": False, "format": "plain"},
            "user_789": {"verbose": True, "format": "json"},
        }
        return prefs.get(user_id, {"verbose": False, "format": "plain"})

    print("Simulating per-request agent creation:\n")

    for req in requests:
        # In FastAPI, this would be in the request handler
        prefs = get_user_preferences(req["user_id"])

        agent = BaseAgent(
            name="APIAgent",
            system_prompt=(
                "You are a helpful assistant. "
                "User: {name} (Plan: {plan}). "
                "Locale: {locale}. "
                "Response format: {format}. "
                "Verbose mode: {verbose}."
            ),
            system_context={
                "name": req["name"],
                "plan": req["plan"],
                "locale": req["locale"],
                "format": prefs["format"],
                "verbose": "enabled" if prefs["verbose"] else "disabled",
            }
        )

        print(f"Request from {req['user_id']}:")
        print(f"  {agent.system_prompt}\n")


# =============================================================================
# Example 5: RAG context injection
# =============================================================================

def example_rag_injection():
    """
    Dynamic prompts for RAG (Retrieval-Augmented Generation).

    The prompt is updated with retrieved documents before each query.
    """
    print("=" * 60)
    print("Example 5: RAG Context Injection")
    print("=" * 60)

    # Simulated document retrieval
    def retrieve_documents(query: str) -> list:
        """Simulate document retrieval based on query."""
        docs = {
            "pricing": [
                "Pricing: Free tier includes 100 API calls/month.",
                "Pro tier: $29/month for 10,000 API calls.",
            ],
            "installation": [
                "Install via pip: pip install fractal-agents",
                "Requires Python 3.8+",
            ],
        }
        for keyword, content in docs.items():
            if keyword in query.lower():
                return content
        return ["No relevant documents found."]

    # State to hold retrieved context
    rag_context = {"documents": []}

    def build_rag_prompt():
        base = "You are a helpful assistant. Answer based on the provided context.\n\n"
        if rag_context["documents"]:
            context = "\n".join(f"- {doc}" for doc in rag_context["documents"])
            return base + f"Context:\n{context}"
        return base + "No context available."

    agent = BaseAgent(
        name="RAGAgent",
        system_prompt=build_rag_prompt
    )

    print("Initial prompt (no context):")
    print(f"  {agent.system_prompt}\n")

    # Simulate query 1
    query1 = "What is the pricing?"
    rag_context["documents"] = retrieve_documents(query1)
    print(f"After retrieving docs for '{query1}':")
    print(f"  {agent.system_prompt}\n")

    # Simulate query 2
    query2 = "How do I install it?"
    rag_context["documents"] = retrieve_documents(query2)
    print(f"After retrieving docs for '{query2}':")
    print(f"  {agent.system_prompt}\n")


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    example_template_prompt()
    print()
    example_callable_prompt()
    print()
    example_instance_method_prompt()
    print()
    example_fastapi_pattern()
    print()
    example_rag_injection()

    print("=" * 60)
    print("[OK] All dynamic prompt examples completed!")
    print("=" * 60)
