SELECT
  hub,
  tier,
  COUNT(*) AS customer_count,
  AVG(monthly_recurring_revenue) AS avg_mrr,
  AVG(months_active) AS avg_months_active,
  AVG(ltv) AS avg_ltv,
  AVG(CASE WHEN churned THEN 1 ELSE 0 END) AS churn_rate
FROM {{ ref('stg_usage') }}
GROUP BY hub, tier
