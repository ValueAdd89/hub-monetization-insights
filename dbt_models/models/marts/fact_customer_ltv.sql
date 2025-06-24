{{ config(materialized='table') }} -- Configures this dbt model to be created as a SQL table for persistence.

WITH customer_revenue_history AS (
    SELECT
        s.customer_id,
        s.hub,
        s.tier,
        c.industry,
        c.company_size,
        c.country,
        s.subscription_start_date,
        s.subscription_end_date,
        s.monthly_revenue,
        s.is_active,
        -- Calculate subscription duration in months (from start to end or current date).
        CASE 
            WHEN s.subscription_end_date IS NOT NULL 
            THEN DATEDIFF('month', s.subscription_start_date, s.subscription_end_date)
            ELSE DATEDIFF('month', s.subscription_start_date, CURRENT_DATE)
        END AS subscription_duration_months,
        -- Calculate total revenue generated from this specific subscription instance.
        CASE 
            WHEN s.subscription_end_date IS NOT NULL 
            THEN DATEDIFF('month', s.subscription_start_date, s.subscription_end_date) * s.monthly_revenue
            ELSE DATEDIFF('month', s.subscription_start_date, CURRENT_DATE) * s.monthly_revenue
        END AS total_subscription_revenue
    FROM {{ ref('stg_subscriptions') }} s
    LEFT JOIN {{ ref('stg_customers') }} c ON s.customer_id = c.customer_id -- Joins with customer data for relevant dimensions.
),
customer_usage_value AS (
    SELECT
        u.customer_id,
        COUNT(DISTINCT u.event_date) AS total_usage_days, -- Total days a customer had usage events.
        AVG(u.session_duration_minutes) AS avg_session_duration, -- Average duration of a customer's usage sessions.
        COUNT(DISTINCT u.feature_used) AS unique_features_used, -- Count of distinct features a customer has used.
        SUM(u.pages_viewed) AS total_pages_viewed, -- Total pages viewed by a customer.
        SUM(u.api_calls) AS total_api_calls, -- Total API calls made by a customer.
        -- Calculate usage-based value score: A composite score indicating customer engagement and feature adoption.
        (COUNT(DISTINCT u.event_date) * 0.3 + -- Weights usage frequency.
         AVG(u.session_duration_minutes) * 0.1 + -- Weights engagement depth.
         COUNT(DISTINCT u.feature_used) * 5 + -- Weights feature adoption significantly.
         SUM(u.pages_viewed) * 0.01 + -- Weights content consumption.
         SUM(u.api_calls) * 0.005) AS usage_value_score -- Weights API call volume.
    FROM {{ ref('stg_usage_events') }} u
    GROUP BY u.customer_id -- Aggregates usage data per customer.
),
customer_support_cost AS (
    SELECT
        sp.customer_id,
        COUNT(sp.interaction_id) AS total_support_interactions, -- Total number of support interactions.
        AVG(sp.resolution_time_hours) AS avg_resolution_time, -- Average time to resolve support tickets.
        AVG(sp.satisfaction_score) AS avg_satisfaction, -- Average satisfaction score from support.
        -- Estimate support cost (simplified model): Assigns a cost per interaction based on resolution time.
        COUNT(sp.interaction_id) * 
        CASE 
            WHEN AVG(sp.resolution_time_hours) <= 2 THEN 25 -- Low cost for quick resolutions.
            WHEN AVG(sp.resolution_time_hours) <= 8 THEN 50 -- Medium cost.
            ELSE 100 -- High cost for complex/long issues.
        END AS estimated_support_cost
    FROM {{ ref('stg_support_interactions') }} sp
    GROUP BY sp.customer_id -- Aggregates support data per customer.
),
ltv_calculation AS (
    SELECT
        r.customer_id,
        r.industry,
        r.company_size,
        r.country,
        -- Aggregate subscription metrics from customer revenue history.
        COUNT(DISTINCT r.hub) AS total_hubs_subscribed,
        COUNT(r.subscription_start_date) AS total_subscriptions,
        COUNT(CASE WHEN r.is_active THEN 1 END) AS active_subscriptions,
        SUM(r.total_subscription_revenue) AS total_historical_revenue,
        SUM(CASE WHEN r.is_active THEN r.monthly_revenue ELSE 0 END) AS current_mrr,
        AVG(r.subscription_duration_months) AS avg_subscription_duration,
        MIN(r.subscription_start_date) AS first_subscription_date,
        MAX(r.subscription_start_date) AS latest_subscription_date,
        -- Usage metrics joined from `customer_usage_value`. COALESCE handles missing usage data.
        COALESCE(u.total_usage_days, 0) AS total_usage_days,
        COALESCE(u.avg_session_duration, 0) AS avg_session_duration,
        COALESCE(u.unique_features_used, 0) AS unique_features_used,
        COALESCE(u.usage_value_score, 0) AS usage_value_score,
        -- Support metrics joined from `customer_support_cost`. COALESCE handles missing support data.
        COALESCE(sp.total_support_interactions, 0) AS total_support_interactions,
        COALESCE(sp.avg_satisfaction, 5) AS avg_satisfaction, -- Defaults to 5 if no satisfaction data.
        COALESCE(sp.estimated_support_cost, 0) AS estimated_support_cost,
        -- Customer lifecycle calculations.
        DATEDIFF('month', MIN(r.subscription_start_date), CURRENT_DATE) AS customer_age_months, -- Calculates total customer age since first subscription.
        -- LTV Components: Net historical value after deducting estimated support costs.
        SUM(r.total_subscription_revenue) - COALESCE(sp.estimated_support_cost, 0) AS net_historical_value,
        -- Predictive LTV: Estimates future value, considering current active status, engagement, and satisfaction.
        CASE 
            WHEN COUNT(CASE WHEN r.is_active THEN 1 END) > 0 THEN -- Logic for actively subscribed customers.
                -- Base projection: current MRR * average subscription duration.
                SUM(CASE WHEN r.is_active THEN r.monthly_revenue ELSE 0 END) * 
                GREATEST(1, AVG(r.subscription_duration_months)) * 
                -- Adjust for usage engagement: Higher usage_value_score increases LTV.
                (1 + COALESCE(u.usage_value_score, 0) / 1000) *
                -- Adjust for satisfaction: Higher satisfaction increases LTV.
                (COALESCE(sp.avg_satisfaction, 5) / 5) *
                -- Adjust for multi-hub usage: Subscribing to more hubs increases LTV.
                (1 + COUNT(DISTINCT r.hub) * 0.1)
            ELSE -- Logic for churned or inactive customers.
                -- For churned customers, LTV is their total historical revenue minus support cost.
                SUM(r.total_subscription_revenue) - COALESCE(sp.estimated_support_cost, 0)
        END AS predicted_ltv
    FROM customer_revenue_history r
    LEFT JOIN customer_usage_value u ON r.customer_id = u.customer_id
    LEFT JOIN customer_support_cost sp ON r.customer_id = sp.customer_id
    GROUP BY r.customer_id, r.industry, r.company_size, r.country -- Groups by customer and relevant dimensions.
)
SELECT
    -- Primary key
    customer_id,
    -- Dimensions for slicing and dicing LTV data.
    industry,
    company_size,
    country,
    -- Customer metrics relevant to LTV.
    total_hubs_subscribed,
    total_subscriptions,
    active_subscriptions,
    customer_age_months,
    first_subscription_date,
    latest_subscription_date,
    -- Revenue metrics for LTV calculations.
    total_historical_revenue,
    current_mrr,
    avg_subscription_duration,
    net_historical_value,
    predicted_ltv,
    estimated_support_cost,
    -- Usage metrics contributing to LTV.
    total_usage_days,
    avg_session_duration,
    unique_features_used,
    usage_value_score,
    -- Support metrics contributing to LTV.
    total_support_interactions,
    avg_satisfaction,
    -- LTV categorization: Segment customers based on their predicted LTV for targeted strategies.
    CASE 
        WHEN predicted_ltv >= 10000 THEN 'VERY_HIGH'
        WHEN predicted_ltv >= 5000 THEN 'HIGH'
        WHEN predicted_ltv >= 2000 THEN 'MEDIUM'
        WHEN predicted_ltv >= 500 THEN 'LOW'
        ELSE 'VERY_LOW'
    END AS ltv_segment,
    -- ROI calculation for customer based on net value vs estimated support cost.
    CASE 
        WHEN estimated_support_cost > 0 
        THEN (net_historical_value / estimated_support_cost) * 100 
        ELSE NULL -- Avoids division by zero.
    END AS customer_roi_pct,
    -- Payback period (simplified): Time in months to recoup estimated support costs through current MRR.
    CASE 
        WHEN current_mrr > 0 
        THEN estimated_support_cost / current_mrr 
        ELSE NULL -- Avoids division by zero.
    END AS payback_period_months,
    -- Metadata for tracking.
    CURRENT_TIMESTAMP AS created_at
FROM ltv_calculation
WHERE customer_age_months >= 0; -- Data quality check: Ensures customer age is non-negative.
