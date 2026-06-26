import os
from xai_sdk import Client
from xai_sdk.chat import user
from xai_sdk.tools import web_search

client = Client(api_key=os.getenv("XAI_API_KEY"))
chat = client.chat.create(
    model="grok-4-fast",
    tools=[web_search()],  # Just web search
)

chat.append(user("Find official URLs for Austin City Council roster"))

print("Streaming response with server-side web search...\n")

try:
    for response, chunk in chat.stream():
        # Show tool calls
        for tool_call in chunk.tool_calls:
            print(f"\n[TOOL CALL] {tool_call.function.name}: {tool_call.function.arguments[:100]}...")

        # Show content as it streams
        if chunk.content:
            print(chunk.content, end="", flush=True)

    print("\n\n=== Final Response ===")
    print(f"Content length: {len(response.content) if response.content else 0}")
    print(f"Tool calls made: {len(response.tool_calls) if response.tool_calls else 0}")
    if hasattr(response, 'server_side_tool_usage'):
        print(f"Server-side usage: {response.server_side_tool_usage}")
    if hasattr(response, 'citations'):
        print(f"Citations: {len(response.citations) if response.citations else 0}")

except Exception as e:
    print(f"\n\nError occurred: {type(e).__name__}: {e}")
    print("But we may have gotten partial results before the error")
