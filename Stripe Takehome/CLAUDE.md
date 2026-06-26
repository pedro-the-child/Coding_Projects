# Stripe Subscriptions Upsell — Project Context

## Goal
Analyze Payments + Merchants CSVs to identify non-Subscription users with high conversion potential for a sales/marketing campaign. Output a ranked merchant list (`targets.csv`) with rationale.

## Data
- `merchants.csv` — merchant metadata: `merchant`, `industry`, `first_charge_date`, `country`, `business_size`
- `payments.csv.csv` — merchant-day volume data: `date`, `merchant`, `subscription_volume`, `checkout_volume`, `payment_link_volume`, `total_volume`
- All volumes are in **cents**
- Product usage is **non-exclusive** (e.g. a transaction can use both Checkout and Subscriptions)
- Dataset covers simulated future period 2041–2042; treat as a real random sample

## Stripe Products Referenced
- **Subscriptions** — APIs for recurring payments and revenue management
- **Checkout** — Stripe-hosted prebuilt checkout page
- **Payment Links** — No-code payment pages

## Target Criteria
Identify merchants that:
1. Are **not** currently using Subscriptions (`subscription_volume = 0`)
2. Have **high Checkout and/or Payment Link volume** (indicates recurring-ready payment flows)
3. Are in **recurring-friendly industries**: SaaS/Software, Education, Digital goods, Business services, Healthcare, Religion/Memberships, Personal services, Consulting, Leisure, Rentals
4. Are **mature merchants** (longer tenure since `first_charge_date`)

## Analytical Approach
Use an **empirical holdout conversion analysis** — not assumed weights:
- **Observation window:** May 2041 → March 2042 (11 months) — characterize merchant behavior
- **Conversion window:** April 2042 → June 2042 (3 months) — measure who adopted Subscriptions
- Segment non-Subscription merchants by key attributes in the observation window
- Compute conversion rate per segment; highest-spread attributes become scoring dimensions
- Flag segments with n < 30 as statistically unreliable

### Attributes to segment on
| Attribute | Bucketing |
|---|---|
| Industry | As-is (categorical) |
| Business size | As-is (small / medium / large) |
| Checkout volume | Quartile buckets (Q1–Q4) |
| Payment Link volume | Quartile buckets (Q1–Q4) |
| Active day ratio | Low / medium / high (<25%, 25–60%, 60%+) |
| Revenue consistency (CV = std/mean of monthly volume) | Low / medium / high variance |
| Tenure at window start | <6mo, 6–12mo, 12mo+ |
| Country | As-is (ISO code) |

## Output
- `targets.csv` — ranked merchant list with `merchant_id`, `industry`, volumes, score components, and total score
- Short memo-style documentation of approach and rationale

## Technical Preferences
- **Use DuckDB SQL as the primary tool** — do the heavy lifting in SQL, not pandas/Python
- Python is acceptable only for orchestration (connecting, running queries, writing CSV)
- Keep scoring logic simple and interpretable (no ML)
- Excel-friendly CSV output

## Interview Context
This is a take-home for a **Business Intelligence / Data Analyst role**. The work should demonstrate:

### Must-show skills (minimum requirements)
- **SQL proficiency** — cohort analysis, window functions, aggregations, CTEs; all heavy lifting in DuckDB SQL
- **Attention to detail** — clean outputs, correct window definitions, handling data quality issues (e.g. null `first_charge_date`)
- **Clear communication** — memo-style rationale, results explainable to a non-technical stakeholder
- **Actionable insights** — output directly informs campaign prioritization, not just descriptive stats

### Nice-to-show skills (preferred qualifications)
- **Statistical awareness** — flag low-n segments, note confidence limitations, don't over-index on noisy rates
- **Python (orchestration only)** — thin wrapper around DuckDB; shows working knowledge without over-engineering
- **Self-service / stakeholder tooling mindset** — CSV output is Excel-friendly; scoring is transparent and auditable by a sales rep
- **Cross-functional thinking** — frame findings in terms of sales/marketing campaign tiers, not just data output
