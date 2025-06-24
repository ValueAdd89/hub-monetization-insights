SELECT
  hub,
  tier,
  price_usd,
  seats_included
FROM {{ source('raw', 'pricing_plans') }}
