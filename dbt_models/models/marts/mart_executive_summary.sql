{{ config(materialized='table') }} -- Configures this dbt model to be created as a SQL table for persistence.

WITH current_period_metrics AS (
    SELECT
        DATE_TRUNC('month', CURRENT_DATE) AS current_month, -- Defines the current reporting month.
        DATE_TRUNC('month', DATEADD('month', -1, CURRENT_DATE)) AS previous_month, -- Defines the previous reporting month.
        -- Current month metrics: Calculates average MRR, active customers, and churn rate for the current month.
        SUM(CASE WHEN fsm.metric_date >= DATE_TRUNC('month', CURRENT_DATE) 
                 THEN fsm.total_mrr ELSE 0 END) / 
        COUNT(CASE WHEN fsm.metric_date >= DATE_TRUNC('month', CURRENT_DATE) 
                   THEN 1 END) AS current_month_avg_mrr,
        SUM(CASE WHEN fsm.metric_date >= DATE_TRUNC('month', CURRENT_DATE) 
                 THEN fsm.active_customers ELSE 0 END) / 
        COUNT(CASE WHEN fsm.metric_date >= DATE_TRUNC('month', CURRENT_DATE) 
                   THEN 1 END) AS current_month_avg_customers,
        AVG(CASE WHEN fsm.metric_date >= DATE_TRUNC('month', CURRENT_DATE) 
                 THEN fsm.daily_churn_rate_pct ELSE NULL END) AS current_month_avg_churn_rate,
        -- Previous month metrics: Calculates average MRR and active customers for the prior month for comparison.
        SUM(CASE WHEN fsm.metric_date >= DATE_TRUNC('month', DATEADD('month', -1, CURRENT_DATE))
                      AND fsm.metric_date < DATE_TRUNC('month', CURRENT_DATE)
                 THEN fsm.total_mrr ELSE 0 END) / 
        COUNT(CASE WHEN fsm.metric_date >= DATE_TRUNC('month', DATEADD('month', -1, CURRENT_DATE))
                        AND fsm.metric_date < DATE_TRUNC('month', CURRENT_DATE)
                   THEN 1 END) AS previous_month_avg_mrr,
        SUM(CASE WHEN fsm.metric_date >= DATE_TRUNC('month', DATEADD('month', -1, CURRENT_DATE))
                      AND fsm.metric_date < DATE_TRUNC('month', CURRENT_DATE)
                 THEN fsm.active_customers ELSE 0 END) / 
        COUNT(CASE WHEN fsm.metric_date >= DATE_TRUNC('month', DATEADD('month', -1, CURRENT_DATE))
                        AND fsm.metric_date < DATE_TRUNC('month', CURRENT_DATE)
                   THEN 1 END) AS previous_month_avg_customers
    FROM {{ ref('fact_subscription_metrics') }} fsm
    WHERE fsm.metric_date >= DATE_TRUNC('month', DATEADD('month', -1, CURRENT_DATE)) -- Limits data to current and previous month.
),
hub_performance AS (
    SELECT
        hub,
        SUM(total_mrr) AS hub_total_mrr, -- Total MRR per hub.
        SUM(active_customers) AS hub_total_customers, -- Total active customers per hub.
        AVG(arpu) AS hub_avg_arpu, -- Average ARPU per hub.
        AVG(daily_churn_rate_pct) AS hub_avg_churn_rate -- Average churn rate per hub.
    FROM {{ ref('fact_subscription_metrics') }} fsm
    WHERE fsm.metric_date = (SELECT MAX(metric_date) FROM {{ ref('fact_subscription_metrics') }}) -- Considers only the latest available daily metrics for current performance.
    GROUP BY hub -- Aggregates performance by hub.
),
customer_segments AS (
    SELECT
        customer_segment,
        COUNT(*) AS segment_count, -- Count of customers in each segment.
        SUM(current_mrr) AS segment_mrr, -- Total MRR for each segment.
        AVG(estimated_ltv) AS segment_avg_ltv, -- Average LTV for each segment.
        COUNT(CASE WHEN churn_risk = 'HIGH' THEN 1 END) AS high_risk_count -- Count of high-risk customers per segment.
    FROM {{ ref('dim_customers') }}
    GROUP BY customer_segment -- Aggregates customer data by segment.
),
pricing_opportunities AS (
    SELECT
        hub,
        tier,
        optimal_price,
        current_avg_price,
        optimal_revenue_uplift_pct, -- Percentage uplift from optimal pricing scenario.
        strategic_recommendation -- Strategic recommendation for the pricing scenario.
    FROM {{ ref('fact_pricing_optimization') }}
    WHERE revenue_rank = 1 -- Focuses on the most optimal (rank 1) pricing scenarios only.
)
SELECT
    -- Executive KPIs from the current period.
    current_month,
    current_month_avg_mrr,
    current_month_avg_customers,
    current_month_avg_churn_rate,
    -- Growth metrics: Month-over-month percentage growth for MRR and customers.
    CASE 
        WHEN previous_month_avg_mrr > 0 
        THEN ((current_month_avg_mrr - previous_month_avg_mrr) / previous_month_avg_mrr) * 100
        ELSE 0 -- Avoids division by zero.
    END AS mrr_growth_mom_pct,
    CASE 
        WHEN previous_month_avg_customers > 0 
        THEN ((current_month_avg_customers - previous_month_avg_customers) / previous_month_avg_customers) * 100
        ELSE 0 -- Avoids division by zero.
    END AS customer_growth_mom_pct,
    -- Top performing hub by revenue.
    (SELECT hub FROM hub_performance ORDER BY hub_total_mrr DESC LIMIT 1) AS top_hub_by_revenue,
    (SELECT hub_total_mrr FROM hub_performance ORDER BY hub_total_mrr DESC LIMIT 1) AS top_hub_revenue,
    -- Customer insights: Count of champion customers, their MRR, and total high-risk customers.
    (SELECT segment_count FROM customer_segments WHERE customer_segment = 'CHAMPION') AS champion_customers,
    (SELECT segment_mrr FROM customer_segments WHERE customer_segment = 'CHAMPION') AS champion_mrr,
    (SELECT SUM(high_risk_count) FROM customer_segments) AS total_high_risk_customers,
    -- Pricing opportunities: Count of immediate opportunities and total potential revenue uplift.
    (SELECT COUNT(*) FROM pricing_opportunities WHERE strategic_recommendation = 'IMPLEMENT_IMMEDIATELY') AS immediate_pricing_opportunities,
    (SELECT SUM(optimal_revenue_uplift_pct) FROM pricing_opportunities WHERE strategic_recommendation = 'IMPLEMENT_IMMEDIATELY') AS total_pricing_upside_pct,
    -- Metadata for tracking report generation.
    CURRENT_TIMESTAMP AS report_generated_at,
    'EXECUTIVE_SUMMARY' AS report_type
FROM current_period_metrics;