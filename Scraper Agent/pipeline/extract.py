import os
import re
import phonenumbers
import json
from xai_sdk import Client
from xai_sdk.chat import user
from pipeline.fetch import fetch_with_cache

client = Client(api_key=os.getenv("XAI_API_KEY"))

# Regex pattern for emails
EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)

def extract_emails(text):
    """Extract email addresses from text"""
    return sorted(set(re.findall(EMAIL_RE, text or "")))

def extract_phones(text, region="US"):
    """Extract phone numbers from text"""
    out = set()
    for m in phonenumbers.PhoneNumberMatcher(text or "", region):
        out.add(phonenumbers.format_number(m.number, phonenumbers.PhoneNumberFormat.E164))
    return sorted(out)

# LLM prompt for extracting person metadata
SCHEMA = """Return STRICT JSON:
{{"full_name":"<string>","role_title":"<string>","body_name":"<string>",
 "chamber":"<string|null>","district":"<string|null>","party":"<string|null>","notes":"<string|null>"}}
Rules:
- Use only facts in the text. If unsure, set null.
- Map titles to common forms (council member, commissioner, senator, representative, mayor).
- If staff, set notes="staff".
Jurisdiction: {jur}
URL: {url}
Text:
{snippet}
"""

def model_map_person(snippet: str, jur: str, url: str) -> dict:
    """Use LLM to extract person metadata from text"""
    prompt = SCHEMA.format(jur=jur, url=url, snippet=snippet[:1800])

    chat = client.chat.create(model="grok-4-fast")
    chat.append(user(prompt))
    response = chat.sample()
    text = response.content

    try:
        js = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*?\}", text, re.DOTALL)
        if match:
            js = json.loads(match.group(0))
        else:
            return {}

    if isinstance(js, list):
        return js[0] if js else {}

    return js

def identify_detail_link_with_llm(person_name, links):
    """
    Use LLM to identify which link (if any) leads to the person's detail page.
    Returns: index of the correct link or None
    """
    if not links:
        return None

    # Format links for LLM
    links_str = "\n".join([f"{i}. {link['text']} -> {link['url']}" for i, link in enumerate(links)])

    prompt = f"""Person: {person_name}
Links in their block:
{links_str}

Which link number (0, 1, 2...) leads to their detail/profile page with contact information?
Return ONLY the number, or "none" if no suitable link exists.
Examples: "0", "1", "none"
"""

    chat = client.chat.create(model="grok-3")
    chat.append(user(prompt))
    response = chat.sample()
    answer = response.content.strip().lower()

    # Parse response
    if answer == "none":
        return None
    try:
        return int(answer)
    except:
        return None

def extract_link_pattern(block_element, correct_link_index, person_name):
    """
    Given the HTML element and which link was correct,
    extract a pattern that can be applied to other blocks.
    """
    all_links = block_element.find_all('a', href=True)

    if correct_link_index is None or correct_link_index >= len(all_links):
        return None

    correct_link = all_links[correct_link_index]

    # Try multiple pattern strategies in order of preference

    # Pattern 1: Link contains person's name in href
    name_parts = [part.lower() for part in person_name.split() if len(part) > 2]
    if name_parts and any(part in correct_link.get('href', '').lower() for part in name_parts):
        return {"type": "name_in_href"}

    # Pattern 2: Link has specific CSS classes
    if correct_link.get('class'):
        return {"type": "class", "classes": correct_link['class']}

    # Pattern 3: Simple position (most common fallback)
    return {"type": "position", "index": correct_link_index}

def apply_link_pattern(block_element, pattern, person_name):
    """
    Apply the discovered pattern to extract the detail link from a block.
    Returns: URL string or None
    """
    if pattern is None:
        return None

    all_links = block_element.find_all('a', href=True)

    if not all_links:
        return None

    if pattern["type"] == "name_in_href":
        # Find link with person's name in href
        name_parts = [part.lower() for part in person_name.split() if len(part) > 2]
        for link in all_links:
            href = link.get('href', '').lower()
            if any(part in href for part in name_parts):
                return link['href']
        return None

    elif pattern["type"] == "class":
        # Find link with matching classes
        link = block_element.find('a', class_=pattern["classes"])
        return link['href'] if link else None

    elif pattern["type"] == "position":
        # Use positional index
        idx = pattern["index"]
        if idx < len(all_links):
            return all_links[idx]['href']
        return None

    return None

def extract_from_block(block, jur_name, page_url):
    """Extract person data from a single block"""
    text = block["text"]

    # Skip very short blocks
    if len(text.split()) < 3:
        return None

    # Deterministic extraction
    emails = extract_emails(text)
    phones = extract_phones(text)

    # LLM extraction for metadata
    meta = model_map_person(text, jur_name, page_url)

    # Skip if no name found
    if not meta.get("full_name"):
        return None

    return {
        **meta,
        "emails": emails,
        "phones": phones,
        "detail_links": block["links"],
        "source_url": page_url
    }

def enrich_with_detail_page(person, detail_url):
    """
    Fetch a detail page and extract contact info.
    Returns: updated person dict
    """
    # Already has complete contact info
    if person.get("emails") and person.get("phones"):
        return person

    try:
        # Fetch detail page
        from urllib.parse import urljoin
        full_url = urljoin(person["source_url"], detail_url)

        detail_rec = fetch_with_cache({"url": full_url, "tier": "detail"})

        # Simple text extraction (no need for full parse)
        from pathlib import Path
        detail_html = Path(detail_rec["path"]).read_text(encoding="utf-8", errors="ignore")
        from bs4 import BeautifulSoup
        detail_soup = BeautifulSoup(detail_html, 'html.parser')
        detail_text = detail_soup.get_text(separator='\n', strip=True)

        # Extract contact info only (deterministic)
        if not person.get("emails"):
            emails = extract_emails(detail_text)
            if emails:
                person["emails"] = emails

        if not person.get("phones"):
            phones = extract_phones(detail_text)
            if phones:
                person["phones"] = phones

    except Exception as e:
        # Skip links that fail to fetch
        print(f"    Failed to fetch {detail_url}: {e}")

    return person

def extract_from_page(page: dict, jur_name: str) -> list[dict]:
    """Extract person data from a parsed page using pattern-based link detection"""
    people = []
    blocks = page.get("blocks", [])
    print(f"  Found {len(blocks)} blocks")

    # Phase 1: Extract from blocks on current page
    for block in blocks:
        person = extract_from_block(block, jur_name, page["url"])
        if person:
            person["tier"] = page["tier"]
            # Store the HTML element for pattern matching
            person["_block_element"] = block.get("element")
            people.append(person)

    print(f"  Extracted {len(people)} people from page")

    # Phase 2: Smart pattern-based detail page enrichment
    missing_contact = sum(1 for p in people if not p.get("emails") or not p.get("phones"))
    if missing_contact > 0 and people:
        print(f"  {missing_contact} people missing contact info, using pattern-based enrichment...")

        # Step 1: Use LLM to find correct link for first person
        first_person = people[0]
        if first_person.get("detail_links") and first_person.get("_block_element"):
            print(f"  Identifying detail link pattern using first person: {first_person.get('full_name')}")
            link_index = identify_detail_link_with_llm(
                first_person.get("full_name", ""),
                first_person.get("detail_links", [])
            )

            if link_index is not None:
                print(f"    → LLM selected link {link_index}: {first_person['detail_links'][link_index]['url']}")

                # Step 2: Extract the pattern
                pattern = extract_link_pattern(
                    first_person["_block_element"],
                    link_index,
                    first_person.get("full_name", "")
                )
                print(f"    → Extracted pattern: {pattern}")

                # Step 3: Apply pattern to all people (including first person)
                if pattern:
                    for person in people:
                        # Skip if already has complete info
                        if person.get("emails") and person.get("phones"):
                            continue

                        # Apply pattern to find detail URL
                        if person.get("_block_element"):
                            detail_url = apply_link_pattern(
                                person["_block_element"],
                                pattern,
                                person.get("full_name", "")
                            )

                            if detail_url:
                                print(f"    Enriching {person.get('full_name')} from {detail_url}")
                                enrich_with_detail_page(person, detail_url)
            else:
                print(f"    → LLM found no suitable detail links")

    # Clean up temporary fields
    for person in people:
        person.pop("_block_element", None)

    return people
