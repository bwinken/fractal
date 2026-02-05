"""
Dynamic System Prompts Example
==============================

This example demonstrates how to create system prompts that change at runtime,
enabling per-user personalization and context injection.

OVERVIEW
--------
Fractal supports two types of dynamic system prompts:

1. **Template substitution**: Use `{placeholder}` syntax with `system_context`
2. **Callable prompts**: Pass a function that returns the prompt string

TEMPLATE SUBSTITUTION
---------------------
Use `{placeholder}` in your prompt and provide values via `system_context`:

    agent = BaseAgent(
        system_prompt="Hello {user_name}, you have {plan} plan.",
        system_context={"user_name": "Alice", "plan": "pro"}
    )
    # Result: "Hello Alice, you have pro plan."

    # Update at runtime:
    agent.update_system_context(user_name="Bob")
    # Result: "Hello Bob, you have pro plan."

CALLABLE PROMPTS
----------------
Pass a function for full dynamic control:

    def get_prompt():
        return f"Current time: {datetime.now()}"

    agent = BaseAgent(system_prompt=get_prompt)
    # Prompt regenerated on each access!

USE CASES
---------
- Per-user personalization in web backends (FastAPI)
- RAG context injection before each query
- Multi-tenant SaaS with tenant-specific prompts
- A/B testing different prompt variants

NO API KEY REQUIRED
-------------------
This example demonstrates prompt construction without making API calls.

To run:
    python examples/dynamic_prompt_example.py
"""
import os

# Set dummy API key for demonstration (no API calls made)
os.environ.setdefault("OPENAI_API_KEY", "sk-demo-key-not-used")

from fractal import BaseAgent


# =============================================================================
# Main: Demonstrate Dynamic Prompts
# =============================================================================

def main():
    """Run the dynamic prompt example."""
    print("=" * 70)
    print("Dynamic System Prompts Example")
    print("=" * 70)

    # =========================================================================
    # 1. Template Substitution
    # =========================================================================
    print("\n[1] Template Substitution")
    print("-" * 40)

    agent = BaseAgent(
        name="SupportAgent",
        system_prompt=(
            "You are a support assistant for {company}. "
            "User: {user_name} (Plan: {plan}). "
            "Respond in a {tone} manner."
        ),
        system_context={
            "company": "Acme Corp",
            "user_name": "Alice",
            "plan": "free",
            "tone": "friendly"
        }
    )

    print(f"Initial prompt:\n  {agent.system_prompt}\n")

    # Update context at runtime
    agent.update_system_context(user_name="Bob", plan="enterprise")
    print(f"After update_system_context(user_name='Bob', plan='enterprise'):\n  {agent.system_prompt}\n")

    agent.update_system_context(tone="formal and professional")
    print(f"After update_system_context(tone='formal...'):\n  {agent.system_prompt}\n")

    # =========================================================================
    # 2. Callable Prompts
    # =========================================================================
    print("\n[2] Callable Prompts")
    print("-" * 40)

    # External state (could come from database, config, etc.)
    app_state = {
        "current_user": "Alice",
        "debug_mode": False,
        "features": ["new_ui", "beta"]
    }

    def build_prompt():
        """Generate prompt from current state."""
        features = ", ".join(app_state["features"]) if app_state["features"] else "none"
        debug = " [DEBUG MODE]" if app_state["debug_mode"] else ""
        return f"User: {app_state['current_user']}{debug}. Features: {features}."

    agent2 = BaseAgent(
        name="DynamicAgent",
        system_prompt=build_prompt  # Pass function, not result!
    )

    print(f"Initial prompt:\n  {agent2.system_prompt}\n")

    # Change external state
    app_state["current_user"] = "Bob"
    app_state["debug_mode"] = True
    app_state["features"] = ["new_ui", "beta", "experimental"]

    print(f"After state change:\n  {agent2.system_prompt}\n")

    # =========================================================================
    # 3. FastAPI Pattern (Simulated)
    # =========================================================================
    print("\n[3] FastAPI Pattern (Simulated)")
    print("-" * 40)

    # Simulated requests
    requests = [
        {"user_id": "u123", "name": "Alice", "plan": "pro"},
        {"user_id": "u456", "name": "Bob", "plan": "free"},
    ]

    print("Simulating per-request agent creation:\n")

    for req in requests:
        # In FastAPI, create fresh agent per request
        request_agent = BaseAgent(
            name="APIAgent",
            system_prompt="Hello {name}! You're on the {plan} plan.",
            system_context={"name": req["name"], "plan": req["plan"]}
        )
        print(f"  Request from {req['user_id']}:")
        print(f"    {request_agent.system_prompt}\n")

    # =========================================================================
    # 4. RAG Context Injection
    # =========================================================================
    print("\n[4] RAG Context Injection")
    print("-" * 40)

    # State for RAG context
    rag_context = {"documents": []}

    def rag_prompt():
        base = "Answer based on context. "
        if rag_context["documents"]:
            docs = "; ".join(rag_context["documents"])
            return base + f"Context: {docs}"
        return base + "No context available."

    rag_agent = BaseAgent(name="RAGAgent", system_prompt=rag_prompt)

    print(f"Before retrieval:\n  {rag_agent.system_prompt}\n")

    # Simulate document retrieval
    rag_context["documents"] = ["Doc1: Pricing is $29/month", "Doc2: Free trial 14 days"]

    print(f"After retrieval:\n  {rag_agent.system_prompt}\n")

    print("=" * 70)
    print("[OK] Dynamic prompt example completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
