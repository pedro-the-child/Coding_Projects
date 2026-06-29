with source as (
    select * from {{ source('oura_raw', 'heartrate') }}
),

renamed as (
    select
        timestamp                       as hr_timestamp,
        date(timestamp)                 as hr_date,
        bpm,
        source                          as hr_source
    from source
)

select * from renamed
