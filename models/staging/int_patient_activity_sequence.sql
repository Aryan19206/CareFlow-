{{ config(materialized='view') }}

WITH patient_events AS (
    SELECT
        case_id,
        event_id,
        activity,
        event_timestamp,
        department,
        resource,

        LAG(activity) OVER (
            PARTITION BY case_id
            ORDER BY event_timestamp, event_id
        ) AS previous_activity,

        LAG(event_timestamp) OVER (
            PARTITION BY case_id
            ORDER BY event_timestamp, event_id
        ) AS previous_timestamp

    FROM {{ ref('stg_event_logs') }}
)

SELECT
    case_id,
    event_id,
    previous_activity,
    activity,
    previous_timestamp,
    event_timestamp,

    TIMESTAMP_DIFF(
        event_timestamp,
        previous_timestamp,
        MINUTE
    ) AS minutes_since_previous_activity,

    department,
    resource

FROM patient_events