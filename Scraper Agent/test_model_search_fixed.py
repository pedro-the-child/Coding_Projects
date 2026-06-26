from pipeline.model_search import discover_official_urls

# Test the fixed model_search
print("Testing model_search with Austin City Council...\n")
urls = discover_official_urls("Austin City Council")

print(f"\nFound {len(urls)} URLs:")
for i, url_obj in enumerate(urls, 1):
    print(f"{i}. {url_obj['url']} (tier: {url_obj['tier']})")
