# Stripe Subscriptions Upsell — Analysis Memo

**To:** Data Science Manager
**From:** Pedro
**Re:** Identifying non-Subscription merchants with high conversion potential

---

## 1. Data Preparation

**Source data:**
- `merchants.csv` — 1 row per merchant with metadata: industry, business size, country, and `first_charge_date`
- `payments.csv` — daily payment volume per merchant across four dimensions: subscription, checkout, payment link, and total volume (all in cents)

**Cleaning steps and data quality notes:**

- **Volume units:** All volume columns are in cents. Converted to USD throughout by dividing by 100.
- **Missing `first_charge_date`:** 26 merchants have `first_charge_date = '0'`, a sentinel value for unknown. These were treated as NULL and excluded from tenure calculations.
- **Double-attribution:** Products are non-exclusive — a transaction can be counted under both Checkout and total volume simultaneously. To avoid negative values when computing unattributed (direct API) volume, I floored at zero: `GREATEST(total_vol - checkout_vol - paylink_vol, 0)`.
- **Merchants with no payment history:** ~3,300 merchants appear in `merchants.csv` but have zero total volume across the entire dataset. These carry no behavioral signal and were excluded from the analysis entirely.
- **Single-month merchants:** 4,193 merchants (24%) had activity in only one calendar month of the observation window. Standard deviation is undefined for a single data point, so their revenue CV is NULL. These are flagged but not excluded — CV was ultimately dropped from the scoring model due to weak predictive signal across all segments.

**Window definitions:**

| Window | Dates | Length | Purpose |
|---|---|---|---|
| Observation | Apr 1, 2041 – Mar 31, 2042 | 12 months | Characterize merchant behavior |
| Conversion | Apr 1, 2042 – Jun 22, 2042 | ~3 months | Measure who adopted Subscriptions |

The dataset begins in April 2041, so the observation window covers the full available history. This maximizes the behavioral signal available for segmentation.

---

## 2. Approach and Rationale

**Method: Empirical holdout conversion analysis**

Rather than assume which merchant attributes predict Subscription adoption, I let the data determine it. The approach:

1. Identify all merchants with zero subscription volume in the observation window — these are the candidates
2. For each candidate, compute behavioral and metadata attributes during the observation window
3. Segment candidates by each attribute and compute the conversion rate per segment in the conversion window
4. Use segments with the highest lift over baseline as scoring dimensions

This approach is self-correcting: it only rewards attributes that empirically correlate with adoption in this dataset, rather than relying on assumed priors. It also produces a fully auditable score — a sales rep can look at any merchant's score and understand exactly which factors drove it.

**Why not a machine learning model?**

With only 170 converters out of 17,360 candidates (0.98% baseline), the dataset is highly imbalanced and the signal is thin. An ML model would require careful calibration, cross-validation, and would produce scores that are difficult to explain to a non-technical sales team. A transparent scoring rubric is more appropriate here.

**Segmentation dimensions evaluated:**

Eight dimensions were evaluated. Only three showed meaningful spread in conversion rates:

| Dimension | Included in Score | Reason |
|---|---|---|
| Industry | ✅ | 2.54% (Personal services) vs. 0.00% (Automotive) — largest spread |
| Country | ✅ | 2.84% (JP) vs. 0.00% (many markets) — strong geographic variation |
| Dominant payment method | ✅ | 2.85% (paylink) vs. 0.78% (checkout) — direct behavioral signal |
| Business size | ❌ | Flat: 0.99% (small) vs. 0.86% (medium) vs. 0.00% (large) |
| Total volume quartile | ❌ | Flat: 0.88%–1.18% across Q1–Q4 |
| Active day ratio | ❌ | Weak/inverse: high-frequency merchants converted at lower rates |
| Revenue CV | ❌ | Flat: ~0.7%–1.2% across all variance buckets |
| Tenure | ❌ | Flat: ~0.84%–1.10% across new/mid/mature |

**Scoring methodology:**

For each of the three retained dimensions, a Bayesian-shrunk relative lift is computed:

```
adjusted_rate  = (n × raw_segment_rate + k × baseline_rate) / (n + k)   [k = 100]
lift           = adjusted_rate / baseline_rate
score          = 100 × mean(lift_industry, lift_country, lift_dominant_method)
```

The shrinkage constant `k = 100` pulls small segments toward the baseline, preventing noisy estimates in thin segments from driving extreme scores. For large segments (n >> 100), shrinkage has negligible effect.

A score of **100** means the merchant's segments convert at exactly the baseline rate. A score of **200** means they convert at 2× baseline on average.

**Dominant payment method — key finding:**

| Method | n | Conversion rate | vs. Baseline |
|---|---|---|---|
| Payment Links | 1,192 | 2.85% | +2.9× |
| Unattributed (direct API) | 14,760 | 0.85% | 0.87× |
| Checkout | 1,408 | 0.78% | 0.80× |

Payment Link merchants convert at nearly 3× the baseline rate. This is the most behaviorally direct signal in the dataset: Payment Links merchants are already using a Stripe-native, no-code product for collecting payments — adopting Subscriptions is a natural extension with minimal implementation lift.

Checkout merchants converting below baseline was a counterintuitive finding. One possible explanation: Checkout merchants may already have a more complex integration and are less likely to change their payment stack during the conversion window. This warrants further investigation.

---

## 3. Results

**Baseline:** 17,360 non-Subscription merchants, 170 converters, **0.98% baseline conversion rate**

**Score distribution:**

| Percentile | Score |
|---|---|
| p25 | 74.6 |
| p50 | 97.6 |
| p75 | 123.3 |
| p90 | 146.8 |
| p95 | 162.1 |
| p99 | 207.5 |
| max | 256.0 |

**Campaign tiers — 2×2 propensity × volume matrix:**

A propensity score alone does not determine how to allocate sales effort. A merchant with a score of 200 and $50 in total volume does not warrant a personal sales call. The final tiers cross conversion propensity with total payment volume:

| Tier | Criteria | Merchants | Avg Score | Avg Volume |
|---|---|---|---|---|
| **Tier 1: High-touch** | Top 10% volume AND score ≥ 150 | 45 | 167 | $514,386 |
| **Tier 2a: High-intent** | Score ≥ 150, below top 10% volume | 1,367 | 176 | $4,680 |
| **Tier 2b: High-value** | Top 10% volume, score < 150 | 1,691 | 97 | $1,611,535 |
| **Tier 3: Self-serve** | Below both thresholds | 14,257 | 95 | $8,376 |

**Recommended campaign approach by tier:**

- **Tier 1 (45 merchants):** Dedicated outreach with a named account rep — these merchants have both the revenue scale to justify personal attention and the behavioral/industry profile indicating high adoption likelihood. Average volume of $514K makes the subscription revenue opportunity meaningful.
- **Tier 2a (1,367 merchants):** Scalable digital campaign — high propensity but smaller accounts. Email sequences, targeted in-product messaging, and case studies from similar merchants. Prioritize within this tier by score.
- **Tier 2b (1,691 merchants):** Nurture campaign — large accounts with weaker conversion signal. Focus on education and removing friction. Worth monitoring; if any shift to a higher-signal product mix (e.g., Payment Links), re-score and escalate.
- **Tier 3 (14,257 merchants):** Self-serve only — in-product prompts, documentation, and Stripe-initiated feature suggestions.

**Top industries among Tier 1 and Tier 2a:**
Personal services, Business services, and Digital goods dominate the high-propensity tiers. These are structurally recurring-revenue businesses that benefit most from Stripe's subscription management features (automated billing, retry logic, proration, customer portal).

---

## 4. Next Steps

**With more time:**

- **Extend the conversion window:** The 3-month window captures early adopters but may miss merchants on longer decision cycles, particularly in enterprise and B2B segments. A 6–12 month window would yield more converters and tighter confidence intervals.
- **Investigate the Checkout anomaly:** Checkout merchants converting below baseline is surprising given their Stripe integration depth. Segmenting further by integration age, transaction frequency, or checkout version may reveal a subgroup with high potential.
- **Add interaction terms:** The model currently treats industry, country, and dominant method as independent. A Personal services merchant in Japan using Payment Links likely has much higher conversion probability than the product of their individual lifts suggests. Testing interaction segments (where n permits) could improve ranking within the high-propensity tiers.
- **Score decay:** Merchant behavior changes. A merchant who switches from direct API to Payment Links mid-year should be re-scored. A monthly refresh of scores would keep the Tier 1 list current.

**With more data:**

- **Transaction-level data:** Product-level volume per transaction (not just daily aggregates) would enable richer behavioral features — average transaction size, transaction frequency distributions, and whether a merchant's business has natural subscription-like payment patterns (same amount, same interval).
- **Support and account data:** Merchants who have contacted support about billing, recurring payments, or invoicing are warm leads. CRM data indicating past outreach attempts or product demos would prevent redundant sales effort.
- **Churn data from existing Subscription users:** Understanding which merchant profiles have the highest retention on Subscriptions would improve targeting — acquiring merchants who will churn quickly is worse than a lower raw conversion rate.
- **Competitor data:** Merchants who recently switched away from a competitor's subscription billing product are high-value targets. This is not available in transactional data but may be available via third-party enrichment.

---

## 5. Metrics Proposal

**Metric 1: Subscription Adoption Rate (SAR) by Campaign Tier**

*Definition:* The percentage of targeted non-Subscription merchants in each tier who process at least one subscription payment within 90 days of first outreach.

*Formula:* `(merchants who adopted Subscriptions within 90 days) / (merchants contacted) × 100`

*Why it matters:* This is the primary success metric — it directly measures whether the campaign is converting the right merchants. Tracking it by tier validates the tiering model: Tier 1 and Tier 2a should significantly outperform Tier 2b and Tier 3. If Tier 2a outperforms Tier 1, it may indicate that the volume threshold for high-touch outreach is too conservative. Comparing SAR against the 0.98% organic baseline quantifies the campaign's incremental lift.

---

**Metric 2: Subscription Volume Ramp (SVR) — 90-Day Post-Adoption**

*Definition:* The median monthly subscription volume (in USD) processed by newly converted merchants in the 90 days following their first subscription payment.

*Formula:* `MEDIAN(monthly subscription volume) over months 1–3 post-adoption, across all converted merchants`

*Why it matters:* Adoption alone is not enough — a merchant who processes one $5 subscription and stops is not a success. SVR measures whether converted merchants are actually building recurring revenue on Stripe. A high SAR with a low SVR suggests we are acquiring merchants who are experimenting rather than committing. Tracking SVR by industry and tier helps identify which merchant profiles are most likely to become sustained Subscription users, informing future campaign prioritization.

---

**Metric 3: Time-to-First-Subscription (TTFS)**

*Definition:* The median number of days between a merchant's first outreach touchpoint and their first subscription payment.

*Formula:* `MEDIAN(date of first subscription payment − date of first outreach contact)`, measured across all merchants who converted within 180 days.

*Why it matters:* TTFS measures sales cycle efficiency and helps right-size the campaign. A short TTFS (< 14 days) in Tier 2a suggests that self-serve digital campaigns are working and minimal human intervention is needed. A long TTFS (> 60 days) in Tier 1 may indicate that merchants need more onboarding support or that the product requires integration work that slows adoption. Tracking TTFS over successive campaign cohorts also measures whether improvements to onboarding, documentation, or sales tooling are shortening the conversion cycle.
