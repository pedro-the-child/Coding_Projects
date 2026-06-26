import os
import json
import re
from typing import List, Dict
from xai_sdk import Client
from xai_sdk.chat import user
from xai_sdk.tools import web_search

client = Client(api_key=os.getenv("XAI_API_KEY"))

PROMPT = """You are a research assistant.
Task: Given a jurisdiction name, return up to 5 official URLs for the CURRENT roster/directory of its legislative body.
Rules:
- Prefer .gov (or official city/state domains). Include council/assembly/commission directories, not news or Ballotpedia.
- Return STRICT JSON with this schema:
{{ "jurisdiction": "<input>",
  "urls": [ {{"url":"<string>", "reason":"<why this is official>"}} ]
}}
Jurisdiction: {jur_name}
"""

def discover_official_urls(jur_name: str) -> List[Dict]:
    msg = PROMPT.format(jur_name=jur_name)

    # Using server-side web_search tool (future-proof, not deprecated)
    # NOTE: Requires xai-sdk >= 1.3.1 (version 1.3.0 has bugs)
    chat = client.chat.create(
        model="grok-4-fast",
        tools=[web_search()],
    )

    chat.append(user(msg))

    # Server-side tools execute automatically, just call sample()
    response = chat.sample()
    text = response.content
    
    # Try to extract JSON from the response
    try:
        # First try direct JSON parse
        js = json.loads(text)
    except json.JSONDecodeError:
        # If that fails, try to extract JSON with regex
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            js = json.loads(match.group(0))
        else:
            print(f"Could not parse JSON from response: {text}")
            return []
    
    urls = js.get("urls", [])
    
    # Filter and deduplicate
    seen = set()
    result = []
    for u in urls:
        url = u.get("url", "")
        if url.startswith("http") and url not in seen:
            seen.add(url)
            result.append({
                "url": url, 
                "tier": "gov" if ".gov" in url or "city" in url or "state" in url else "civic"
            })
    
    return result[:8]