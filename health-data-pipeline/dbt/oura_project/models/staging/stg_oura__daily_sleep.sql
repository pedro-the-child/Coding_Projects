with source as (
    select * from {{ source('oura_raw', 'daily_sleep') }}
),

renamed as (
    select
        id,
        cast(day as date) as sleep_date,
        score as sleep_score,
        contributors__deep_sleep   as contributor_deep_sleep,
        contributors__efficiency   as contributor_efficiency,
        contributors__latency      as contributor_latency,
        contributors__rem_sleep    as contributor_rem_sleep,
        contributors__restfulness  as contributor_restfulness,
        contributors__timing       as contributor_timing,
        contributors__total_sleep  as contributor_total_sleep,
        timestamp as sleep_timestamp
    from source
)

select * from renamed
