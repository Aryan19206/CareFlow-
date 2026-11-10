
{{ config(materialized='view') }}

SELECT
    CAST(Patient_ID AS STRING) AS case_id,
    CAST(Event_ID AS STRING) AS event_id,
    TRIM(Activity) AS activity,
    Event_Timestamp AS event_timestamp,
    TRIM(Department) AS department,
    TRIM(Resource) AS resource
FROM `careflow-process-mining-512416.careflow_dataset.event_logs_full`
WHERE
    Patient_ID IS NOT NULL
    AND Activity IS NOT NULL
    AND Event_Timestamp IS NOT NULL
