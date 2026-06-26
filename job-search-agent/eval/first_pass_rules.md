# First-Pass Filter Rules

Apply these rules using only the metadata visible from the listing preview (title, location, salary, seniority). Do not read the full JD at this stage.

## Title Filter
See `eval/title_filter.md` for full guidance. Titles are **not** a hard gate — many non-standard titles (GTM Analyst, Strategy Analyst) have matching job content. Only hard-reject titles that are clearly wrong function (Data Engineer, ML Engineer, etc.).

## Seniority Filter
- **Accept:** Mid, Senior, IC levels
- **Reject:** Intern, Junior, Entry Level, Associate (context-dependent), Lead, Principal, Director, VP, C-level

## Location Filter
- **Accept:** Remote (US), Hybrid with quarterly in-office
- **Reject:** On-site only, non-US locations, roles requiring non-US work authorization

**Critical:** Do NOT infer onsite from a city/state in the location header. Company HQ addresses routinely appear as the listing location even for fully remote roles. Only reject on location if the job description body explicitly uses language like "must be in office", "hybrid X days/week", "on-site required", or "not remote". If a listing appeared in a remote-filtered search (LinkedIn f_WT=2, BuiltIn remote URL, SimplyHired remote filter) and the body has no explicit onsite language, treat it as remote-unconfirmed and pass it through — do not reject.

## Compensation Filter (tiered by equity reliability)

Default to **$135K floor** unless the company is on a known list below.

| Company Type | Minimum Top-of-Range | Rationale |
|---|---|---|
| Public companies | $110,000 | RSUs are liquid |
| Late-stage private with liquid equity (Tier 2) | $110,000 | Secondary market / tender offers |
| All other private companies | $135,000 | Equity is illiquid/speculative |

### Evaluation Logic
1. If top of base range >= $135K -> **PASS** (no lookup needed)
2. If top of base range < $110K -> **REJECT** (no lookup needed)
3. If top of base range is $110K-$134K -> check if company is public or on the Tier 2 list below. If unknown, do a quick lookup. If neither public nor Tier 2 -> **REJECT**.

### Known Public Companies (non-exhaustive -- verify via quick lookup if unsure)
Airbnb, Alma, Atlassian, Block (Square), Chegg, Cloudflare, Coinbase, CrowdStrike,
Datadog, DocuSign, Doximity, Dropbox, DoorDash, Elastic, Etsy, Fastly, Five9,
GitLab, Google/Alphabet, HubSpot, Instacart, Lyft, Meta, MongoDB, Netflix,
Nextdoor, Okta, Palo Alto Networks, Pinterest, Reddit, Roku, Salesforce,
SeatGeek, Shopify, Snap, Snowflake, Spotify, Stripe*, Toast, Twilio, Uber,
Unity, Upstart, Veeam, Veeva, Zillow, Zoom
(*Stripe is private -- listed under Tier 2 below)

### Tier 2: Late-Stage Private with Liquid Equity ($5B+ valuation, secondary/tender programs)

**AI / ML:** OpenAI, Anthropic, xAI, Databricks, Scale AI, Cohere, Cerebras, Perplexity, Glean

**Fintech / Payments:** Stripe, Plaid, Deel, Gusto, Revolut, Ripple, Kraken, Mercury, Gemini, Upgrade, Chime

**Enterprise SaaS / Productivity:** Canva, Notion, Rippling, Discord, Airtable, Cohesity, Workato

**Cybersecurity:** Tanium, Snyk, Arctic Wolf, Verkada, Wiz, Lacework

**Aerospace / Defense Tech:** SpaceX, Anduril, Shield AI, Waymo

**Health Tech:** Devoted Health, Innovaccer

**Data / Cloud / Infrastructure:** Crusoe Energy, Lambda Labs, CoreWeave

**Gaming / Consumer:** Epic Games, Fanatics

**Criteria for adding to this list:** Private, $5B+ valuation, confirmed secondary market activity (EquityZen/Forge) or recurring tender offers, US presence with analytics-relevant roles.

## Role-Specific Salary Exceptions
- **Analytics Engineer titles:** Do not reject for missing salary. AE roles reliably clear the $135K floor — proceed to deep eval and note salary as unlisted in the result file.
- All other private company roles: no salary listed → reject (rule unchanged).

## Disqualifying Requirements (auto-reject if visible in preview)
- R required
- SAS required
- 10+ years of experience required
- Active security clearance required

## Warehouse / Tool Substitution (do NOT auto-reject)
Cloud data warehouse differences are transferable and should not be treated as hard failures:
- Snowflake ↔ BigQuery ↔ Redshift — all SQL-based, dbt-compatible; treat as equivalent unless the JD says "X required, no exceptions" or lists it as a **disqualifying** factor
- Only reject on warehouse mismatch if the role is explicitly a Snowflake/Redshift *administration* or *infrastructure* role (not analytics/AE work that happens to run on that warehouse)
- Similarly: dbt is dbt regardless of underlying warehouse — candidate's dbt experience is fully transferable

## Known Spam Sources (skip without evaluating)
Jobgether, Stott and May, Prestige Staffing, Swoon, HARAMAIN, Crossing Hurdles, and other staffing agencies/aggregators posting on behalf of unnamed clients.
