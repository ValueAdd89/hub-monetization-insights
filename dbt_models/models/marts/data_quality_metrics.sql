{{ config(materialized='table') }} -- Configures this dbt model to be created as a SQL table for persistence.

WITH source_quality AS (
    SELECT
        'customers' AS table_name, -- Identifies the source table.
        COUNT(*) AS total_records, -- Total records in the table.
        COUNT(DISTINCT customer_id) AS unique_keys, -- Count of unique primary keys.
        COUNT(CASE WHEN email IS NULL OR email = '' THEN 1 END) AS missing_email, -- Count of missing email addresses.
        COUNT(CASE WHEN signup_date IS NULL THEN 1 END) AS missing_signup_date, -- Count of missing signup dates.
        COUNT(CASE WHEN country IS NULL OR country = '' THEN 1 END) AS missing_country -- Count of missing country data.
    FROM {{ ref('stg_customers') }}
    UNION ALL -- Combines data quality metrics from different staging tables into a single result set.
    SELECT
        'subscriptions' AS table_name,
        COUNT(*) AS total_records,
        COUNT(DISTINCT subscription_id) AS unique_keys,
        COUNT(CASE WHEN monthly_revenue <= 0 THEN 1 END) AS invalid_revenue, -- Count of non-positive monthly revenues.
        COUNT(CASE WHEN subscription_end_date < subscription_start_date THEN 1 END) AS invalid_dates, -- Count of subscriptions with end date before start date.
        COUNT(CASE WHEN customer_id IS NULL THEN 1 END) AS missing_customer_id -- Count of subscriptions without a linked customer ID.
    FROM {{ ref('stg_subscriptions') }}
    UNION ALL -- Continues combining data quality metrics.
    SELECT
        'usage_events' AS table_name,
        COUNT(*) AS total_records,
        COUNT(DISTINCT event_id) AS unique_keys,
        COUNT(CASE WHEN session_duration_minutes < 0 THEN 1 END) AS negative_duration, -- Count of negative session durations.
        COUNT(CASE WHEN pages_viewed < 0 THEN 1 END) AS negative_pages, -- Count of negative page views.
        COUNT(CASE WHEN event_date > CURRENT_DATE THEN 1 END) AS future_dates -- Count of usage events with future dates.
    FROM {{ ref('stg_usage_events') }}
),
business_rule_checks AS (
    SELECT
        'Customer LTV Validation' AS check_name, -- Name of the business rule check.
        COUNT(CASE WHEN estimated_ltv < 0 THEN 1 END) AS failures, -- Counts records where LTV is unexpectedly negative.
        COUNT(*) AS total_checked, -- Total records checked by this rule.
        'Critical' AS severity -- Severity of the data quality issue.
    FROM {{ ref('dim_customers') }}
    UNION ALL -- Combines multiple business rule checks.
    SELECT
        'MRR Consistency Check' AS check_name,
        COUNT(CASE WHEN total_mrr < 0 OR net_new_mrr > total_mrr * 2 THEN 1 END) AS failures, -- Flags inconsistent MRR values (e.g., negative total MRR, or net new MRR suspiciously large).
        COUNT(*) AS total_checked,
        'High' AS severity
    FROM {{ ref('fact_subscription_metrics') }}
    WHERE metric_date >= CURRENT_DATE - 30 -- Checks for recent data (last 30 days).
    UNION ALL -- Continues combining business rule checks.
    SELECT
        'Churn Rate Bounds Check' AS check_name,
        COUNT(CASE WHEN daily_churn_rate_pct < 0 OR daily_churn_rate_pct > 100 THEN 1 END) AS failures, -- Flags churn rates outside the valid 0-100% range.
        COUNT(*) AS total_checked,
        'Medium' AS severity
    FROM {{ ref('fact_subscription_metrics') }}
    WHERE metric_date >= CURRENT_DATE - 30 -- Checks for recent data.
)
SELECT
    table_name,
    total_records,
    unique_keys,
    CASE WHEN unique_keys = total_records THEN 'PASS' ELSE 'FAIL' END AS uniqueness_check, -- Checks if all keys are unique (expected for primary keys).
    -- Calculate data quality scores as a percentage (100 - % of flagged issues).
    CASE 
        WHEN table_name = 'customers' THEN 
            100 - ((missing_email + missing_signup_date + missing_country)::FLOAT / total_records * 100)
        WHEN table_name = 'subscriptions' THEN 
            100 - ((invalid_revenue + invalid_dates + missing_customer_id)::FLOAT / total_records * 100)
        WHEN table_name = 'usage_events' THEN 
            100 - ((negative_duration + negative_pages + future_dates)::FLOAT / total_records * 100)
        ELSE 100 -- Defaults to 100% if no specific quality checks are defined for a table or check.
    END AS data_quality_score,
    CURRENT_TIMESTAMP AS last_checked -- Timestamp of when the quality check was last performed.
FROM source_quality
UNION ALL -- Combines source data quality checks with business rule checks for a comprehensive view.
SELECT
    check_name AS table_name, -- Renames check_name to table_name for union compatibility.
    total_checked AS total_records, -- Renames total_checked to total_records (total items checked by the rule).
    failures AS unique_keys, -- Renames failures to unique_keys (representing the count of records that failed the rule).
    CASE WHEN failures = 0 THEN 'PASS' ELSE 'FAIL' END AS uniqueness_check, -- Indicates if the business rule check passed or failed.
    CASE WHEN total_checked > 0 THEN 100 - (failures::FLOAT / total_checked * 100) ELSE 100 END AS data_quality_score, -- Calculates quality score for business rules.
    CURRENT_TIMESTAMP AS last_checked
FROM business_rule_checks STAGING MODELS