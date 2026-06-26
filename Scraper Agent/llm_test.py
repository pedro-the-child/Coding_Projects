import os
import json
from xai_sdk import Client
from xai_sdk.chat import user, tool_result
from xai_sdk.tools import web_search

client = Client(api_key=os.getenv("XAI_API_KEY"))
chat = client.chat.create(model="grok-4-fast", tools=[web_search()])
chat.append(user("summarize ai news for yesterday"))

for _ in range(2):
    response = chat.sample()
    
    if not response.tool_calls:
        break
        
    for tc in response.tool_calls:
        if tc.function.name == "web_search":
            args = json.loads(tc.function.arguments)
            # Mock results (replace with real search)
            results = json.dumps([{"title": "Mock AI News", "snippet": "Yesterday's AI update: Grok-4 released."}])
            chat.append(tool_result(results))

print(response.content)