import os
from xai_sdk import Client
from xai_sdk.chat import user
from xai_sdk.tools import web_search

client = Client(api_key=os.getenv("XAI_API_KEY"))
chat = client.chat.create(
    model="grok-4-fast",
    tools=[web_search()],
)

chat.append(user("What is the latest update from xAI?"))

print("Calling chat.sample() - this may trigger tool calls...")
response = chat.sample()

print(f"\n=== First Response ===")
print(f"Content: {response.content if response.content else 'EMPTY'}")
print(f"Tool calls: {len(response.tool_calls) if response.tool_calls else 0}")

# If there are tool calls but no content, the tools executed server-side
# We need to call sample() again to get the final answer
if response.tool_calls and not response.content:
    print("\n=== Tool calls detected, calling sample() again for final answer ===")
    response = chat.sample()

print(f"\n=== Final Response ===")
print(f"Content: {response.content}")
print(f"\nServer side tool usage: {response.server_side_tool_usage if hasattr(response, 'server_side_tool_usage') else 'N/A'}")

# Check for citations if available
if hasattr(response, 'citations') and response.citations:
    print(f"\nCitations: {response.citations}")
