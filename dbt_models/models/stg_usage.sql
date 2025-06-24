SELECT
  customer_id,
  hub,
  tier,
  monthly_recurring_revenue,
  months_active,
  churned,
  monthly_recurring_revenue * months_active AS ltv
FROM {{ source('raw', 'usage_data') }}
