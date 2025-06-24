{% snapshot customers_snapshot %}
    {{
        config(
          target_schema='snapshots',
          unique_key='customer_id',
          strategy='timestamp',
          updated_at='updated_at',
        )
    }}
    
    SELECT 
        customer_id,
        company_name,
        industry,
        company_size,
        country,
        state,
        email,
        signup_date,
        updated_at
    FROM {{ source('raw', 'customers') }}
    
{% endsnapshot %}