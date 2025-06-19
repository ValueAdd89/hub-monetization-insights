{% macro optimize_table() %}
  {% if target.type == 'snowflake' %}
    -- Snowflake-specific optimization
    ALTER TABLE {{ this }} SET AUTO_SUSPEND = 60;
    ANALYZE TABLE {{ this }} COMPUTE STATISTICS;
  {% elif target.type == 'bigquery' %}
    -- BigQuery-specific optimization
    -- Clustering and partitioning handled in model config
  {% elif target.type == 'redshift' %}
    -- Redshift-specific optimization
    ANALYZE {{ this }};
    VACUUM {{ this }};
  {% elif target.type == 'postgres' %}
    -- PostgreSQL-specific optimization
    ANALYZE {{ this }};
    VACUUM ANALYZE {{ this }};
  {% endif %}
{% endmacro %}