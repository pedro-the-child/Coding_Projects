# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a scraper agent that extracts contact information for elected officials from government websites. It uses a multi-stage pipeline that:
1. Normalizes jurisdiction names (e.g., "NYC council" -> "New York City Council")
2. Uses Grok-4 Fast with web search to discover official government URLs
3. Fetches web pages (with Playwright fallback for JavaScript-heavy sites)
4. Parses HTML (special table handling for roster pages)
5. Extracts structured data using regex + LLM calls
6. Deduplicates people using fuzzy name matching
7. Exports to CSV with contact info

## Environment Setup

**Python**: 3.13.7 (virtual environment in `agent_env/`)

**Required environment variable**: `XAI_API_KEY` for x.AI Grok API access

**Activate virtual environment**:
```bash
source agent_env/bin/activate
```

**Key dependencies** (no requirements.txt exists):
- xai-sdk 1.3.0 (for Grok-4 Fast model)
- playwright 1.55.0 (for JavaScript rendering)
- httpx 0.28.1 (for static HTTP fetches)
- trafilatura 2.0.0 (for HTML text extraction)
- beautifulsoup4 4.14.2 (for table parsing)
- pandas 2.3.3 (for CSV export)
- rapidfuzz (for fuzzy name matching in deduplication)
- phonenumbers 9.0.16 (for phone extraction)
- tenacity 9.1.2 (for retry logic)

**Install Playwright browsers** (required for fetch.py):
```bash
playwright install chromium
```

## Running the Pipeline

**Full pipeline** (from jurisdiction name to CSV):
```bash
python -m pipeline.run "Austin City Council"
```

The pipeline runs sequentially through all stages and prints progress:
- `[normalize]` - jurisdiction name normalization
- `[model-search]` - URL discovery count
- `[fetch]` - pages fetched
- `[parse]` - pages parsed
- `[extract]` - raw people extracted
- `[resolve]` - unique people after deduplication
- `[export]` - CSV path
- `[report]` - report path

**Test scripts**:
```bash
python test_xai_docs.py          # Test xAI SDK web_search tool
python test_model_search.py      # Test URL discovery
python llm_test.py               # Test basic Grok chat
python show_urls.py              # Show discovered URLs
```

## Pipeline Architecture

All pipeline stages are in `pipeline/` directory. Each module implements one stage:

**1. normalize.py** (`normalize(input_str) -> Jurisdiction`)
- Maps user input to canonical jurisdiction name
- Uses `configs/aliases.csv` to handle variants (e.g., "NYC council" -> "New York City Council")
- Returns dataclass with: name, level (city/state/federal), country, region, aliases
- Falls back to "{name} Council" pattern for unknown inputs

**2. model_search.py** (`discover_official_urls(jur_name) -> List[Dict]`)
- Uses Grok-4 Fast + web_search tool to find official government URLs
- Returns list of `{"url": str, "tier": "gov"|"civic"}` dicts
- Filters for .gov domains and official sites
- Deduplicates, limits to 8 URLs
- JSON extraction with regex fallback for malformed responses

**3. fetch.py** (`fetch_with_cache(item) -> Dict`)
- Tries static HTTP fetch first (httpx with retry logic via tenacity)
- Falls back to Playwright browser rendering if static fails
- Caches HTML to `data/raw/` using URL hash as filename
- Returns: `{"url", "tier", "rendered": bool, "path": str}`
- Cache paths: `{hash}.html` (static) or `{hash}.rendered.html` (dynamic)

**4. parse.py** (`parse_doc(rec) -> Dict`)
- Special handling for roster/member pages with tables
- For table pages: extracts each cell as separate block (handles multi-column layouts)
- Falls back to trafilatura for non-table pages
- Returns: `{"url", "tier", "rendered", "text": str}`
- Text limited to 200,000 chars

**5. extract.py** (`extract_from_page(page, jur_name) -> List[Dict]`)
- **Two-phase extraction**:
  - Phase 1: Regex for emails (EMAIL_RE) and phones (phonenumbers library)
  - Phase 2: Grok-4 Fast for structured person data (name, title, chamber, district, party)
- **Text splitting** (split_people_blocks): 3 strategies:
  - Strategy 1: Double-newline splits for detailed pages
  - Strategy 2: Single lines with role keywords for compact lists
  - Strategy 3: Inline splitting on role patterns (e.g., "District 1", "Mayor")
- **LLM extraction** (model_map_person): Strict JSON schema for person metadata
- Returns list of person dicts with: full_name, role_title, body_name, chamber, district, party, emails, phones, source_url, tier

**6. resolve.py** (`cluster_people(people, threshold=90) -> List[Dict]`)
- Uses rapidfuzz token_set_ratio for fuzzy name matching
- Default threshold: 90 (configurable)
- Generates UUID for each unique person
- Merges contact info (emails, phones) from all matches
- Tracks all source URLs where person appears

**7. export.py** (`export(jur_name, people) -> str`)
- Converts to pandas DataFrame
- Outputs to `data/outputs/{jurisdiction}.csv`
- Schema: jurisdiction, body_name, person_id, full_name, role_title, chamber, district, party, email_primary, phone_primary, source_count

**8. report.py** (`report(csv_path) -> str`)
- Generates summary stats: found_members, pct_email, pct_phone
- Outputs to `data/reports/{jurisdiction}_report.csv`

## Configuration Files

**configs/aliases.csv** - Jurisdiction name normalization table
- Columns: input, normalized_name, level, country, region, aliases (pipe-separated)
- Used by normalize.py to map variants to canonical names

**configs/title_dictionary.yaml** - Role title reference (currently unused in code)
- Categories: legislator_titles, executive_titles, staff_markers

**configs/queries.yaml** - Empty (reserved for future search query templates)

## Data Directory Structure

```
data/
├── raw/           # Cached HTML files (by URL hash)
├── parsed/        # Not currently used
├── outputs/       # Final CSVs ({jurisdiction}.csv)
└── reports/       # Summary reports ({jurisdiction}_report.csv)
```

## Key Implementation Details

**LLM Strategy**: Two-phase extraction (regex for contact info, LLM for structured data) balances precision and recall.

**Web Fetch Strategy**: Static-first with Playwright fallback minimizes resource usage while handling JavaScript.

**Table Parsing**: Cell-by-cell extraction (not row-by-row) handles multi-column roster layouts where one row contains multiple people.

**Text Splitting**: Three-strategy approach handles various page layouts (detailed bios, compact lists, inline text).

**Deduplication**: Fuzzy matching accounts for name variations (nicknames, middle initials, etc.).

**API Usage**: All LLM calls use Grok-4 Fast (fast, cost-effective for structured extraction).

## Common Patterns

**When adding new jurisdictions**: Add entries to `configs/aliases.csv`

**When URLs are missed**: Check model_search.py prompt or increase URL limit (currently 8)

**When extraction fails**:
- Check parse.py table detection logic (looks for "roster" or "members" in URL)
- Check extract.py splitting strategies (may need new pattern for unusual page layouts)

**When deduplication merges wrong people**: Lower threshold in resolve.py cluster_people call (default 90)

**When deduplication misses duplicates**: Raise threshold or check name normalization in resolve.py _norm function
