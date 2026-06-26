import os
from xai_sdk import Client
from xai_sdk.chat import user
from xai_sdk.search import SearchParameters, web_source

client = Client(api_key=os.getenv("XAI_API_KEY"))

# Use search_parameters instead of tools for single-call web search
chat = client.chat.create(
    model="grok-4-fast",
    search_parameters=SearchParameters(
        mode="on",  # Always perform search
        sources=[web_source(country="US")],
    ),
)

chat.append(user("What is the latest update from xAI?"))

print("Calling chat.sample() once with search_parameters...")
response = chat.sample()

print(f"\n=== Response ===")
print(f"Content: {response.content}")
print(f"\nCitations: {response.citations if hasattr(response, 'citations') else 'N/A'}")
print(f"\nUsage: {response.usage}")
