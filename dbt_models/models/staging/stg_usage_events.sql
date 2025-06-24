{{ config(materialized='view') }} -- Configures this dbt model to be created as a SQL view.

WITH source AS (
    SELECT * FROM {{ source('raw', 'usage_events') }} -- Selects all columns from the 'usage_events' table in the 'raw' schema.
),
cleaned AS (
    SELECT
        event_id,
        customer_id,
        subscription_id,
        event_date::DATE AS event_date, -- Casts 'event_date' to a DATE type.
        session_duration_minutes,
        pages_viewed,
        api_calls,
        TRIM(LOWER(feature_used)) AS feature_used, -- Cleans and standardizes 'feature_used'.
        event_timestamp::TIMESTAMP AS event_timestamp, -- Casts 'event_timestamp' to a TIMESTAMP type.
        -- Derived metrics: Calculate new metrics based on raw usage data for deeper insights.
        CASE 
            WHEN session_duration_minutes > 0 THEN pages_viewed / session_duration_minutes  -- Calculates pages viewed per minute of session.
            ELSE 0  -- Avoids division by zero if session duration is 0.
        END AS pages_per_minute,
        CASE 
            WHEN session_duration_minutes > 0 THEN api_calls / session_duration_minutes  -- Calculates API calls per minute of session.
            ELSE 0  -- Avoids division by zero if session duration is 0.
        END AS api_calls_per_minute,
        -- Engagement scoring: Categorizes user engagement based on session duration and pages viewed.
        CASE 
            WHEN session_duration_minutes >= 30 AND pages_viewed >= 10 THEN 'HIGH' -- High engagement tier (e.g., highly active users).
            WHEN session_duration_minutes >= 15 AND pages_viewed >= 5 THEN 'MEDIUM' -- Medium engagement tier.
            WHEN session_duration_minutes >= 5 AND pages_viewed >= 2 THEN 'LOW' -- Low engagement tier.
            ELSE 'MINIMAL' -- Minimal engagement (e.g., passive or inactive users).
        END AS engagement_level
    FROM source
    WHERE event_id IS NOT NULL -- Filters out records with null event IDs.
      AND customer_id IS NOT NULL -- Filters out records with null customer IDs.
      AND event_date IS NOT NULL -- Filters out records with null event dates.
      AND session_duration_minutes >= 0 -- Ensures non-negative session durations for valid calculations.
      AND pages_viewed >= 0 -- Ensures non-negative page views.
      AND api_calls >= 0 -- Ensures non-negative API calls.
)
SELECT * FROM cleaned -- Selects all columns from the cleaned CTE.
