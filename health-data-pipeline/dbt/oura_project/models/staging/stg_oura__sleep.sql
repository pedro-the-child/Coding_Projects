with source as (
    select * from {{ source('oura_raw', 'sleep') }}
),

renamed as (
    select
        id,
        cast(day as date)           as sleep_date,
        type                        as sleep_type,
        bedtime_start,
        bedtime_end,
        total_sleep_duration,
        time_in_bed,
        awake_time,
        light_sleep_duration,
        deep_sleep_duration,
        rem_sleep_duration,
        restless_periods,
        average_heart_rate,
        lowest_heart_rate,
        average_hrv,
        average_breath,
        latency,
        efficiency
    from source
)

select * from renamed
