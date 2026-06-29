with daily_metrics as (
    select * from {{ ref('int_oura__daily_metrics') }}
)

select
    metric_date,

    -- scores
    sleep_score,
    readiness_score,
    activity_score,

    -- sleep composition (converted to minutes)
    round(total_sleep_seconds / 60, 1)  as total_sleep_minutes,
    round(deep_sleep_seconds / 60, 1)   as deep_sleep_minutes,
    round(rem_sleep_seconds / 60, 1)    as rem_sleep_minutes,
    round(light_sleep_seconds / 60, 1)  as light_sleep_minutes,
    sleep_efficiency,
    avg_sleep_latency,

    -- cardiovascular
    avg_hrv,
    sleep_avg_hr,
    sleep_lowest_hr,
    avg_bpm_day,
    min_bpm_day,
    max_bpm_day,
    avg_breath,

    -- recovery signals
    readiness_score                     as overall_recovery,
    temperature_deviation,
    contributor_hrv_balance,
    contributor_resting_heart_rate,
    contributor_recovery_index,

    -- activity
    steps,
    active_calories,
    total_calories,
    round(high_activity_time / 60, 1)   as high_activity_minutes,
    round(medium_activity_time / 60, 1) as medium_activity_minutes,
    round(sedentary_time / 60, 1)       as sedentary_minutes,

    -- score components
    contributor_deep_sleep,
    contributor_rem_sleep,
    contributor_restfulness,
    contributor_timing,
    contributor_total_sleep,
    contributor_sleep_balance,
    contributor_activity_balance,
    contributor_body_temperature

from daily_metrics
order by metric_date desc
