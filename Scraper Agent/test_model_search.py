import os
import sys
import json

# Add the parent directory to the path so we can import from pipeline
sys.path.insert(0, os.path.dirname(__file__))

from pipeline.model_search import discover_official_urls

# Test with a sample jurisdiction
jurisdiction = "San Francisco, CA"

print(f"Testing model_search with jurisdiction: {jurisdiction}")
print("-" * 60)

try:
    results = discover_official_urls(jurisdiction)
    print(f"\nFound {len(results)} URLs:")
    print(json.dumps(results, indent=2))
except Exception as e:
    import traceback
    print(f"Error: {type(e).__name__}: {e}")
    print("\nFull traceback:")
    traceback.print_exc()

