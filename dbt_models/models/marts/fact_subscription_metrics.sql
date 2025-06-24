{{ config(materialized='table') }} -- Configures this dbt model to be created as a SQL table.

WITH daily_metrics AS (
    SELECT
        DATE_TRUNC('day', d.date_day) AS metric_date, -- Metric aggregated by day.
        s.hub,
        s.tier,
        c.industry,
        c.company_size,
        c.country,
        -- Subscription metrics: Counts of active, new, and churned subscriptions on each day.
        COUNT(DISTINCT CASE WHEN s.subscription_start_date <= d.date_day 
                           AND (s.subscription_end_date > d.date_day OR s.subscription_end_date IS NULL) -- Checks if subscription is active on a given day.
                           THEN s.subscription_id END) AS active_subscriptions,
        COUNT(DISTINCT CASE WHEN s.subscription_start_date = d.date_day -- Counts subscriptions that started on this specific day.
                           THEN s.subscription_id END) AS new_subscriptions,
        COUNT(DISTINCT CASE WHEN s.subscription_end_date = d.date_day -- Counts subscriptions that ended (churned) on this specific day.
                           THEN s.subscription_id END) AS churned_subscriptions,
        -- Revenue metrics: Total, new, and churned MRR on each day.
        SUM(CASE WHEN s.subscription_start_date <= d.date_day 
                 AND (s.subscription_end_date > d.date_day OR s.subscription_end_date IS NULL) -- Checks if MRR contributes on a given day.
                 THEN s.monthly_revenue ELSE 0 END) AS total_mrr,
        SUM(CASE WHEN s.subscription_start_date = d.date_day -- MRR from new subscriptions on this day.
                 THEN s.monthly_revenue ELSE 0 END) AS new_mrr,
        SUM(CASE WHEN s.subscription_end_date = d.date_day -- MRR lost from churned subscriptions on this day.
                 THEN s.monthly_revenue ELSE 0 END) AS churned_mrr,
        -- Customer metrics: Count of active customers on each day.
        COUNT(DISTINCT CASE WHEN s.subscription_start_date <= d.date_day 
                           AND (s.subscription_end_date > d.date_day OR s.subscription_end_date IS NULL) -- Checks if customer is active on a given day.
                           THEN s.customer_id END) AS active_customers
    FROM {{ ref('stg_subscriptions') }} s
    CROSS JOIN (
        SELECT DATE_TRUNC('day', DATEADD('day', ROW_NUMBER() OVER () - 1, '2023-01-01')) AS date_day
        FROM {{ ref('stg_subscriptions') }} -- Generates a sequence of daily dates starting from a base date.
        LIMIT 730 -- Limits the date range to 2 years of daily data for analysis.
    ) d
    LEFT JOIN {{ ref('stg_customers') }} c ON s.customer_id = c.customer_id -- Joins with customer data for demographic dimensions.
    WHERE d.date_day <= CURRENT_DATE -- Ensures dates are not in the future relative to the current run.
      AND d.date_day >= '2023-01-01' -- Ensures dates start from Jan 1, 2023, for relevant historical analysis.
    GROUP BY 1, 2, 3, 4, 5, 6 -- Groups by metric date and all relevant dimensions for daily metrics.
),
metrics_with_calculations AS (
    SELECT
        *,
        -- Calculate growth rates using LAG window function to compare to previous periods.
        LAG(total_mrr, 30) OVER (PARTITION BY hub, tier ORDER BY metric_date) AS mrr_30_days_ago, -- MRR from 30 days prior.
        LAG(active_subscriptions, 7) OVER (PARTITION BY hub, tier ORDER BY metric_date) AS subscriptions_7_days_ago, -- Active subscriptions from 7 days prior.
        LAG(total_mrr, 7) OVER (PARTITION BY hub, tier ORDER BY metric_date) AS mrr_7_days_ago, -- MRR from 7 days prior.
        -- Calculate daily churn rate (churned subscriptions divided by previous day's active subscriptions).
        CASE 
            WHEN LAG(active_subscriptions, 1) OVER (PARTITION BY hub, tier ORDER BY metric_date) > 0
            THEN churned_subscriptions::FLOAT / LAG(active_subscriptions, 1) OVER (PARTITION BY hub, tier ORDER BY metric_date)
            ELSE 0 -- Avoids division by zero.
        END AS daily_churn_rate,
        -- Calculate net revenue retention (30-day): Current MRR divided by MRR from 30 days ago.
        CASE 
            WHEN LAG(total_mrr, 30) OVER (PARTITION BY hub, tier ORDER BY metric_date) > 0
            THEN total_mrr::FLOAT / LAG(total_mrr, 30) OVER (PARTITION BY hub, tier ORDER BY metric_date)
            ELSE 1 -- Assumes 100% retention if no previous MRR for comparison.
        END AS revenue_retention_30d
    FROM daily_metrics
)
SELECT
    -- Primary key for the fact table, ensuring uniqueness for each daily metric snapshot.
    {{ dbt_utils.generate_surrogate_key(['metric_date', 'hub', 'tier', 'industry', 'company_size', 'country']) }} AS fact_key,
    metric_date,
    {{ dbt_utils.generate_surrogate_key(['hub', 'tier']) }} AS product_key, -- Foreign key to the product dimension.
    -- Dimensions for slicing and dicing metrics by various attributes.
    hub,
    tier,
    industry,
    company_size,
    country,
    -- Subscription metrics: Raw and aggregated counts.
    active_subscriptions,
    new_subscriptions,
    churned_subscriptions,
    active_customers,
    -- Revenue metrics: Raw MRR values and net change.
    total_mrr,
    new_mrr,
    churned_mrr,
    COALESCE(new_mrr - churned_mrr, 0) AS net_new_mrr, -- Calculates net change in MRR (new MRR - churned MRR).
    -- Growth metrics: Percentage growth for MRR (30-day) and subscriptions (7-day).
    CASE 
        WHEN mrr_30_days_ago > 0 
        THEN ((total_mrr - mrr_30_days_ago) / mrr_30_days_ago) * 100 
        ELSE 0 
    END AS mrr_growth_30d_pct,
    CASE 
        WHEN subscriptions_7_days_ago > 0 
        THEN ((active_subscriptions - subscriptions_7_days_ago) / subscriptions_7_days_ago) * 100 
        ELSE 0 
    END AS subscription_growth_7d_pct,
    -- Retention metrics: Daily churn rate as a percentage and 30-day revenue retention as a percentage.
    daily_churn_rate * 100 AS daily_churn_rate_pct,
    revenue_retention_30d * 100 AS revenue_retention_30d_pct,
    -- Unit economics: Average Revenue Per User (ARPU) and average value of new subscriptions.
    CASE 
        WHEN active_customers > 0 
        THEN total_mrr / active_customers 
        ELSE 0 
    END AS arpu, -- Average Revenue Per User
    CASE 
        WHEN new_subscriptions > 0 
        THEN new_mrr / new_subscriptions 
        ELSE 0 
    END AS avg_new_subscription_value,
    -- Metadata for tracking report generation time.
    CURRENT_TIMESTAMP AS created_at
FROM metrics_with_calculations
WHERE metric_date >= '2023-01-01' -- Filters to include data from January 1, 2023, onwards.
  AND total_mrr >= 0; -- Data quality check: Ensures total MRR is non-negative.