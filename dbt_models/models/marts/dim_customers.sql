{{ config(materialized='table') }} -- Configures this dbt model to be created as a SQL table for efficient querying.

WITH customer_enriched AS (
    SELECT
        cm.*, -- Selects all customer metrics from the intermediate model (`int_customer_metrics`).
        -- Customer segmentation based on multiple factors: Categorizes customers for targeted marketing and analysis.
        CASE 
            WHEN cm.current_mrr >= 500 AND cm.customer_health_score >= 80 THEN 'CHAMPION' -- High-value, healthy customers.
            WHEN cm.current_mrr >= 200 AND cm.customer_health_score >= 70 THEN 'LOYAL' -- Consistent, engaged customers.
            WHEN cm.customer_health_score >= 80 AND cm.days_since_last_activity <= 7 THEN 'POTENTIAL_LOYAL' -- Healthy and recently active, new potential.
            WHEN cm.current_mrr >= 100 AND cm.days_since_last_activity <= 30 THEN 'NEW_CUSTOMER' -- Recently acquired and active.
            WHEN cm.customer_health_score >= 50 AND cm.days_since_last_activity <= 30 THEN 'PROMISING' -- Showing some engagement.
            WHEN cm.current_mrr > 0 AND cm.days_since_last_activity > 30 THEN 'AT_RISK' -- Active but with signs of disengagement.
            WHEN cm.current_mrr > 0 AND cm.customer_health_score < 30 THEN 'CANNOT_LOSE' -- High MRR but low health, critical to retain.
            WHEN cm.current_mrr = 0 AND cm.days_since_last_activity <= 90 THEN 'HIBERNATING' -- Inactive but potentially recoverable.
            ELSE 'LOST' -- Customers who have likely churned or are very inactive.
        END AS customer_segment,
        -- Lifetime value calculation (simplified): Estimates future value based on current metrics and predictive factors.
        CASE 
            WHEN cm.current_mrr > 0 
            THEN cm.current_mrr * GREATEST(1, cm.months_since_first_subscription) * -- Base LTV from current MRR and tenure.
                 (cm.customer_health_score / 100.0) * 1.2  -- Adjusts LTV based on health score (as a multiplier) and a general uplift factor (1.2).
            ELSE cm.total_historical_mrr -- For inactive customers, LTV is simply their total historical revenue.
        END AS estimated_ltv,
        -- Churn risk scoring: Categorizes customers by their likelihood of churning based on various indicators.
        CASE 
            WHEN cm.days_since_last_activity > 90 THEN 'HIGH' -- High risk if inactive for more than 90 days.
            WHEN cm.days_since_last_activity > 30 AND cm.customer_health_score < 40 THEN 'HIGH' -- High risk if inactive and low health.
            WHEN cm.customer_health_score < 30 THEN 'HIGH' -- High risk if very low health score.
            WHEN cm.days_since_last_activity > 14 AND cm.customer_health_score < 60 THEN 'MEDIUM' -- Medium risk if some inactivity and moderate health.
            WHEN cm.avg_satisfaction_score < 3 AND cm.total_support_tickets > 5 THEN 'MEDIUM' -- Medium risk if low satisfaction and high support needs.
            ELSE 'LOW' -- Low risk otherwise.
        END AS churn_risk
    FROM {{ ref('int_customer_metrics') }} cm
)
SELECT
    customer_id,
    company_name,
    industry,
    company_size,
    country,
    state,
    signup_date,
    customer_segment, -- Derived customer segment.
    estimated_ltv, -- Estimated customer lifetime value.
    churn_risk, -- Categorized churn risk.
    customer_health_score, -- Calculated health score.
    current_mrr, -- Current Monthly Recurring Revenue.
    total_subscriptions, -- Total number of subscriptions.
    active_subscriptions, -- Number of active subscriptions.
    unique_hubs_subscribed, -- Count of distinct product hubs subscribed to.
    subscribed_hubs, -- List of subscribed hubs.
    subscription_tiers, -- List of subscription tiers.
    months_since_first_subscription, -- Tenure since first subscription.
    days_since_last_activity, -- Days since last usage activity.
    total_active_days, -- Total days with recorded usage activity.
    unique_features_used, -- Count of unique features used.
    avg_session_duration, -- Average session duration.
    total_support_tickets, -- Total support tickets.
    avg_satisfaction_score, -- Average satisfaction score.
    -- Add row metadata for tracking when the record was created/updated.
    CURRENT_TIMESTAMP AS created_at,
    CURRENT_TIMESTAMP AS updated_at
FROM customer_enriched -- Final selection for the customer dimension table.