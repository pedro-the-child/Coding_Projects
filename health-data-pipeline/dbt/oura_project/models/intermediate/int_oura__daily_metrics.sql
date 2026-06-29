with sleep as (
    select * from {{ ref('stg_oura__daily_sleep') }}
),

readiness as (
    select * from {{ ref('stg_oura__daily_readiness') }}
),

activity as (
    select * from {{ ref('stg_oura__daily_activity') }}
),

sleep_detail as (
    select
        sleep_date,
        avg(average_heart_rate)  as avg_heart_rate,
        avg(lowest_heart_rate)   as avg_lowest_heart_rate,
        avg(average_hrv)         as avg_hrv,
        avg(average_breath)      as avg_breath,
        sum(total_sleep_duration) as total_sleep_seconds,
        sum(deep_sleep_duration)  as deep_sleep_seconds,
        sum(rem_sleep_duration)   as rem_sleep_seconds,
        sum(light_sleep_duration) as light_sleep_seconds,
        avg(efficiency)           as sleep_efficiency,
        avg(latency)              as avg_sleep_latency
    from {{ ref('stg_oura__sleep') }}
    where sleep_type = 'long_sleep'
    group by 1
),

hr_daily as (
    select
        hr_date,
        avg(bpm)  as avg_bpm_day,
        min(bpm)  as min_bpm_day,
        max(bpm)  as max_bpm_day
    from {{ ref('stg_oura__heartrate') }}
    group by 1
),

spine as (
    select
        coalesce(s.sleep_date, r.readiness_date, a.activity_date) as metric_date
    from sleep s
    full outer join readiness r on s.sleep_date = r.readiness_date
    full outer join activity a  on s.sleep_date = a.activity_date
)

select
    spine.metric_date,

    -- sleep scores
    sleep.sleep_score,
    sleep.contributor_deep_sleep,
    sleep.contributor_efficiency,
    sleep.contributor_rem_sleep,
    sleep.contributor_restfulness,
    sleep.contributor_timing,
    sleep.contributor_total_sleep,

    -- sleep detail
    sd.total_sleep_seconds,
    sd.deep_sleep_seconds,
    sd.rem_sleep_seconds,
    sd.light_sleep_seconds,
    sd.sleep_efficiency,
    sd.avg_sleep_latency,
    sd.avg_hrv,
    sd.avg_breath,
    sd.avg_heart_rate       as sleep_avg_hr,
    sd.avg_lowest_heart_rate as sleep_lowest_hr,

    -- readiness
    readiness.readiness_score,
    readiness.temperature_deviation,
    readiness.contributor_hrv_balance,
    readiness.contributor_resting_heart_rate,
    readiness.contributor_recovery_index,
    readiness.contributor_sleep_balance,
    readiness.contributor_activity_balance,
    readiness.contributor_body_temperature,

    -- activity
    activity.activity_score,
    activity.steps,
    activity.active_calories,
    activity.total_calories,
    activity.high_activity_time,
    activity.medium_activity_time,
    activity.low_activity_time,
    activity.sedentary_time,

    -- heart rate (all-day)
    hr.avg_bpm_day,
    hr.min_bpm_day,
    hr.max_bpm_day

from spine
left join sleep     on spine.metric_date = sleep.sleep_date
left join readiness on spine.metric_date = readiness.readiness_date
left join activity  on spine.metric_date = activity.activity_date
left join sleep_detail sd on spine.metric_date = sd.sleep_date
left join hr_daily hr     on spine.metric_date = hr.hr_date
