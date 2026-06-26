import os
import json
from xai_sdk import Client
from xai_sdk.chat import user, tool_result
from xai_sdk.tools import web_search

client = Client(api_key=os.getenv("XAI_API_KEY"))
chat = client.chat.create(model="grok-4-fast", tools=[web_search()])
chat.append(user("What is the capital of Mars?"))  # Question that can't be answered without search

print("Starting loop...")
for i in range(5):
    print(f"\nIteration {i+1}")
    response = chat.sample()

    print(f"  Content length: {len(response.content) if response.content else 0}")
    print(f"  Tool calls: {len(response.tool_calls) if response.tool_calls else 0}")

    if response.content and not response.tool_calls:
        print("\n=== Final Response ===")
        print(response.content)
        break

    if response.tool_calls:
        for tc in response.tool_calls:
            print(f"  Tool call: {tc.function.name}")
            print(f"  Arguments: {tc.function.arguments}")
            if tc.function.name == "web_search":
                # Mock client-side tool result
                results = json.dumps([{"title": "Mars", "snippet": "Mars has no capital city as it's uninhabited."}])
                chat.append(tool_result(results))
                print(f"  Appended mock tool result")

print("\nDone!")
