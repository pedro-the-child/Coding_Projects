import os
from xai_sdk import Client
from xai_sdk.chat import user
from xai_sdk.tools import web_search

client = Client(api_key=os.getenv("XAI_API_KEY"))

# Use the NEW agentic tool calling API (won't be deprecated)
chat = client.chat.create(
    model="grok-4-fast",
    tools=[web_search()],  # Server-side tool
)

chat.append(user("What is the latest update from xAI?"))

print("Using agentic tool calling API...")
print("Calling sample() in a loop until we get final content...\n")

# Simple loop: keep calling sample() until we get actual content
max_iterations = 10
for i in range(max_iterations):
    response = chat.sample()

    print(f"Iteration {i+1}:")
    print(f"  - Content length: {len(response.content) if response.content else 0}")
    print(f"  - Tool calls: {len(response.tool_calls) if response.tool_calls else 0}")

    # If we got content, we're done
    if response.content:
        print("\n=== Final Response ===")
        print(response.content)
        print(f"\nServer-side tool usage: {response.server_side_tool_usage}")
        break

    # If there are tool calls but no content, tools are still executing
    # Just call sample() again - the server handles tool execution
    if response.tool_calls:
        print("  - Tools executing server-side, calling sample() again...")
        continue
else:
    print("\nReached max iterations without final response")
