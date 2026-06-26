# Job Search Agent Instructions

You are a job search agent. When invoked, run the full workflow below from start to finish without asking for confirmation at each step. Only pause if you encounter an ambiguous case that requires human judgment.

Always read `profile.md` before beginning any evaluation.
Always check `dedup_index.txt` before evaluating any posting.
Always append to both `reviewed_jobs.txt` (human-readable log) and
`dedup_index.txt` (identifier only) immediately after evaluating each job,
before moving to the next — do not batch writes.
Write result files only for jobs that pass all layers of filtering.
Be conservative: when in doubt about fit, do not write a result file.
Never skip a job due to canonical URL resolution failure — fall back to
fingerprint or job board URL instead, and log which method was used.

## File Structure
- `profile.md` — candidate identity (target roles, skills, domain experience, hard requirements)
- `dedup_index.txt` — one identifier per line, used for fast dedup lookups (load this, not reviewed_jobs.txt)
- `reviewed_jobs.txt` — human-readable evaluation log (append to, but do not load into context for dedup)
- `eval/first_pass_rules.md` — title filter, salary tiers, company lists, disqualifying requirements
- `eval/deep_eval_rubric.md` — scoring framework, pass/fail thresholds, result file template
- `eval/candidate_skills.md` — skills and experience for deep eval matching
- `eval/title_filter.md` — accepted/rejected titles, known spam sources
- `searches.md` — search queries for each session

## Dedup Entry Format
Each line in `reviewed_jobs.txt`:
```
[dedup_method] | [identifier] | [company] | [title] | [date_evaluated]
```
Methods: `canonical`, `fingerprint`, `jobboard`

## Result File Naming
`results/YYYY-MM-DD_CompanyName_JobTitle.md`

## Run Log Location
`logs/YYYY-MM-DD_run.log` — append summary at end of each session.

---

## Workflow

### Step 1: Load Context
- Read `profile.md` in full
- Read `dedup_index.txt` into memory as a lookup set (not reviewed_jobs.txt)
- Read `searches.md` to get the list of queries for this session

**Incomplete entry recovery:** After loading `dedup_index.txt`, scan `reviewed_jobs.txt` for any lines that contain none of the keywords `PASS`, `REJECT`, or `SKIP` — these are evaluations that were started but never completed (e.g., due to context window exhaustion). Collect the identifier field (column 2) from each such line and add it to a **re-evaluation queue**. When these identifiers are encountered during Step 3 dedup checks, bypass the dedup skip and re-evaluate them — then update the `reviewed_jobs.txt` entry in place with the outcome.

### Step 2: Execute Searches
For each query in `searches.md`, use the method matching the board type:

**Direct URL fetch (LinkedIn, BuiltIn, SimplyHired):**
- Use WebFetch on the URL directly and extract all job posting URLs/titles from the HTML
- Each fetch typically returns 20-60 results in a single request

**Google site: search (Greenhouse, Lever):**
- Use WebSearch with the `site:` query to find individual ATS job posting URLs

For all methods:
- Quick dedup check against `dedup_index.txt` at job board URL level
- Filter out known spam sources listed in `eval/title_filter.md`
- Filter out obvious title mismatches before returning results (Data Engineer, Data Scientist, ML Engineer, Software Engineer, Intern, Junior, Director, VP, and other hard-reject titles from `eval/title_filter.md`)
- Return only new, non-spam, plausibly relevant candidates — do not return every raw result from the page
- Add new URLs to the session's pending evaluation list

### Step 3: Canonical URL Resolution + Deduplication
For every candidate URL, resolve to the most authoritative identifier. The goal is to find the **company's own ATS posting URL** (Greenhouse, Lever, Workday, Ashby, ApplyToJob, SmartRecruiters, etc.) rather than using aggregator URLs.

**How to resolve canonical URLs by source:**

- **LinkedIn:** Most listings have an external "Apply" link that points to the company's ATS (Greenhouse, Lever, Workday, etc.). When fetching the listing, look for this external URL in the page content and use it as the canonical URL. **Exception:** "Easy Apply" listings have no external link (the application stays on LinkedIn). For Easy Apply jobs, use fingerprint fallback (`company::title::location`).
- **BuiltIn:** Fetch the listing and look for the "Apply Now" or external apply link/redirect URL in the page HTML. BuiltIn often includes the Greenhouse/Lever URL in the page source. If found, use as canonical.
- **SimplyHired:** Same as BuiltIn — look for external apply destination in page HTML.
- **Greenhouse/Lever/Ashby/Workday (direct from site: search):** These ARE already canonical — use the URL as-is.

**Note:** Many ATS embeds (Ashby, some Lever) render via JavaScript and won't appear in static HTML fetches. When canonical resolution fails, always fall through to fingerprint rather than logging the aggregator URL as "canonical".

**Resolution priority (attempt in order, stop at first success):**

1. **Canonical URL** — extract the ATS/careers page link as described above. Fetch it to verify it's live. Check against `dedup_index.txt` → skip if seen.
   - **If fetching the canonical URL returns a 404, a redirect to a general jobs listing page, or does not contain the specific job — treat the posting as closed and skip it. Do not work around this by fetching cached data from third-party sites.**
2. **Fingerprint fallback** — if no external apply link exists or canonical fetch fails, construct `company::title::location` (lowercase, trimmed). Check against `dedup_index.txt` → skip if seen. Log: `[WARN] Canonical resolution failed for [URL] — using fingerprint`
3. **Job board URL fallback** — if fingerprint cannot be constructed, use the job board URL. Check against `dedup_index.txt` → skip if seen. Log: `[WARN] Fingerprint unavailable for [URL] — using job board URL as identifier`

**Important:** The canonical URL (or fingerprint) is what goes in `dedup_index.txt`. This prevents evaluating the same job twice when it appears on multiple boards. When recording in `reviewed_jobs.txt`, use the dedup method that actually succeeded:
- `canonical` — if the ATS URL was found and verified
- `fingerprint` — if using `company::title::location` fallback
- `jobboard` — only if neither canonical nor fingerprint was possible

Do NOT log a job board aggregator URL (LinkedIn, BuiltIn, SimplyHired) as "canonical" — that defeats the purpose of dedup. If you couldn't resolve the ATS URL, use fingerprint.

Do not write to `reviewed_jobs.txt` or `dedup_index.txt` yet — wait until after evaluation.

### Step 4: First-Pass Filter (fast, no full JD read)
Fetch enough of the page to extract title, location/remote policy, salary, and seniority signals. Apply rules from `eval/first_pass_rules.md`:
- Wrong title → reject (see `eval/title_filter.md`)
- Wrong location / no remote → reject
- Salary listed and below floor → reject (use tiered compensation logic)
- Wrong seniority (intern, junior, VP, director) → reject

**Location interpretation:** A city/state in the location header (e.g. "San Francisco, CA" or "Wellington, FL") is often the company's registered HQ address — it does NOT mean the role is onsite. Only reject for location if the job description body explicitly states onsite work is required (e.g. "must work in office", "hybrid 3 days/week", "in-person required", "not remote"). For listings sourced from LinkedIn with `f_WT=2` (remote work type filter) or BuiltIn/SimplyHired remote-filtered URLs: treat location as unconfirmed-but-likely-remote, not onsite, unless the body contradicts it.

**Fetch efficiency:** Extract only the 4 signals needed (title, location, salary, seniority). Do not return or store company descriptions, about sections, benefits, perks, or responsibilities at this stage.

Append entry to `reviewed_jobs.txt` and `dedup_index.txt` immediately after each job (pass or fail). Log rejections with reason.

### Step 5: Deep Fit Evaluation (full JD read)
Fetch the complete job description (use canonical URL if resolved). Evaluate using `eval/deep_eval_rubric.md` and `eval/candidate_skills.md`.

**Fetch efficiency:** Extract and return only: required qualifications, preferred qualifications, key responsibilities, salary, location, and seniority. Explicitly exclude: company/about sections, benefits and perks, diversity and inclusion statements, mission/values, and any boilerplate not directly describing role requirements. These sections add no signal for fit evaluation.

**A. Hard Requirements Check (binary gate)** — go through every listed requirement, matching against `eval/candidate_skills.md`. If any is clearly not met → reject.

**B. Fit Score (0–100)** — per scoring guide in `eval/deep_eval_rubric.md`. Weight toward must-have skills.

**C. Red Flag Check** — note: no salary range, vague requirements, culture fit concerns, misclassified role.

Only proceed if all hard requirements are met **and** fit score ≥ 75%.

### Step 6: Write Result File
Write `results/YYYY-MM-DD_CompanyName_JobTitle.md` using the template in `eval/deep_eval_rubric.md`.

### Step 7: Write Run Summary
Append to `logs/YYYY-MM-DD_run.log`:
- Queries executed, raw candidates found, skipped (already reviewed)
- Canonical / fingerprint / job board URL counts
- First-pass rejections by reason
- Deep pass results (failed hard requirements, below fit threshold, passed)
- Result files written, new entries added to `reviewed_jobs.txt`
