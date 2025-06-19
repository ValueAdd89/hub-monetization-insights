{{ config(materialized='table') }} -- Configures this dbt model to be created as a SQL table.

WITH current_pricing AS (
    SELECT
        hub,
        tier,
        AVG(monthly_revenue) AS current_avg_price, -- Calculates the current average price for each hub-tier combination.
        COUNT(DISTINCT customer_id) AS current_customer_count, -- Counts current active customers for the hub-tier.
        SUM(monthly_revenue) AS current_total_revenue -- Sums current total revenue for the hub-tier.
    FROM {{ ref('stg_subscriptions') }}
    WHERE is_active = TRUE -- Considers only active subscriptions for current pricing.
    GROUP BY hub, tier -- Aggregates current pricing metrics by hub and tier.
),
elasticity_analysis AS (
    SELECT
        pe.*, -- Selects all columns from the intermediate pricing elasticity model (`int_pricing_elasticity`).
        cp.current_avg_price,
        cp.current_customer_count,
        cp.current_total_revenue,
        -- Calculate revenue impact versus current pricing for each simulated scenario.
        (pe.potential_monthly_revenue - cp.current_total_revenue) AS revenue_impact, -- Absolute change in monthly revenue.
        (pe.potential_customers - cp.current_customer_count) AS customer_impact, -- Absolute change in customer count.
        (pe.price_point - cp.current_avg_price) AS price_change, -- Absolute change in price.
        -- Calculate percentage changes for revenue, customer count, and price.
        CASE 
            WHEN cp.current_total_revenue > 0 
            THEN ((pe.potential_monthly_revenue - cp.current_total_revenue) / cp.current_total_revenue) * 100
            ELSE 0 -- Avoids division by zero.
        END AS revenue_change_pct,
        CASE 
            WHEN cp.current_customer_count > 0 
            THEN ((pe.potential_customers - cp.current_customer_count) / cp.current_customer_count) * 100
            ELSE 0 -- Avoids division by zero.
        END AS customer_change_pct,
        CASE 
            WHEN cp.current_avg_price > 0 
            THEN ((pe.price_point - cp.current_avg_price) / cp.current_avg_price) * 100
            ELSE 0 -- Avoids division by zero.
        END AS price_change_pct
    FROM {{ ref('int_pricing_elasticity') }} pe
    LEFT JOIN current_pricing cp ON pe.hub = cp.hub AND pe.tier = cp.tier -- Joins elasticity data with current pricing context.
),
optimal_pricing AS (
    SELECT
        hub,
        tier,
        MAX(CASE WHEN revenue_rank = 1 THEN price_point END) AS optimal_price, -- Finds the price point with the highest potential revenue (rank 1).
        MAX(CASE WHEN revenue_rank = 1 THEN potential_monthly_revenue END) AS max_potential_revenue,
        MAX(CASE WHEN revenue_rank = 1 THEN revenue_change_pct END) AS optimal_revenue_uplift_pct,
        MAX(CASE WHEN revenue_rank = 1 THEN customer_change_pct END) AS optimal_customer_impact_pct,
        MAX(CASE WHEN revenue_rank = 1 THEN pricing_risk_level END) AS optimal_pricing_risk
    FROM elasticity_analysis
    GROUP BY hub, tier -- Aggregates to find optimal pricing per hub and tier.
),
competitive_analysis AS (
    -- This CTE would typically join with an actual competitive data source to compare our pricing.
    -- For this example, it's creating placeholder competitive metrics based on existing subscriptions.
    SELECT
        hub,
        tier,
        AVG(monthly_revenue) * 1.15 AS competitor_avg_price, -- Assumes competitors charge 15% more than our current active MRR.
        'PLACEHOLDER' AS competitive_position -- Placeholder for actual competitive position.
    FROM {{ ref('stg_subscriptions') }}
    WHERE is_active = TRUE
    GROUP BY hub, tier
)
SELECT
    -- Primary key for the pricing optimization fact table, uniquely identifying each scenario.
    {{ dbt_utils.generate_surrogate_key(['ea.hub', 'ea.tier', 'ea.price_point']) }} AS pricing_scenario_key,
    -- Dimensions for analyzing pricing scenarios.
    ea.hub,
    ea.tier,
    ea.price_point,
    -- Current state metrics for comparison against potential scenarios.
    ea.current_avg_price,
    ea.current_customer_count,
    ea.current_total_revenue,
    -- Scenario projections: Potential customers, revenue, and adoption rate at a given price point.
    ea.potential_customers,
    ea.potential_monthly_revenue,
    ea.potential_annual_revenue,
    ea.adoption_rate,
    -- Impact analysis: Absolute and percentage changes if a new price point is adopted.
    ea.revenue_impact,
    ea.customer_impact,
    ea.price_change,
    ea.revenue_change_pct,
    ea.customer_change_pct,
    ea.price_change_pct,
    -- Elasticity metrics: Demand elasticity and its classification, and revenue rank.
    ea.price_elasticity_of_demand,
    ea.elasticity_classification,
    ea.pricing_risk_level,
    ea.revenue_rank,
    -- Optimization recommendations: Details about the most optimal price point for the hub/tier.
    op.optimal_price,
    op.max_potential_revenue,
    op.optimal_revenue_uplift_pct,
    op.optimal_customer_impact_pct,
    op.optimal_pricing_risk,
    -- Competitive context: Our price point's relation to the assumed competitor average.
    ca.competitor_avg_price,
    CASE 
        WHEN ea.price_point < ca.competitor_avg_price * 0.9 THEN 'BELOW_MARKET'
        WHEN ea.price_point > ca.competitor_avg_price * 1.1 THEN 'ABOVE_MARKET'
        ELSE 'MARKET_ALIGNED'
    END AS competitive_position,
    -- Strategic recommendations: Actionable advice based on pricing scenario and risk.
    CASE 
        WHEN ea.revenue_rank = 1 AND ea.pricing_risk_level = 'LOW_RISK' THEN 'IMPLEMENT_IMMEDIATELY'
        WHEN ea.revenue_rank <= 3 AND ea.pricing_risk_level IN ('LOW_RISK', 'MEDIUM_RISK') THEN 'TEST_RECOMMENDED'
        WHEN ea.revenue_change_pct > 10 AND ea.pricing_risk_level = 'MEDIUM_RISK' THEN 'CAREFUL_TESTING'
        WHEN ea.pricing_risk_level = 'HIGH_RISK' THEN 'AVOID'
        ELSE 'MONITOR'
    END AS strategic_recommendation,
    -- Implementation timeline/priority: Suggests when to act on a pricing scenario.
    CASE 
        WHEN ea.revenue_rank = 1 AND ea.pricing_risk_level = 'LOW_RISK' THEN 'Q1'
        WHEN ea.revenue_rank <= 3 AND ea.pricing_risk_level IN ('LOW_RISK', 'MEDIUM_RISK') THEN 'Q2'
        WHEN ea.revenue_change_pct > 5 THEN 'Q3'
        ELSE 'Q4_OR_LATER'
    END AS implementation_priority,
    -- Metadata for tracking.
    CURRENT_TIMESTAMP AS created_at
FROM elasticity_analysis ea
LEFT JOIN optimal_pricing op ON ea.hub = op.hub AND ea.tier = op.tier
LEFT JOIN competitive_analysis ca ON ea.hub = ca.hub AND ea.tier = ca.tier
WHERE ea.potential_customers > 0 -- Filters out scenarios where no customers can be acquired.
  AND ea.price_point > 0 -- Ensures valid (positive) price points are considered.
ORDER BY ea.hub, ea.tier, ea.revenue_rank;