# xAI Web Search APIs: Tool Calling vs Search Parameters

## TL;DR - SOLUTION FOUND! ✅

**Use `tools=[web_search()]` with either `chat.sample()` OR `chat.stream()`** - this is the future-proof API that won't be deprecated.

**Critical requirement**:
- `xai-sdk >= 1.3.1` (version 1.3.0 has bugs that cause empty responses)

## The Problem (SOLVED)

When using `tools=[web_search()]`, the response content was empty. This was because:
- **Wrong SDK version** - xai-sdk 1.3.0 had bugs preventing server-side tools from working correctly
- **Solution** - Upgrade to xai-sdk 1.3.1 and it works with both `sample()` and `stream()`

## Solution: Two Different APIs

xAI provides TWO different ways to use web search:

### 1. Tool Calling API (Multi-turn, Agentic)
**Pattern**: `tools=[web_search()]`

```python
from xai_sdk.tools import web_search

chat = client.chat.create(
    model="grok-4-fast",
    tools=[web_search()]
)
```

**Behavior**:
- Server-side agentic execution
- First `sample()` returns empty content with `tool_calls`
- Requires loop to handle multiple turns
- Tools execute server-side, outputs stay internal
- Used in `llm_test.py` (requires loop)

**When to use**: Complex multi-step tasks requiring multiple tool calls

### 2. Search Parameters API (Single-call, Direct) ✅ **USE THIS**
**Pattern**: `search_parameters=SearchParameters(...)`

```python
from xai_sdk.search import SearchParameters, web_source

chat = client.chat.create(
    model="grok-4-fast",
    search_parameters=SearchParameters(
        mode="on",  # Always perform search
        sources=[web_source(country="US")],
    ),
)
```

**Behavior**:
- Single `sample()` call returns complete response
- `response.content` contains the final answer
- `response.citations` contains source URLs
- No loops needed

**When to use**: Simple queries where you want web-augmented responses without complex agentic behavior

## Fixed Code

`model_search.py` now uses the **Search Parameters API**:

```python
from xai_sdk.search import SearchParameters, web_source

chat = client.chat.create(
    model="grok-4-fast",
    search_parameters=SearchParameters(
        mode="on",
        sources=[web_source(country="US")],
    ),
)

chat.append(user(msg))
response = chat.sample()  # Single call, gets content directly
text = response.content    # This now has content!
```

## Key Differences

| Feature | Tool Calling API | Search Parameters API |
|---------|-----------------|----------------------|
| Import | `from xai_sdk.tools import web_search` | `from xai_sdk.search import SearchParameters, web_source` |
| Usage | `tools=[web_search()]` | `search_parameters=SearchParameters(...)` |
| Calls needed | Multiple (loop) | Single |
| Content | Empty on first call | Populated immediately |
| Use case | Complex agentic tasks | Simple web-augmented queries |

## Test Files

- `test_search_api.py` - Working example with Search Parameters API ✅
- `test_websearch_simple.py` - Shows Tool Calling API requires multiple calls
- `test_xai_docs.py` - Original attempt (Tool Calling API, empty content)
- `llm_test.py` - Tool Calling API with loop
- `test_model_search_fixed.py` - Tests the fixed model_search.py

## Recommendation ✅

**Use the agentic `tools=[web_search()]` API** (implemented in model_search.py)
- ✅ Future-proof (won't be deprecated)
- ✅ Works with both `chat.sample()` and `chat.stream()`
- ✅ Real server-side tool execution
- ⚠️ Requires xai-sdk >= 1.3.1 (1.3.0 has bugs)

**Simple pattern with sample()**:
```python
from xai_sdk.tools import web_search

chat = client.chat.create(model="grok-4-fast", tools=[web_search()])
chat.append(user("your query"))

response = chat.sample()  # Server executes tools automatically
text = response.content   # Contains final response after tool execution
```

**Stream pattern** (if you want to see tool calls in real-time):
```python
text = ""
for response, chunk in chat.stream():
    if chunk.content:
        text += chunk.content
```

## References

- xAI SDK GitHub: https://github.com/xai-org/xai-sdk-python
- Example: `examples/sync/search.py` (uses SearchParameters)
- xAI Docs: https://docs.x.ai/docs/guides/tools/search-tools
- Deprecation notice: SearchParameters deprecated Dec 15, 2025
