with source as (
    select * from {{ source('oura_raw', 'daily_readiness') }}
),

renamed as (
    select
        id,
        cast(day as date) as readiness_date,
        score                               as readiness_score,
        temperature_deviation               as temperature_deviation,
        temperature_trend_deviation         as temperature_trend_deviation,
        contributors__activity_balance      as contributor_activity_balance,
        contributors__body_temperature      as contributor_body_temperature,
        contributors__hrv_balance           as contributor_hrv_balance,
        contributors__previous_day_activity as contributor_previous_day_activity,
        contributors__previous_night        as contributor_previous_night,
        contributors__recovery_index        as contributor_recovery_index,
        contributors__resting_heart_rate    as contributor_resting_heart_rate,
        contributors__sleep_balance         as contributor_sleep_balance
    from source
)

select * from renamed
