{{ config(materialized='view') }} -- Configures this dbt model to be created as a SQL view.

WITH source AS (
    SELECT * FROM {{ source('raw', 'support_interactions') }} -- Selects all columns from the 'support_interactions' table in the 'raw' schema.
),
cleaned AS (
    SELECT
        interaction_id,
        customer_id,
        interaction_date::DATE AS interaction_date, -- Casts 'interaction_date' to a DATE type.
        TRIM(UPPER(interaction_type)) AS interaction_type, -- Cleans and standardizes 'interaction_type'.
        TRIM(UPPER(category)) AS category, -- Cleans and standardizes 'category'.
        TRIM(UPPER(priority)) AS priority, -- Cleans and standardizes 'priority'.
        resolution_time_hours,
        satisfaction_score,
        resolved::BOOLEAN AS resolved, -- Casts 'resolved' to a BOOLEAN type.
        -- Business logic: Categorizes resolution speed based on 'resolution_time_hours'.
        CASE 
            WHEN resolution_time_hours <= 2 THEN 'FAST' -- Interactions resolved very quickly.
            WHEN resolution_time_hours <= 8 THEN 'NORMAL' -- Interactions resolved within standard business hours.
            WHEN resolution_time_hours <= 24 THEN 'SLOW' -- Interactions taking a full day to resolve.
            ELSE 'VERY_SLOW' -- Interactions with significantly delayed resolution.
        END AS resolution_speed,
        -- Business logic: Categorizes satisfaction based on 'satisfaction_score'.
        CASE 
            WHEN satisfaction_score >= 4 THEN 'SATISFIED' -- High satisfaction scores.
            WHEN satisfaction_score >= 3 THEN 'NEUTRAL' -- Moderate satisfaction.
            ELSE 'DISSATISFIED' -- Low satisfaction scores, indicating potential issues.
        END AS satisfaction_category
    FROM source
    WHERE interaction_id IS NOT NULL -- Filters out records with null interaction IDs.
      AND customer_id IS NOT NULL -- Filters out records with null customer IDs.
      AND interaction_date IS NOT NULL -- Filters out records with null interaction dates.
)
SELECT * FROM cleaned -- Selects all columns from the cleaned CTE.