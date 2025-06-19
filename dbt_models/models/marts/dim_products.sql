{{ config(materialized='table') }} -- Configures this dbt model to be created as a SQL table for efficient querying.

WITH product_hierarchy AS (
    SELECT DISTINCT
        hub,
        tier,
        -- Create product hierarchy display names for better readability in reports.
        CASE 
            WHEN hub = 'cms' THEN 'Content Management'
            WHEN hub = 'crm' THEN 'Customer Relationship'
            WHEN hub = 'analytics' THEN 'Business Intelligence'
            WHEN hub = 'marketing' THEN 'Marketing Automation'
            WHEN hub = 'sales' THEN 'Sales Enablement'
            ELSE 'Other'
        END AS hub_display_name,
        CASE 
            WHEN tier = 'starter' THEN 'Starter'
            WHEN tier = 'professional' THEN 'Professional'
            WHEN tier = 'enterprise' THEN 'Enterprise'
            ELSE 'Unknown'
        END AS tier_display_name,
        -- Pricing information from current subscriptions: Aggregates pricing metrics per hub and tier.
        AVG(monthly_revenue) AS avg_monthly_revenue,
        MIN(monthly_revenue) AS min_monthly_revenue,
        MAX(monthly_revenue) AS max_monthly_revenue,
        COUNT(DISTINCT customer_id) AS total_subscribers, -- Total number of unique customers subscribed to this hub-tier.
        COUNT(CASE WHEN is_active THEN customer_id END) AS active_subscribers -- Number of currently active subscribers for this hub-tier.
    FROM {{ ref('stg_subscriptions') }}
    GROUP BY hub, tier -- Aggregates product metrics by hub and tier.
)
SELECT
    -- Create surrogate key for unique product combinations, used as a primary key.
    {{ dbt_utils.generate_surrogate_key(['hub', 'tier']) }} AS product_key,
    hub,
    tier,
    hub_display_name,
    tier_display_name,
    hub || ' - ' || tier_display_name AS product_full_name, -- Concatenates hub and tier for a full product name display.
    -- Product attributes: Assigns a numerical rank to tiers for ordering/sorting.
    CASE 
        WHEN tier = 'starter' THEN 1
        WHEN tier = 'professional' THEN 2
        WHEN tier = 'enterprise' THEN 3
        ELSE 0
    END AS tier_rank,
    -- Pricing metrics: Average, min, and max monthly revenue for the product.
    avg_monthly_revenue,
    min_monthly_revenue,
    max_monthly_revenue,
    -- Subscriber metrics: Total and active subscribers, and calculated retention rate.
    total_subscribers,
    active_subscribers,
    CASE WHEN total_subscribers > 0 THEN active_subscribers::FLOAT / total_subscribers ELSE 0 END AS retention_rate, -- Calculates the active retention rate for the product.
    -- Product categorization: Assigns a broader category to each product hub for high-level analysis.
    CASE 
        WHEN hub IN ('cms', 'marketing') THEN 'GROWTH'
        WHEN hub IN ('crm', 'sales') THEN 'REVENUE'
        WHEN hub = 'analytics' THEN 'INTELLIGENCE'
        ELSE 'OTHER'
    END AS product_category,
    -- Metadata for tracking when the product dimension record was created/updated.
    CURRENT_TIMESTAMP AS created_at,
    CURRENT_TIMESTAMP AS updated_at
FROM product_hierarchy
ORDER BY hub, tier_rank -- Orders products for consistent presentation and analysis.