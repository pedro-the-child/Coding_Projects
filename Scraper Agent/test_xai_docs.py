import os
from xai_sdk import Client
from xai_sdk.chat import user
from xai_sdk.tools import web_search

client = Client(api_key=os.getenv("XAI_API_KEY"))
chat = client.chat.create(
    model="grok-4-fast",  # reasoning model
    tools=[web_search()],
)

chat.append(user("What is the latest update from xAI?"))

print("Calling chat.sample() once...")
# Get the final response in one go once it's ready
response = chat.sample()

print("\nFinal Response:")
print(response.content if response.content else "EMPTY CONTENT")

print("\n\nTool Calls:")
print(f"Count: {len(response.tool_calls) if response.tool_calls else 0}")

print("\n\nUsage:")
if hasattr(response, 'usage'):
    print(response.usage)
else:
    print("No usage attribute")

if hasattr(response, 'server_side_tool_usage'):
    print("\n\nServer Side Tool Usage:")
    print(response.server_side_tool_usage)


