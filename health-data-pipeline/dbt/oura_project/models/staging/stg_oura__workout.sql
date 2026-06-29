with source as (
    select * from {{ source('oura_raw', 'workout') }}
),

renamed as (
    select
        id,
        cast(day as date)   as workout_date,
        activity            as workout_type,
        start_datetime,
        end_datetime,
        calories,
        distance,
        intensity,
        source              as workout_source
    from source
)

select * from renamed
