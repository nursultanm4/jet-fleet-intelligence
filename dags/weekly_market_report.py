"""Airflow DAG: weekly Excel + Plotly market report."""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "jet_analytics",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}


def _build_excel():
    from src.excel.report_builder import build_weekly_market_report
    path = build_weekly_market_report()
    print(f"Weekly report: {path}")


def _build_rebalancing():
    from src.excel.report_builder import build_rebalancing_sheet
    for code in ("UZ", "BR", "KZ"):
        path = build_rebalancing_sheet(code)
        print(f"Rebalancing sheet: {path}")


def _build_html():
    from src.excel.report_builder import build_plotly_html
    path = build_plotly_html()
    print(f"Plotly HTML: {path}")


with DAG(
    dag_id="weekly_market_report",
    default_args=default_args,
    description="Еженедельный Excel-отчёт и визуализация по рынкам",
    schedule_interval="0 8 * * 1",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["jet", "excel", "report"],
) as dag:
    excel_task = PythonOperator(task_id="build_weekly_excel", python_callable=_build_excel)
    rebalancing_task = PythonOperator(task_id="build_rebalancing_sheets", python_callable=_build_rebalancing)
    html_task = PythonOperator(task_id="build_plotly_html", python_callable=_build_html)

    excel_task >> rebalancing_task >> html_task
