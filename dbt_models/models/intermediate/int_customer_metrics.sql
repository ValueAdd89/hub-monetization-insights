{{ config(materialized='table') }} -- Configures this dbt model to be created as a SQL table for persistence and efficient querying.

WITH customer_base AS (
    SELECT * FROM {{ ref('stg_customers') }} -- Selects all cleaned customer demographic data.
),
subscription_summary AS (
    SELECT
        customer_id,
        COUNT(DISTINCT subscription_id) AS total_subscriptions, -- Counts all unique subscriptions for a customer.
        COUNT(DISTINCT CASE WHEN is_active THEN subscription_id END) AS active_subscriptions, -- Counts only currently active subscriptions.
        COUNT(DISTINCT hub) AS unique_hubs_subscribed, -- Counts unique product hubs a customer is subscribed to (e.g., CMS, CRM).
        SUM(CASE WHEN is_active THEN monthly_revenue ELSE 0 END) AS current_mrr, -- Calculates current Monthly Recurring Revenue from active subscriptions.
        SUM(monthly_revenue) AS total_historical_mrr, -- Calculates total revenue generated from all (active and past) subscriptions.
        MIN(subscription_start_date) AS first_subscription_date, -- Finds the earliest subscription start date for a customer.
        MAX(subscription_start_date) AS latest_subscription_date, -- Finds the latest subscription start date for a customer.
        STRING_AGG(DISTINCT hub, ', ' ORDER BY hub) AS subscribed_hubs, -- Aggregates all subscribed product hubs into a comma-separated string.
        STRING_AGG(DISTINCT tier, ', ' ORDER BY tier) AS subscription_tiers -- Aggregates all subscribed tiers into a comma-separated string.
    FROM {{ ref('stg_subscriptions') }}
    GROUP BY customer_id -- Aggregates all subscription-related metrics per customer.
),
usage_summary AS (
    SELECT
        customer_id,
        COUNT(DISTINCT event_date) AS total_active_days, -- Counts unique days a customer had usage events, indicating activity frequency.
        COUNT(event_id) AS total_events, -- Counts all usage events for a customer.
        SUM(session_duration_minutes) AS total_session_minutes, -- Sums up all session durations for a customer.
        SUM(pages_viewed) AS total_pages_viewed, -- Sums up all pages viewed by a customer.
        SUM(api_calls) AS total_api_calls, -- Sums up all API calls made by a customer.
        COUNT(DISTINCT feature_used) AS unique_features_used, -- Counts unique features a customer has interacted with.
        AVG(session_duration_minutes) AS avg_session_duration, -- Calculates average session duration for a customer.
        MAX(event_date) AS last_activity_date, -- Finds the most recent usage activity date.
        MIN(event_date) AS first_activity_date, -- Finds the earliest usage activity date.
        -- Advanced engagement metrics: Counts sessions categorized by engagement level (HIGH, MEDIUM, LOW, MINIMAL).
        COUNT(CASE WHEN engagement_level = 'HIGH' THEN 1 END) AS high_engagement_sessions,
        COUNT(CASE WHEN engagement_level = 'MEDIUM' THEN 1 END) AS medium_engagement_sessions,
        COUNT(CASE WHEN engagement_level = 'LOW' THEN 1 END) AS low_engagement_sessions,
        COUNT(CASE WHEN engagement_level = 'MINIMAL' THEN 1 END) AS minimal_engagement_sessions
    FROM {{ ref('stg_usage_events') }}
    GROUP BY customer_id -- Aggregates all usage-related metrics per customer.
),
support_summary AS (
    SELECT
        customer_id,
        COUNT(interaction_id) AS total_support_tickets, -- Counts total support tickets initiated by a customer.
        COUNT(CASE WHEN resolved THEN interaction_id END) AS resolved_tickets, -- Counts resolved support tickets.
        COUNT(CASE WHEN priority = 'HIGH' THEN interaction_id END) AS high_priority_tickets, -- Counts high priority tickets.
        AVG(resolution_time_hours) AS avg_resolution_time_hours, -- Calculates average resolution time for tickets.
        AVG(satisfaction_score) AS avg_satisfaction_score, -- Calculates average satisfaction score from support interactions.
        MAX(interaction_date) AS last_support_date, -- Finds the most recent support interaction date.
        MIN(interaction_date) AS first_support_date, -- Finds the earliest support interaction date.
        -- Support health metrics: Counts interactions by satisfaction category.
        COUNT(CASE WHEN satisfaction_category = 'SATISFIED' THEN 1 END) AS satisfied_interactions,
        COUNT(CASE WHEN satisfaction_category = 'DISSATISFIED' THEN 1 END) AS dissatisfied_interactions
    FROM {{ ref('stg_support_interactions') }}
    GROUP BY customer_id -- Aggregates all support-related metrics per customer.
)
SELECT
    c.customer_id,
    c.company_name,
    c.industry,
    c.company_size,
    c.country,
    c.state,
    c.signup_date,
    -- Subscription metrics: Joined from `subscription_summary`. COALESCE ensures 0 instead of NULL for customers with no data.
    COALESCE(sub.total_subscriptions, 0) AS total_subscriptions,
    COALESCE(sub.active_subscriptions, 0) AS active_subscriptions,
    COALESCE(sub.unique_hubs_subscribed, 0) AS unique_hubs_subscribed,
    COALESCE(sub.current_mrr, 0) AS current_mrr,
    COALESCE(sub.total_historical_mrr, 0) AS total_historical_mrr,
    sub.first_subscription_date,
    sub.latest_subscription_date,
    sub.subscribed_hubs,
    sub.subscription_tiers,
    -- Usage metrics: Joined from `usage_summary`.
    COALESCE(usage.total_active_days, 0) AS total_active_days,
    COALESCE(usage.total_events, 0) AS total_events,
    COALESCE(usage.total_session_minutes, 0) AS total_session_minutes,
    COALESCE(usage.total_pages_viewed, 0) AS total_pages_viewed,
    COALESCE(usage.total_api_calls, 0) AS total_api_calls,
    COALESCE(usage.unique_features_used, 0) AS unique_features_used,
    COALESCE(usage.avg_session_duration, 0) AS avg_session_duration,
    usage.last_activity_date,
    usage.first_activity_date,
    -- Support metrics: Joined from `support_summary`.
    COALESCE(support.total_support_tickets, 0) AS total_support_tickets,
    COALESCE(support.resolved_tickets, 0) AS resolved_tickets,
    COALESCE(support.high_priority_tickets, 0) AS high_priority_tickets,
    COALESCE(support.avg_resolution_time_hours, 0) AS avg_resolution_time_hours,
    COALESCE(support.avg_satisfaction_score, 0) AS avg_satisfaction_score,
    support.last_support_date,
    -- Calculated business metrics: Derive key performance indicators vital for customer understanding.
    DATEDIFF('day', c.signup_date, CURRENT_DATE) AS customer_age_days, -- Calculates customer age in days since their initial signup.
    CASE 
        WHEN sub.first_subscription_date IS NOT NULL 
        THEN DATEDIFF('month', sub.first_subscription_date, CURRENT_DATE) -- Calculates months since the customer's first subscription.
        ELSE 0  -- Defaults to 0 if no subscription history.
    END AS months_since_first_subscription,
    CASE 
        WHEN usage.last_activity_date IS NOT NULL 
        THEN DATEDIFF('day', usage.last_activity_date, CURRENT_DATE) -- Calculates days since the last recorded usage activity.
        ELSE 999  -- Assigns a high value for customers with no usage data, indicating potential inactivity.
    END AS days_since_last_activity,
    -- Customer health score (0-100): A composite score indicating overall customer health/engagement.
    LEAST(100, -- Caps the total score at 100 to ensure a bounded range.
        COALESCE(
            (CASE WHEN usage.avg_session_duration > 0 THEN LEAST(30, usage.avg_session_duration) ELSE 0 END) + -- Contribution from average session duration (capped at 30).
            (CASE WHEN usage.unique_features_used > 0 THEN LEAST(20, usage.unique_features_used * 2) ELSE 0 END) + -- Contribution from unique features used (capped at 20).
            (CASE WHEN support.avg_satisfaction_score > 0 THEN support.avg_satisfaction_score * 10 ELSE 0 END) + -- Contribution from average satisfaction score (scaled).
            (CASE WHEN sub.active_subscriptions > 0 THEN 20 ELSE 0 END) + -- Bonus for having active subscriptions.
            (CASE WHEN DATEDIFF('day', usage.last_activity_date, CURRENT_DATE) <= 7 THEN 20 ELSE 0 END) -- Bonus for recent activity (within 7 days).
        , 0) -- Coalesce to 0 if all components for health score are null.
    ) AS customer_health_score
FROM customer_base c
LEFT JOIN subscription_summary sub ON c.customer_id = sub.customer_id -- Left join to include all customers, even those without subscriptions.
LEFT JOIN usage_summary usage ON c.customer_id = usage.customer_id -- Left join to include all customers, even those without usage data.
LEFT JOIN support_summary support ON c.customer_id = support.customer_id -- Left join to include all customers, even those without support interactions.