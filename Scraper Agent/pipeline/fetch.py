from pathlib import Path
import httpx, hashlib, time, random
from tenacity import retry, stop_after_attempt, wait_exponential
from playwright.sync_api import sync_playwright

RAW = Path("data/raw"); RAW.mkdir(parents=True, exist_ok=True)

def _path(url:str, rendered:bool)->Path:
    # Generate a unique file path based on the URL's hash
    h = hashlib.sha1(url.encode()).hexdigest()
    return RAW / (h + (".rendered.html" if rendered else ".html"))

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1,max=8))
def fetch_static(url:str)->str:
# Attempt to fetch the URL's content statically (simple HTTP GET)
    time.sleep(random.uniform(1.0, 2.0))  # Polite delay between requests
    r = httpx.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=30)
    r.raise_for_status(); return r.text

def fetch_rendered(url:str)->str:
# Fallback: Use Playwright to render dynamic pages (e.g., JavaScript-loaded content)
    time.sleep(random.uniform(1.0, 2.0))  # Polite delay between requests
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_page()
        page.goto(url, timeout=45000)
        html = page.content()
        b.close()
        return html

def fetch_with_cache(item):
    # Process a single URL item (e.g., {"url": "https://sfbos.org/roster-members", "tier": "gov"})
    url = item["url"]  # Extract the URL from the dict passed by model_search
    tier = item["tier"]  # Tier info (e.g., "gov") is available but not used here
    p = _path(url, rendered=False)
    if p.exists():  # Check if cached version exists
        return {"url": url, "tier": tier, "rendered": False, "path": str(p)}
    try:
        html = fetch_static(url)  # Try static fetch first
        p.write_text(html, encoding="utf-8")
        return {"url": url, "tier": tier, "rendered": False, "path": str(p)}
    except Exception:
        p2 = _path(url, rendered=True)  # Fallback path for rendered content
        html = fetch_rendered(url)
        p2.write_text(html, encoding="utf-8")
        return {"url": url, "tier": tier, "rendered": True, "path": str(p2)}
