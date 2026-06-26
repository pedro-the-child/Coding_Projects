import os
from xai_sdk import Client
from xai_sdk.chat import user
from xai_sdk.tools import web_search

client = Client(api_key=os.getenv("XAI_API_KEY"))
chat = client.chat.create(model="grok-4-fast", tools=[web_search()])
chat.append(user("What was announced by xAI yesterday?"))  # Needs search

print("Testing SERVER-SIDE tool execution (no tool_result() calls)")
print("Starting loop...\n")

for i in range(5):
    print(f"Iteration {i+1}")
    response = chat.sample()

    print(f"  Content: {response.content[:100] if response.content else 'NONE'}...")
    print(f"  Tool calls: {len(response.tool_calls) if response.tool_calls else 0}")

    if response.tool_calls:
        for tc in response.tool_calls:
            print(f"    - {tc.function.name}: {tc.function.arguments[:50]}...")

    # Check if we have server-side tool usage
    if hasattr(response, 'server_side_tool_usage'):
        print(f"  Server-side tools: {response.server_side_tool_usage}")

    # If we have content, we're done
    if response.content:
        print("\n=== Final Response ===")
        print(response.content)
        break

    # Key difference: DON'T call chat.append(tool_result(...))
    # Let the SERVER handle tool execution
    print("  Waiting for server-side tool execution...")

print("\nDone!")
