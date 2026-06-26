# Deep Evaluation Rubric

Use this rubric after a job passes first-pass filtering. Read the full JD before scoring.

## Step A: Hard Requirements Check (binary gate)

Go through **every** listed requirement in the JD. For each:
- Map it to the candidate's skills in `eval/candidate_skills.md`
- Mark as MET or NOT MET

If any hard/required qualification is clearly not met -> **REJECT**. Do not proceed to scoring.

Common hard-requirement failure patterns:
- Domain-specific experience stated as required (e.g., "healthcare claims data required", "supply chain experience required")
- Specific tools stated as required that candidate lacks (e.g., "Databricks required", "R required")
- Years of experience significantly above candidate's level (e.g., "10+ years required")

## Step B: Fit Score (0-100)

Score based on alignment between JD requirements and candidate profile.

### Weighting
- **Must-have / required skills:** 60% of score weight
- **Preferred / nice-to-have skills:** 25% of score weight
- **Domain / industry match:** 15% of score weight

### Scoring Guide
| Range | Meaning |
|---|---|
| 90-100 | Near-perfect match -- all required skills met at depth, most preferred met |
| 80-89 | Strong match -- all required met, minor preferred gaps |
| 75-79 | Solid match -- all required met, some preferred gaps, minor domain stretch |
| 70-74 | Borderline -- required met but thin, notable preferred gaps |
| 60-69 | Weak -- some required gaps or significant domain mismatch |
| <60 | Poor fit |

### Threshold
- **Pass:** Score >= 75 AND all hard requirements met
- **Fail:** Score < 75 OR any hard requirement not met

## Step C: Red Flag Check

Note any of the following (do not auto-reject, but document):
- No salary range listed
- Vague or generic requirements suggesting poorly defined role
- Title/seniority mismatch (e.g., "Senior" title but entry-level requirements)
- Culture-fit signals that suggest poor match
- Role scope creep (e.g., analytics title but heavy engineering or management duties)

## Result File Template

For jobs that pass (>= 75% + all hard requirements), write to `results/YYYY-MM-DD_CompanyName_JobTitle.md`:

```markdown
# Company -- Title

## Metadata
- **Date Found:** YYYY-MM-DD
- **Source URL:** [job board URL where the listing was first found, e.g. LinkedIn/BuiltIn]
- **Canonical URL:** [company's own ATS URL, e.g. boards.greenhouse.io/..., jobs.lever.co/..., company.applytojob.com/... — NOT the aggregator URL. If no ATS URL was resolved, state "unresolved" and use source URL]
- **Dedup Method:** canonical|fingerprint|jobboard
- **Salary:** [range or "Not listed"]
- **Location:** [remote status + location details]
- **Seniority:** [level]
- **Company:** [name]
- **Industry:** [sector]

---

## Fit Score: XX / 100

---

## Requirements Met
[Checklist of hard + preferred requirements mapped to candidate skills]

## Requirements Gaps
[List of unmet preferred qualifications or minor gaps]

## Red Flags
[Any concerns noted in Step C]

## Why This Role
[2-3 sentences on why this is a good match]
```
