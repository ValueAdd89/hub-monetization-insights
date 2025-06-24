{{ config(materialized='view') }} -- Configures this dbt model to be created as a SQL view.

WITH source AS (
SELECT * FROM {{ source('raw', 'subscriptions') }} -- Selects all columns from the 'subscriptions' table in the 'raw' schema.
),

cleaned AS (
SELECT
 subscription_id,
 customer_id,
 TRIM(LOWER(product_hub)) AS hub, -- Cleans and standardizes 'product_hub' (removes whitespace, converts to lowercase).
 TRIM(LOWER(subscription_tier)) AS tier, -- Cleans and standardizes 'subscription_tier'.
 monthly_revenue,
 subscription_start_date::DATE AS subscription_start_date, -- Casts 'subscription_start_date' to DATE.
 subscription_end_date::DATE AS subscription_end_date, -- Casts 'subscription_end_date' to DATE.
 is_active::BOOLEAN AS is_active, -- Casts 'is_active' to a BOOLEAN type.
 TRIM(LOWER(payment_method)) AS payment_method, -- Cleans and standardizes 'payment_method'.
 created_at::TIMESTAMP AS created_at, -- Casts 'created_at' to TIMESTAMP.
 updated_at::TIMESTAMP AS updated_at, -- Casts 'updated_at' to TIMESTAMP.
 -- Calculated fields: Derived attributes for business logic or data utility.
 CASE
 WHEN subscription_end_date IS NOT NULL AND subscription_end_date <= CURRENT_DATE-- If an end date exists and is in the past or today.
 THEN subscription_end_date-- The effective end date is the actual end date.
 ELSE CURRENT_DATE-- If ongoing or future-dated, the effective end date is considered as today.
 END AS effective_end_date,
 -- Data validation flags: Identify specific data integrity issues that might need attention.
 CASE
 WHEN monthly_revenue <= 0 THEN TRUE-- Flag is TRUE if monthly revenue is non-positive, indicating a potential data error.
 ELSE FALSE
 END AS has_invalid_revenue,
 CASE
 WHEN subscription_end_date < subscription_start_date THEN TRUE-- Flag is TRUE if the end date occurs before the start date.
 ELSE FALSE
 END AS has_invalid_dates
FROM source
WHERE subscription_id IS NOT NULL -- Filters out records with null subscription IDs, ensuring valid subscriptions.
AND customer_id IS NOT NULL -- Filters out records with null customer IDs, ensuring subscriptions are linked to a customer.
AND subscription_start_date IS NOT NULL -- Filters out records with null start dates, which are critical for subscription tracking.
)

SELECT * FROM cleaned -- Selects all columns from the cleaned CTE.