with source as (
    select * from {{ source('oura_raw', 'daily_activity') }}
),

renamed as (
    select
        id,
        cast(day as date)       as activity_date,
        score                   as activity_score,
        active_calories,
        total_calories,
        steps,
        equivalent_walking_distance,
        high_activity_time,
        medium_activity_time,
        low_activity_time,
        sedentary_time,
        resting_time,
        target_calories,
        target_meters,
        contributors__meet_daily_targets as contributor_meet_daily_targets,
        contributors__move_every_hour    as contributor_move_every_hour,
        contributors__recovery_time      as contributor_recovery_time,
        contributors__stay_active        as contributor_stay_active,
        contributors__training_frequency as contributor_training_frequency,
        contributors__training_volume    as contributor_training_volume
    from source
)

select * from renamed
