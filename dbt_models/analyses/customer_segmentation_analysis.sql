-- Customer Segmentation Deep Dive Analysis
-- This analysis provides insights into customer behavior patterns
-- and segmentation effectiveness for the executive team

WITH customer_segment_performance AS (
  SELECT
    customer_segment,
    COUNT(*) as customer_count,
    AVG(current_mrr) as avg_mrr,
    AVG(estimated_ltv) as avg_ltv,
    AVG(customer_health_score) as avg_health_score,
    AVG(days_since_last_activity) as avg_days_inactive,
    COUNT(CASE WHEN churn_risk = 'HIGH' THEN 1 END) as high_risk_count,
    SUM(current_mrr) as total_segment_mrr
  FROM {{ ref('dim_customers') }}
  GROUP BY customer_segment
),

segment_transitions AS (
  -- This would typically compare segments over time
  -- For now, showing current state analysis
  SELECT
    customer_segment,
    customer_count,
    total_segment_mrr,
    ROUND((customer_count::FLOAT / SUM(customer_count) OVER ()) * 100, 2) as pct_of_customers,
    ROUND((total_segment_mrr::FLOAT / SUM(total_segment_mrr) OVER ()) * 100, 2) as pct_of_revenue,
    avg_ltv,
    high_risk_count,
    ROUND((high_risk_count::FLOAT / customer_count) * 100, 2) as pct_high_risk
  FROM customer_segment_performance
)

SELECT
  customer_segment,
  customer_count,
  pct_of_customers || '%' as customer_distribution,
  ' || ROUND(total_segment_mrr, 0) as segment_mrr,
  pct_of_revenue || '%' as revenue_distribution,
  ' || ROUND(avg_ltv, 0) as avg_lifetime_value,
  high_risk_count,
  pct_high_risk || '%' as risk_rate,
  
  -- Strategic recommendations by segment
  CASE 
    WHEN customer_segment = 'CHAMPION' THEN 'Leverage for referrals, upsell opportunities'
    WHEN customer_segment = 'LOYAL' THEN 'Maintain satisfaction, prevent churn'
    WHEN customer_segment = 'AT_RISK' THEN 'Immediate intervention required'
    WHEN customer_segment = 'CANNOT_LOSE' THEN 'Priority retention campaign'
    WHEN customer_segment = 'NEW_CUSTOMER' THEN 'Onboarding optimization'
    ELSE 'Monitor and nurture'
  END as strategic_recommendation

FROM segment_transitions
ORDER BY total_segment_mrr DESC;

