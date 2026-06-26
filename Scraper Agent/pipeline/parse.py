from pathlib import Path
from bs4 import BeautifulSoup
from collections import Counter
from urllib.parse import urljoin

def parse_doc(rec): #Parse HTML document, preserving structure and links.
    html = Path(rec["path"]).read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, 'html.parser')
    base_url = rec["url"]

    # Find content blocks (hierarchy of strategies)
    blocks = find_content_blocks(soup, base_url)

    return {
        "url": rec["url"],
        "tier": rec["tier"],
        "rendered": rec["rendered"],
        "blocks": blocks
    }

def find_content_blocks(soup, base_url):
    """
    Find blocks that likely contain one person/entity.
    Uses hierarchy: try specific → generic
    """

    # Priority 1: Table rows (most structured)
    rows = soup.find_all('tr')
    if len(rows) > 2:  # More than just header
        non_header_rows = [row for row in rows if not is_header_row(row)]
        if len(non_header_rows) > 2:
            return [extract_block_data(row, base_url) for row in non_header_rows]

    # Priority 2: Repeated div patterns (e.g., member cards)
    repeated = find_repeated_elements(soup)
    if repeated and len(repeated) > 2:
        return [extract_block_data(elem, base_url) for elem in repeated]

    # Priority 3: List items (but skip if they're mostly navigation)
    list_items = soup.find_all('li')
    if len(list_items) > 2:
        # Check if list items contain substantial content (not just nav links)
        substantial_items = [li for li in list_items if len(li.get_text(strip=True).split()) > 10]
        if len(substantial_items) > 2:
            return [extract_block_data(item, base_url) for item in substantial_items]

    # Priority 4: Section/article tags
    sections = soup.find_all(['section', 'article'])
    if sections and len(sections) > 2:
        return [extract_block_data(sec, base_url) for sec in sections]

    # Fallback: Split by headings
    heading_blocks = split_by_headings(soup)
    if heading_blocks:
        return [extract_block_data(block, base_url) for block in heading_blocks]

    # Last resort: return whole page as one block
    return [extract_block_data(soup, base_url)]

def is_header_row(row):
    """Detect if table row is a header"""
    # Has <th> tags
    if row.find('th'):
        return True
    # First row with bold text
    if row.find_parent('table').find('tr') == row and row.find(['strong', 'b']):
        return True
    return False

def find_repeated_elements(soup, min_count=3):
    """
    Find divs with same class that repeat multiple times.
    E.g., <div class="member-card"> appearing 10 times
    """
    # Count div classes (use frozenset for matching)
    div_classes = []
    div_elements = []
    for div in soup.find_all('div', class_=True):
        # Skip divs with very little content
        text = div.get_text(strip=True)
        if len(text.split()) < 5:  # Less than 5 words
            continue

        class_set = frozenset(div.get('class', []))
        if class_set:  # Not empty
            div_classes.append(class_set)
            div_elements.append(div)

    if not div_classes:
        return None

    # Find most common class combination (that has substance)
    counts = Counter(div_classes)
    most_common_class, count = counts.most_common(1)[0]

    if count >= min_count:
        # Return all divs with that exact class combination
        return [div for div in div_elements if frozenset(div.get('class', [])) == most_common_class]

    return None

def split_by_headings(soup):
    """
    Split content by <h2>/<h3> headings.
    Each heading + following content = one block
    """
    headings = soup.find_all(['h2', 'h3'])
    if not headings:
        return None

    blocks = []
    for heading in headings:
        # Collect siblings until next heading
        block_elements = [heading]
        for sibling in heading.find_next_siblings():
            if sibling.name in ['h2', 'h3']:
                break
            block_elements.append(sibling)

        # Create container for this block
        container = soup.new_tag('div')
        for elem in block_elements:
            container.append(elem)
        blocks.append(container)

    return blocks if len(blocks) > 2 else None

def extract_block_data(element, base_url):
    """Extract text, links, and preserve HTML element from a block"""
    return {
        "text": element.get_text(separator='\n', strip=True),
        "links": extract_links(element, base_url),
        "element": element  # Preserve for pattern matching
    }

def extract_links(element, base_url):
    """Extract all links from an element"""
    links = []
    for a in element.find_all('a', href=True):
        href = a['href']
        # Convert relative URLs to absolute
        full_url = urljoin(base_url, href)
        links.append({
            "url": full_url,
            "text": a.get_text(strip=True)
        })
    return links
