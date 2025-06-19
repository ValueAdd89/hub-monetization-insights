-- Test to ensure LTV calculations are reasonable

SELECT 
    customer_id,
    estimated_ltv,
    current_mrr,
    months_since_first_subscription
FROM {{ ref('dim_customers') }}
WHERE estimated_ltv > current_mrr * 120  -- LTV shouldn't exceed 10 years of current MRR
   OR (estimated_ltv > 0 AND current_mrr = 0 AND months_since_first_subscription < 1)

---