-- Test to ensure customer health scores are within expected bounds

SELECT customer_id, customer_health_score
FROM {{ ref('dim_customers') }}
WHERE customer_health_score < 0 
   OR customer_health_score > 100
   OR customer_health_score IS NULL

---