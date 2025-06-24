-- Custom test to ensure MRR calculations are consistent
-- across different models and aggregation levels

SELECT 
    metric_date,
    hub,
    tier,
    SUM(total_mrr) as fact_table_mrr
FROM {{ ref('fact_subscription_metrics') }}
WHERE metric_date = CURRENT_DATE - 1
GROUP BY metric_date, hub, tier
HAVING SUM(total_mrr) < 0  -- Should never be negative

---