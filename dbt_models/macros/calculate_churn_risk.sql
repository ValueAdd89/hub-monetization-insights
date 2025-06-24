{% macro calculate_churn_risk(days_since_activity, health_score, satisfaction_score) %}
  CASE 
    WHEN {{ days_since_activity }} > 90 THEN 'HIGH'
    WHEN {{ days_since_activity }} > 30 AND {{ health_score }} < 40 THEN 'HIGH'
    WHEN {{ health_score }} < 30 THEN 'HIGH'
    WHEN {{ days_since_activity }} > 14 AND {{ health_score }} < 60 THEN 'MEDIUM'
    WHEN {{ satisfaction_score }} < 3 THEN 'MEDIUM'
    ELSE 'LOW'
  END
{% endmacro %}