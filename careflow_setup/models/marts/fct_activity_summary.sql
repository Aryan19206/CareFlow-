{{ config(materialized='table') }}

SELECT
    activity,
    COUNT(*) AS total_events,
    COUNT(DISTINCT case_id) AS unique_patients,
    MIN(event_timestamp) AS first_occurrence,
    MAX(event_timestamp) AS last_occurrence

FROM {{ ref('stg_event_logs') }}

GROUP BY activity
ORDER BY total_events DESC