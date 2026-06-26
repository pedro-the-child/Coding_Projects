import hashlib
from pathlib import Path

# Common SF Board of Supervisors URLs to check against
potential_urls = [
    "https://sfbos.org/",
    "https://sfbos.org/roster",
    "https://sfbos.org/roster-members",
    "https://sfbos.org/supervisors",
    "https://www.sf.gov/departments/board-supervisors",
    "https://sfgov.org/bdofsupervisors/",
    "https://sfgov.org/bdofsupervisors/roster",
]

# Get all cached files
cached_files = list(Path("data/raw").glob("*.html"))
print(f"Found {len(cached_files)} cached files\n")

# Try to match cached files to URLs
for cached in cached_files:
    filename = cached.stem.replace(".rendered", "")
    print(f"File: {cached.name}")
    print(f"Hash: {filename}")
    
    # Try to find matching URL
    matched = False
    for url in potential_urls:
        h = hashlib.sha1(url.encode()).hexdigest()
        if h == filename:
            print(f"URL: {url}")
            matched = True
            break
    
    if not matched:
        print("URL: <unknown - not in common list>")
    
    print()


