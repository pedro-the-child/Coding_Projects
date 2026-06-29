from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator

AIRFLOW_HOME = "/usr/local/airflow"
EXTRACTION_DIR = f"{AIRFLOW_HOME}/extraction"
DBT_DIR = f"{AIRFLOW_HOME}/dbt/oura_project"
DBT_PROFILES_DIR = f"{AIRFLOW_HOME}/include/dbt_profiles"

default_args = {
    "owner": "pedro",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="oura_pipeline",
    description="Extract Oura data → BigQuery → dbt build",
    schedule="0 6 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["oura", "health"],
) as dag:

    extract_oura = BashOperator(
        task_id="extract_oura",
        bash_command=f"cd {EXTRACTION_DIR} && python oura_source.py",
        env={
            "OURA_CLIENT_ID": "{{ var.value.OURA_CLIENT_ID }}",
            "OURA_CLIENT_SECRET": "{{ var.value.OURA_CLIENT_SECRET }}",
            "GCP_PROJECT_ID": "{{ var.value.GCP_PROJECT_ID }}",
            "OURA_RAW_DATASET": "oura_raw",
            "DLT_DESTINATION": "bigquery",
            "HOME": "/home/astro",
            "GOOGLE_APPLICATION_CREDENTIALS": (
                f"{AIRFLOW_HOME}/include/gcloud/application_default_credentials.json"
            ),
        },
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=(
            f"cd {DBT_DIR} && "
            f"dbt build --profiles-dir {DBT_PROFILES_DIR}"
        ),
        env={
            "HOME": "/home/astro",
            "GOOGLE_APPLICATION_CREDENTIALS": (
                f"{AIRFLOW_HOME}/include/gcloud/application_default_credentials.json"
            ),
        },
    )

    extract_oura >> dbt_build
