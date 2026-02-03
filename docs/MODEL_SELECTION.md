# Model Selection Guide

## Recommended Models by Use Case

### For Development & Testing: `gpt-4o-mini` ✅
- **Cost**: ~15x cheaper than GPT-4
- **Speed**: Faster response times
- **Use for**: Testing, development, simple tasks, high-volume applications
- **Pricing**: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens

### For Production Quality: `gpt-4o`
- **Cost**: Mid-range pricing
- **Speed**: Good balance
- **Use for**: Production applications requiring good quality
- **Pricing**: ~$2.50 per 1M input tokens, ~$10.00 per 1M output tokens

### For Best Quality: `gpt-4`
- **Cost**: Most expensive
- **Speed**: Slower
- **Use for**: Complex reasoning, critical applications, best possible output
- **Pricing**: ~$30 per 1M input tokens, ~$60 per 1M output tokens

## Cost Comparison Example

For 1,000 agent runs with average 1,000 tokens input + 500 tokens output each:

| Model | Total Tokens | Approximate Cost |
|-------|-------------|-----------------|
| gpt-4o-mini | 1.5M | ~$0.45 |
| gpt-4o | 1.5M | ~$7.50 |
| gpt-4 | 1.5M | ~$60.00 |

## Recommendation

**Start with `gpt-4o-mini`** for development and testing. Most agent tasks work well with this model, and you can always upgrade to `gpt-4` for specific agents that need better reasoning.

## Setting the Model

### Option 1: In Code
```python
agent = BaseAgent(
    name="MyAgent",
    system_prompt="...",
    toolkit=toolkit,
    model="gpt-4o-mini"  # Change here
)
```

### Option 2: Environment Variable
Add to your `.env` file:
```bash
OPENAI_MODEL=gpt-4o-mini
```

Then in code:
```python
import os
agent = BaseAgent(
    name="MyAgent",
    system_prompt="...",
    toolkit=toolkit,
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini")
)
```

### Option 3: Per-Agent Basis
Use different models for different agents:
```python
# Fast, cheap agent for simple tasks
simple_agent = BaseAgent(
    name="SimpleAgent",
    model="gpt-4o-mini",
    # ...
)

# High-quality agent for complex reasoning
complex_agent = BaseAgent(
    name="ComplexAgent",
    model="gpt-4",
    # ...
)
```

## Other OpenAI-Compatible Models

The framework works with any OpenAI-compatible API:

### Local Models (Free!)
- **Ollama**: Run models locally (llama3, mistral, etc.)
- **LM Studio**: Local model serving
- **vLLM**: High-performance inference

```python
agent = BaseAgent(
    name="LocalAgent",
    model="llama3",
    base_url="http://localhost:11434/v1",  # Ollama
    api_key="not-needed"
)
```

### Other Providers
- **Azure OpenAI**: Enterprise-grade hosting
- **Together AI**: Fast inference with various models
- **Anyscale**: Serverless LLM endpoints

See the main README for more details on custom endpoints.
