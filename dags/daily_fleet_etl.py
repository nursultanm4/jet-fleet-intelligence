"""Airflow DAG: daily fleet ETL pipeline."""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "jet_analytics",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def _validate():
    from src.etl.pipeline import validate_raw_files
    validate_raw_files()


def _load_staging():
    from src.etl.pipeline import load_staging
    load_staging()


def _load_dims():
    from src.etl.pipeline import load_dimensions
    load_dimensions()


def _transform():
    from src.etl.pipeline import transform_to_marts
    transform_to_marts()


def _refresh():
    from src.etl.pipeline import refresh_aggregates
    refresh_aggregates()


def _dq():
    from src.etl.pipeline import data_quality_checks
    issues = data_quality_checks()
    if issues:
        raise ValueError(f"Data quality failed: {issues}")


with DAG(
    dag_id="daily_fleet_etl",
    default_args=default_args,
    description="Ежедневный ETL: raw CSV → ClickHouse marts",
    schedule_interval="0 6 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["jet", "etl", "clickhouse"],
) as dag:
    validate_task = PythonOperator(
        task_id="validate_raw_files",
        python_callable=_validate,
    )
    load_dims_task = PythonOperator(
        task_id="load_dimensions",
        python_callable=_load_dims,
    )
    load_staging_task = PythonOperator(
        task_id="load_staging",
        python_callable=_load_staging,
    )
    transform_task = PythonOperator(
        task_id="transform_to_marts",
        python_callable=_transform,
    )
    refresh_task = PythonOperator(
        task_id="refresh_materialized_views",
        python_callable=_refresh,
    )
    dq_task = PythonOperator(
        task_id="data_quality_checks",
        python_callable=_dq,
    )

    validate_task >> load_dims_task >> load_staging_task >> transform_task >> refresh_task >> dq_task
