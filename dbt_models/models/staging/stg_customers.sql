{{ config(materialized='view') }}

WITH source AS (
    SELECT * FROM {{ source('raw', 'customers') }}
),

cleaned AS (
    SELECT
        customer_id,
        company_name,
        TRIM(UPPER(industry)) AS industry,
        TRIM(UPPER(company_size)) AS company_size,
        TRIM(UPPER(country)) AS country,
        TRIM(UPPER(state)) AS state,
        email,
        first_name,
        last_name,
        phone,
        signup_date::DATE AS signup_date,
        created_at::TIMESTAMP AS created_at,
        updated_at::TIMESTAMP AS updated_at,
        -- Data quality flags
        CASE 
            WHEN email IS NULL OR email = '' THEN TRUE 
            ELSE FALSE 
        END AS is_missing_email,
        CASE 
            WHEN country IS NULL OR country = '' THEN TRUE 
            ELSE FALSE 
        END AS is_missing_country
    FROM source
    WHERE customer_id IS NOT NULL
      AND signup_date IS NOT NULL
)

SELECT * FROM cleaned