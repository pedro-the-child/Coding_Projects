"""
Stripe Subscriptions Upsell — Empirical Holdout Conversion Analysis
- Observation window: 2041-05-01 to 2041-11-30 (7 months)
- Conversion window:  2041-12-01 to 2042-06-22 (7 months)
All heavy lifting is done in DuckDB SQL.
Python is used only to run queries and write CSV outputs.
"""

import duckdb

con = duckdb.connect()

# ── 0. Register CSVs as views ──────────────────────────────────────────────────
con.execute("""
    CREATE OR REPLACE VIEW merchants AS
        SELECT * FROM read_csv_auto('merchants.csv');

    CREATE OR REPLACE VIEW payments AS
        SELECT * FROM read_csv_auto('payments.csv.csv');
""")

# ── 1. SEGMENT CONVERSION RATES ───────────────────────────────────────────────
# For each attribute, compute:
#   - n: merchants in segment (non-sub users during obs window)
#   - converters: how many adopted Subscriptions in the conversion window
#   - conversion_rate

con.execute("""
-- Base: all merchants with zero subscription volume in the observation window
-- Step 1: daily aggregates per merchant in observation window
CREATE OR REPLACE VIEW obs_daily AS
    SELECT merchant,
           date::DATE                          AS txn_date,
           SUM(subscription_volume)            AS sub_vol,
           SUM(checkout_volume)                AS checkout_vol,
           SUM(payment_link_volume)            AS paylink_vol,
           SUM(total_volume)                   AS total_vol
    FROM payments
    WHERE date::DATE BETWEEN '2041-05-01' AND '2041-11-30'
    GROUP BY merchant, txn_date;

-- Step 2: monthly rollup per merchant (clean base for CV)
CREATE OR REPLACE VIEW obs_monthly AS
    SELECT merchant,
           DATE_TRUNC('month', txn_date)       AS month,
           SUM(total_vol)                      AS monthly_vol
    FROM obs_daily
    GROUP BY merchant, month;

-- Step 3: per-merchant aggregates — daily stats + CV from monthly rollup
-- Exclude merchants with zero checkout AND zero paylink across the entire dataset
-- (both observation and conversion windows) — these have no behavioral signal at all.
CREATE OR REPLACE VIEW obs_non_sub AS
    WITH daily_agg AS (
        SELECT merchant,
               SUM(sub_vol)                            AS obs_sub_vol,
               SUM(checkout_vol)                       AS obs_checkout_vol,
               SUM(paylink_vol)                        AS obs_paylink_vol,
               SUM(total_vol)                          AS obs_total_vol,
               COUNT(DISTINCT txn_date)                AS active_days
        FROM obs_daily
        GROUP BY merchant
    ),
    monthly_agg AS (
        SELECT merchant,
               COUNT(*)                                AS active_months,
               STDDEV(monthly_vol)                     AS monthly_stddev,
               AVG(monthly_vol)                        AS monthly_avg
        FROM obs_monthly
        GROUP BY merchant
    ),
    -- merchants with any payment volume anywhere in the full dataset
    nonzero_vol_merchants AS (
        SELECT DISTINCT merchant
        FROM payments
        WHERE total_volume > 0
    )
    SELECT d.merchant,
           d.obs_sub_vol,
           d.obs_checkout_vol,
           d.obs_paylink_vol,
           d.obs_total_vol,
           d.active_days,
           m.active_months,
           m.monthly_stddev,
           m.monthly_avg
    FROM daily_agg d
    JOIN monthly_agg m USING (merchant)
    JOIN nonzero_vol_merchants n USING (merchant)
    WHERE d.obs_sub_vol = 0;

-- Converters: merchants who had subscription_volume > 0 in the conversion window
CREATE OR REPLACE VIEW converters AS
    SELECT DISTINCT merchant
    FROM payments
    WHERE date::DATE BETWEEN '2041-12-01' AND '2042-06-22'
      AND subscription_volume > 0;

-- Master table: obs attributes + merchant metadata + conversion flag
CREATE OR REPLACE VIEW master AS
    SELECT
        o.merchant,
        m.industry,
        m.business_size,
        m.country,
        m.first_charge_date,
        -- volumes in dollars
        o.obs_checkout_vol  / 100.0  AS checkout_usd,
        o.obs_paylink_vol   / 100.0  AS paylink_usd,
        (o.obs_checkout_vol + o.obs_paylink_vol) / 100.0 AS combined_vol_usd,
        -- unattributed = direct API volume (floor at 0 to handle double-attribution rows)
        GREATEST(o.obs_total_vol - o.obs_checkout_vol - o.obs_paylink_vol, 0) / 100.0 AS unattributed_vol_usd,
        -- dominant payment method: whichever of checkout, paylink, unattributed is largest
        CASE
            WHEN GREATEST(o.obs_checkout_vol, o.obs_paylink_vol, GREATEST(o.obs_total_vol - o.obs_checkout_vol - o.obs_paylink_vol, 0)) = o.obs_checkout_vol
                AND o.obs_checkout_vol > 0                          THEN 'checkout'
            WHEN GREATEST(o.obs_checkout_vol, o.obs_paylink_vol, GREATEST(o.obs_total_vol - o.obs_checkout_vol - o.obs_paylink_vol, 0)) = o.obs_paylink_vol
                AND o.obs_paylink_vol > 0                           THEN 'paylink'
            WHEN GREATEST(o.obs_total_vol - o.obs_checkout_vol - o.obs_paylink_vol, 0) > 0 THEN 'unattributed'
            ELSE 'no_volume'
        END AS dominant_method,
        -- paylink share of combined volume (NULL if no combined volume)
        CASE WHEN (o.obs_checkout_vol + o.obs_paylink_vol) > 0
             THEN ROUND(o.obs_paylink_vol::DOUBLE / (o.obs_checkout_vol + o.obs_paylink_vol), 3)
             ELSE NULL END AS paylink_mix,
        o.obs_total_vol     / 100.0  AS total_usd,
        -- active day ratio (obs window = 335 days)
        ROUND(o.active_days / 214.0, 3)                     AS active_day_ratio,
        -- coefficient of variation (0 if avg is 0)
        CASE WHEN o.monthly_avg > 0
             THEN ROUND(o.monthly_stddev / o.monthly_avg, 3)
             ELSE NULL END                                   AS revenue_cv,
        -- tenure at start of obs window (months)
        CASE
            WHEN m.first_charge_date = '0' OR m.first_charge_date IS NULL THEN NULL
            ELSE ROUND(DATEDIFF('day',
                    TRY_CAST(m.first_charge_date AS TIMESTAMPTZ),
                    TIMESTAMPTZ '2041-05-01 00:00:00+00') / 30.44, 1)
        END                                                  AS tenure_months,
        -- conversion flag
        CASE WHEN c.merchant IS NOT NULL THEN 1 ELSE 0 END  AS converted
    FROM obs_non_sub o
    JOIN merchants m USING (merchant)
    LEFT JOIN converters c USING (merchant);
""")

# ── 2. SEGMENT ANALYSIS ───────────────────────────────────────────────────────
segment_queries = {

    "industry": """
        SELECT
            'industry'          AS attribute,
            industry            AS segment,
            COUNT(*)            AS n,
            SUM(converted)      AS converters,
            ROUND(100.0 * SUM(converted) / COUNT(*), 2) AS conversion_rate_pct,
            ROUND(100.0 * (SUM(converted) / COUNT(*) - 1.96 * SQRT(SUM(converted) / COUNT(*) * (1 - SUM(converted) / COUNT(*)) / COUNT(*))), 2) AS ci_lower_pct,
            ROUND(100.0 * (SUM(converted) / COUNT(*) + 1.96 * SQRT(SUM(converted) / COUNT(*) * (1 - SUM(converted) / COUNT(*)) / COUNT(*))), 2) AS ci_upper_pct
        FROM master
        GROUP BY industry
        HAVING n >= 30
        ORDER BY conversion_rate_pct DESC
    """,

    "business_size": """
        SELECT
            'business_size'     AS attribute,
            business_size       AS segment,
            COUNT(*)            AS n,
            SUM(converted)      AS converters,
            ROUND(100.0 * SUM(converted) / COUNT(*), 2) AS conversion_rate_pct,
            ROUND(100.0 * (SUM(converted) / COUNT(*) - 1.96 * SQRT(SUM(converted) / COUNT(*) * (1 - SUM(converted) / COUNT(*)) / COUNT(*))), 2) AS ci_lower_pct,
            ROUND(100.0 * (SUM(converted) / COUNT(*) + 1.96 * SQRT(SUM(converted) / COUNT(*) * (1 - SUM(converted) / COUNT(*)) / COUNT(*))), 2) AS ci_upper_pct
        FROM master
        GROUP BY business_size
        HAVING n >= 30
        ORDER BY conversion_rate_pct DESC
    """,

    "country": """
        SELECT
            'country'           AS attribute,
            country             AS segment,
            COUNT(*)            AS n,
            SUM(converted)      AS converters,
            ROUND(100.0 * SUM(converted) / COUNT(*), 2) AS conversion_rate_pct,
            ROUND(100.0 * (SUM(converted) / COUNT(*) - 1.96 * SQRT(SUM(converted) / COUNT(*) * (1 - SUM(converted) / COUNT(*)) / COUNT(*))), 2) AS ci_lower_pct,
            ROUND(100.0 * (SUM(converted) / COUNT(*) + 1.96 * SQRT(SUM(converted) / COUNT(*) * (1 - SUM(converted) / COUNT(*)) / COUNT(*))), 2) AS ci_upper_pct
        FROM master
        GROUP BY country
        HAVING n >= 30
        ORDER BY conversion_rate_pct DESC
    """,

    "total_vol_quartile": """
        SELECT
            'total_vol_quartile' AS attribute,
            'Q' || CAST(q AS VARCHAR) AS segment,
            COUNT(*)            AS n,
            SUM(converted)      AS converters,
            ROUND(100.0 * SUM(converted) / COUNT(*), 2) AS conversion_rate_pct,
            ROUND(100.0 * (SUM(converted) / COUNT(*) - 1.96 * SQRT(SUM(converted) / COUNT(*) * (1 - SUM(converted) / COUNT(*)) / COUNT(*))), 2) AS ci_lower_pct,
            ROUND(100.0 * (SUM(converted) / COUNT(*) + 1.96 * SQRT(SUM(converted) / COUNT(*) * (1 - SUM(converted) / COUNT(*)) / COUNT(*))), 2) AS ci_upper_pct
        FROM (
            SELECT converted, NTILE(4) OVER (ORDER BY total_usd) AS q FROM master
        )
        GROUP BY q
        HAVING n >= 30
        ORDER BY segment
    """,

    "dominant_method": """
        SELECT
            'dominant_method'   AS attribute,
            dominant_method     AS segment,
            COUNT(*)            AS n,
            SUM(converted)      AS converters,
            ROUND(100.0 * SUM(converted) / COUNT(*), 2) AS conversion_rate_pct,
            ROUND(100.0 * (SUM(converted) / COUNT(*) - 1.96 * SQRT(SUM(converted) / COUNT(*) * (1 - SUM(converted) / COUNT(*)) / COUNT(*))), 2) AS ci_lower_pct,
            ROUND(100.0 * (SUM(converted) / COUNT(*) + 1.96 * SQRT(SUM(converted) / COUNT(*) * (1 - SUM(converted) / COUNT(*)) / COUNT(*))), 2) AS ci_upper_pct
        FROM master
        GROUP BY dominant_method
        HAVING n >= 30
        ORDER BY conversion_rate_pct DESC
    """,

    "paylink_mix": """
        SELECT
            'paylink_mix'       AS attribute,
            CASE
                WHEN paylink_mix IS NULL  THEN 'no_combined_vol'
                WHEN paylink_mix < 0.30   THEN '1_checkout_dominant (>70% checkout)'
                WHEN paylink_mix < 0.70   THEN '2_mixed (30-70% each)'
                ELSE                           '3_paylink_dominant (>70% paylink)'
            END                 AS segment,
            COUNT(*)            AS n,
            SUM(converted)      AS converters,
            ROUND(100.0 * SUM(converted) / COUNT(*), 2) AS conversion_rate_pct,
            ROUND(100.0 * (SUM(converted) / COUNT(*) - 1.96 * SQRT(SUM(converted) / COUNT(*) * (1 - SUM(converted) / COUNT(*)) / COUNT(*))), 2) AS ci_lower_pct,
            ROUND(100.0 * (SUM(converted) / COUNT(*) + 1.96 * SQRT(SUM(converted) / COUNT(*) * (1 - SUM(converted) / COUNT(*)) / COUNT(*))), 2) AS ci_upper_pct
        FROM master
        GROUP BY segment
        HAVING n >= 30
        ORDER BY segment
    """,

    "active_day_ratio": """
        SELECT
            'active_day_ratio'  AS attribute,
            CASE
                WHEN active_day_ratio < 0.25 THEN '1_low (<25%)'
                WHEN active_day_ratio < 0.60 THEN '2_medium (25-60%)'
                ELSE                               '3_high (60%+)'
            END                 AS segment,
            COUNT(*)            AS n,
            SUM(converted)      AS converters,
            ROUND(100.0 * SUM(converted) / COUNT(*), 2) AS conversion_rate_pct,
            ROUND(100.0 * (SUM(converted) / COUNT(*) - 1.96 * SQRT(SUM(converted) / COUNT(*) * (1 - SUM(converted) / COUNT(*)) / COUNT(*))), 2) AS ci_lower_pct,
            ROUND(100.0 * (SUM(converted) / COUNT(*) + 1.96 * SQRT(SUM(converted) / COUNT(*) * (1 - SUM(converted) / COUNT(*)) / COUNT(*))), 2) AS ci_upper_pct
        FROM master
        GROUP BY segment
        HAVING n >= 30
        ORDER BY segment
    """,

    "revenue_cv": """
        SELECT
            'revenue_cv'        AS attribute,
            CASE
                WHEN revenue_cv IS NULL        THEN 'no_activity'
                WHEN revenue_cv < 0.5          THEN '1_low_variance (<0.5)'
                WHEN revenue_cv < 1.0          THEN '2_medium_variance (0.5-1.0)'
                ELSE                                '3_high_variance (1.0+)'
            END                 AS segment,
            COUNT(*)            AS n,
            SUM(converted)      AS converters,
            ROUND(100.0 * SUM(converted) / COUNT(*), 2) AS conversion_rate_pct,
            ROUND(100.0 * (SUM(converted) / COUNT(*) - 1.96 * SQRT(SUM(converted) / COUNT(*) * (1 - SUM(converted) / COUNT(*)) / COUNT(*))), 2) AS ci_lower_pct,
            ROUND(100.0 * (SUM(converted) / COUNT(*) + 1.96 * SQRT(SUM(converted) / COUNT(*) * (1 - SUM(converted) / COUNT(*)) / COUNT(*))), 2) AS ci_upper_pct
        FROM master
        GROUP BY segment
        HAVING n >= 30
        ORDER BY segment
    """,

    "tenure": """
        SELECT
            'tenure'            AS attribute,
            CASE
                WHEN tenure_months IS NULL  THEN 'unknown'
                WHEN tenure_months < 6      THEN '1_new (<6mo)'
                WHEN tenure_months < 12     THEN '2_mid (6-12mo)'
                ELSE                             '3_mature (12mo+)'
            END                 AS segment,
            COUNT(*)            AS n,
            SUM(converted)      AS converters,
            ROUND(100.0 * SUM(converted) / COUNT(*), 2) AS conversion_rate_pct,
            ROUND(100.0 * (SUM(converted) / COUNT(*) - 1.96 * SQRT(SUM(converted) / COUNT(*) * (1 - SUM(converted) / COUNT(*)) / COUNT(*))), 2) AS ci_lower_pct,
            ROUND(100.0 * (SUM(converted) / COUNT(*) + 1.96 * SQRT(SUM(converted) / COUNT(*) * (1 - SUM(converted) / COUNT(*)) / COUNT(*))), 2) AS ci_upper_pct
        FROM master
        GROUP BY segment
        HAVING n >= 30
        ORDER BY segment
    """,
}

print("=" * 65)
print("SEGMENT CONVERSION RATES")
print("Baseline: overall conversion rate among non-sub merchants")
print("=" * 65)

baseline = con.execute("""
    SELECT COUNT(*) AS n, SUM(converted) AS converters,
           ROUND(100.0 * SUM(converted) / COUNT(*), 2) AS conversion_rate_pct
    FROM master
""").fetchdf()
print(baseline.to_string(index=False))
print()

all_segments = []
for name, q in segment_queries.items():
    df = con.execute(q).fetchdf()
    print(f"--- {name} ---")
    print(df.to_string(index=False))
    print()
    all_segments.append(df)

# Export full segment table
import pandas as pd
seg_df = pd.concat(all_segments, ignore_index=True)
seg_df.to_csv("segment_conversion_rates.csv", index=False)
print("Exported segment_conversion_rates.csv")

# ── 3. BUILD SCORED TARGETS ───────────────────────────────────────────────────
# Scoring uses empirically observed conversion rates as weights.
# Each dimension's score = (segment_conversion_rate / baseline_rate) — relative lift.
# Final score = average relative lift across dimensions, scaled 0-100.

print("\n" + "=" * 65)
print("BUILDING SCORED TARGETS")
print("=" * 65)

con.execute("""
CREATE OR REPLACE VIEW targets_scored AS
WITH
-- Bayesian shrinkage constant: k=100
-- adjusted_rate = (n * raw_rate + k * baseline_rate) / (n + k)
-- Pulls small segments toward baseline; large segments barely affected.

-- baseline
baseline AS (
    SELECT ROUND(100.0 * SUM(converted) / COUNT(*), 4) AS rate FROM master
),
-- industry
industry_lift AS (
    SELECT industry AS segment, COUNT(*) AS n,
           ROUND(100.0 * SUM(converted) / COUNT(*), 4) AS raw_rate
    FROM master GROUP BY industry HAVING COUNT(*) >= 30
),
-- country
country_lift AS (
    SELECT country AS segment, COUNT(*) AS n,
           ROUND(100.0 * SUM(converted) / COUNT(*), 4) AS raw_rate
    FROM master GROUP BY country HAVING COUNT(*) >= 30
),
-- dominant method
dom_lift AS (
    SELECT dominant_method AS bucket, COUNT(*) AS n,
           ROUND(100.0 * SUM(converted) / COUNT(*), 4) AS raw_rate
    FROM master GROUP BY bucket HAVING COUNT(*) >= 30
),
-- Join lifts; apply Bayesian shrinkage (k=100) and compute relative lift vs baseline
scored AS (
    SELECT
        m.merchant,
        m.industry,
        m.business_size,
        m.country,
        m.dominant_method,
        ROUND(m.checkout_usd, 2)     AS checkout_usd,
        ROUND(m.paylink_usd, 2)      AS paylink_usd,
        ROUND(m.total_usd, 2)        AS total_usd,
        m.tenure_months,
        m.converted,
        ROUND((COALESCE(il.n,0) * COALESCE(il.raw_rate, b.rate) + 100 * b.rate) / (COALESCE(il.n,0) + 100) / b.rate, 4) AS lift_industry,
        ROUND((COALESCE(cl.n,0) * COALESCE(cl.raw_rate, b.rate) + 100 * b.rate) / (COALESCE(cl.n,0) + 100) / b.rate, 4) AS lift_country,
        ROUND((COALESCE(dl.n,0) * COALESCE(dl.raw_rate, b.rate) + 100 * b.rate) / (COALESCE(dl.n,0) + 100) / b.rate, 4) AS lift_dominant_method
    FROM master m
    CROSS JOIN baseline b
    LEFT JOIN industry_lift il ON m.industry       = il.segment
    LEFT JOIN country_lift cl  ON m.country        = cl.segment
    LEFT JOIN dom_lift dl      ON m.dominant_method = dl.bucket
)
SELECT *,
    ROUND(
        100.0 * (lift_industry + lift_country + lift_dominant_method) / 3.0
    , 1) AS score
FROM scored
ORDER BY score DESC
""")

# Preview
print(con.execute("""
    SELECT rank, merchant, industry, country, dominant_method,
           checkout_usd, paylink_usd, total_usd, lift_industry, lift_country, lift_dominant_method, score
    FROM (SELECT ROW_NUMBER() OVER (ORDER BY score DESC) AS rank, * FROM targets_scored)
    LIMIT 20
""").fetchdf().to_string(index=False))

print("\nExported targets.csv")

# ── 4. SCORE SUMMARY — 2×2 MATRIX (propensity × volume) ──────────────────────
# Tiers:
#   Tier 1  High-touch   : top 10% volume AND score ≥ 150
#   Tier 2a High-intent  : score ≥ 150, NOT top 10% volume
#   Tier 2b High-value   : top 10% volume, score < 150
#   Tier 3  Self-serve   : everything else
print("\n" + "=" * 65)
print("SCORE DISTRIBUTION — 2×2 Propensity × Volume Tiers")
print("=" * 65)
print(con.execute("""
WITH vol_cutoff AS (
    SELECT PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY total_usd) AS p90
    FROM targets_scored
),
tiered AS (
    SELECT *,
        CASE
            WHEN total_usd >= (SELECT p90 FROM vol_cutoff) AND score >= 150
                THEN 'Tier 1: High-touch   (top 10% vol + score>=150)'
            WHEN score >= 150
                THEN 'Tier 2a: High-intent  (score>=150, <top 10% vol)'
            WHEN total_usd >= (SELECT p90 FROM vol_cutoff)
                THEN 'Tier 2b: High-value   (top 10% vol, score<150)'
            ELSE
                'Tier 3: Self-serve   (below both thresholds)'
        END AS tier
    FROM targets_scored
)
SELECT tier,
       COUNT(*)                        AS merchants,
       ROUND(AVG(score), 1)            AS avg_score,
       ROUND(AVG(total_usd), 0)        AS avg_vol_usd,
       ROUND(MIN(total_usd), 0)        AS min_vol_usd
FROM tiered
GROUP BY tier
ORDER BY tier
""").fetchdf().to_string(index=False))

# Re-export targets.csv with tier column
con.execute("""
    COPY (
        WITH vol_cutoff AS (
            SELECT PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY total_usd) AS p90
            FROM targets_scored
        )
        SELECT
            ROW_NUMBER() OVER (ORDER BY score DESC) AS rank,
            CASE
                WHEN total_usd >= (SELECT p90 FROM vol_cutoff) AND score >= 150
                    THEN 'Tier 1: High-touch'
                WHEN score >= 150
                    THEN 'Tier 2a: High-intent'
                WHEN total_usd >= (SELECT p90 FROM vol_cutoff)
                    THEN 'Tier 2b: High-value'
                ELSE
                    'Tier 3: Self-serve'
            END AS tier,
            *
        FROM targets_scored
        ORDER BY score DESC
    )
    TO 'targets.csv' (HEADER, DELIMITER ',')
""")
print("\nRe-exported targets.csv with tier column")
