"""
RAG (Retrieval-Augmented Generation) agent example.

Demonstrates how to build a knowledge-based Q&A agent that retrieves
relevant documents before answering. Uses a simple in-memory vector store
with cosine similarity — no external dependencies beyond the OpenAI client.

Usage:
    python examples/rag_example.py

Requires:
    OPENAI_API_KEY in .env (uses the Embeddings API for document indexing)
"""
import os
import math
import asyncio
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel
from fractal import BaseAgent, AgentToolkit

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


# ============================================================================
# Simple in-memory vector store
# ============================================================================

class Document(BaseModel):
    """A document with its embedding."""
    id: str
    content: str
    source: str
    embedding: list[float] = []


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class VectorStore:
    """Minimal in-memory vector store using OpenAI embeddings."""

    def __init__(self, client: AsyncOpenAI, model: str = "text-embedding-3-small"):
        self.client = client
        self.model = model
        self.documents: list[Document] = []

    async def _embed(self, text: str) -> list[float]:
        """Get embedding for a text string."""
        response = await self.client.embeddings.create(
            input=text,
            model=self.model
        )
        return response.data[0].embedding

    async def add_document(self, doc_id: str, content: str, source: str):
        """Add a document to the store."""
        embedding = await self._embed(content)
        self.documents.append(Document(
            id=doc_id,
            content=content,
            source=source,
            embedding=embedding,
        ))

    async def search(self, query: str, top_k: int = 3) -> list[Document]:
        """Search for the most relevant documents."""
        query_embedding = await self._embed(query)
        scored = [
            (doc, cosine_similarity(query_embedding, doc.embedding))
            for doc in self.documents
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in scored[:top_k]]


# ============================================================================
# RAG Agent
# ============================================================================

class RAGAgent(BaseAgent):
    """
    A Retrieval-Augmented Generation agent.

    The agent has access to a vector store of documents. When asked a question,
    it retrieves relevant context and uses it to generate an informed answer.
    """

    def __init__(self, vector_store: VectorStore, client: Optional[AsyncOpenAI] = None):
        self.vector_store = vector_store
        super().__init__(
            name="RAGAgent",
            system_prompt=(
                "You are a knowledgeable assistant. When answering questions, "
                "ALWAYS use the search_knowledge tool first to find relevant information. "
                "Base your answers on the retrieved documents. "
                "If the documents don't contain enough information, say so honestly. "
                "Always cite which source your information comes from."
            ),
            client=client,
        )

    @AgentToolkit.register_as_tool
    async def search_knowledge(self, query: str) -> str:
        """
        Search the knowledge base for relevant documents.

        Args:
            query (str): Search query describing what information you need

        Returns:
            Relevant documents from the knowledge base
        """
        results = await self.vector_store.search(query, top_k=3)
        if not results:
            return "No relevant documents found."

        formatted = []
        for i, doc in enumerate(results, 1):
            formatted.append(f"[{i}] Source: {doc.source}\n{doc.content}")
        return "\n\n---\n\n".join(formatted)


# ============================================================================
# Sample knowledge base
# ============================================================================

KNOWLEDGE_BASE = [
    {
        "id": "fractal-overview",
        "source": "Fractal Documentation",
        "content": (
            "Fractal is a Python framework for building multi-agent AI systems "
            "through recursive delegation. Agents delegate sub-tasks to specialist "
            "agents, forming tree-shaped workflows. It works with any OpenAI-compatible "
            "API endpoint including Azure, Ollama, and LM Studio."
        ),
    },
    {
        "id": "fractal-tools",
        "source": "Fractal Documentation",
        "content": (
            "In Fractal, tools are registered using the @AgentToolkit.register_as_tool "
            "decorator on agent methods. The framework automatically parses Google-style "
            "docstrings into OpenAI tool schemas. Both sync and async tools are supported."
        ),
    },
    {
        "id": "fractal-tracing",
        "source": "Fractal Documentation",
        "content": (
            "Fractal includes built-in observability via TracingKit. When enabled on the "
            "top-level agent, tracing automatically propagates through the entire delegation "
            "chain. Traces can be exported to JSON Lines format and viewed in the terminal "
            "or as interactive HTML visualizations."
        ),
    },
    {
        "id": "fractal-delegation",
        "source": "Fractal Documentation",
        "content": (
            "Delegation in Fractal is set up with register_delegate(). A coordinator agent "
            "registers specialist agents as callable tools. Delegation can be nested to "
            "arbitrary depth (A -> B -> C -> ...). Each agent manages its own conversation "
            "history and context window independently."
        ),
    },
    {
        "id": "fractal-context",
        "source": "Fractal Documentation",
        "content": (
            "Fractal supports automatic context window management. By setting the "
            "context_window parameter (e.g., context_window=128000), the agent will "
            "automatically trim old conversation history before each API call. The system "
            "message is always preserved, and tool-call groups are never split."
        ),
    },
    {
        "id": "python-asyncio",
        "source": "Python Docs",
        "content": (
            "asyncio is a library to write concurrent code using the async/await syntax. "
            "It is used as a foundation for multiple Python asynchronous frameworks. "
            "Key concepts include coroutines, tasks, event loops, and awaitables."
        ),
    },
]


# ============================================================================
# Main
# ============================================================================

async def main():
    client = AsyncOpenAI()

    # Build the vector store
    print("Indexing knowledge base...")
    store = VectorStore(client)
    for doc in KNOWLEDGE_BASE:
        await store.add_document(doc["id"], doc["content"], doc["source"])
    print(f"Indexed {len(store.documents)} documents.\n")

    # Create the RAG agent
    agent = RAGAgent(vector_store=store, client=client)
    print(agent)  # Show agent info

    # Ask questions
    questions = [
        "How does delegation work in Fractal?",
        "What is Fractal's tracing feature?",
        "How do I register tools in Fractal?",
    ]

    for question in questions:
        print(f"\n{'=' * 60}")
        print(f"Q: {question}")
        print("=" * 60)
        result = await agent.run(question)
        print(f"\nA: {result.content}")
        agent.reset()  # Clear history between questions


if __name__ == "__main__":
    asyncio.run(main())
