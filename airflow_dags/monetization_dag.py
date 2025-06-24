from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

default_args = {
    'owner': 'hubspot_analytics',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    'monetization_pipeline',
    default_args=default_args,
    description='Daily pipeline for monetization analytics',
    schedule_interval='@daily',
    start_date=days_ago(1),
    catchup=False,
    tags=['monetization', 'pricing', 'ltv'],
) as dag:

    extract_data = BashOperator(
        task_id='extract_data',
        bash_command='echo "Simulating data pull from source systems..."'
    )

    run_dbt = BashOperator(
        task_id='run_dbt',
        bash_command='cd /path/to/dbt_models && dbt run'
    )

    refresh_dashboard = BashOperator(
        task_id='refresh_dashboard',
        bash_command='echo "Simulating Streamlit dashboard refresh..."'
    )

    extract_data >> run_dbt >> refresh_dashboard
