"""Airflow DAG: daily anomaly detection."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "jet_analytics",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

INSIGHTS_LOG = Path("/opt/jet_analytics/docs/insights/anomaly_log.md")


def _detect():
    from src.etl.anomaly import run_detection
    anomalies = run_detection()
    print(f"Detected {len(anomalies)} anomalies")
    if anomalies:
        _append_log(anomalies)


def _append_log(anomalies: list[dict]) -> None:
    """Append high-severity anomalies to markdown log."""
    log_path = INSIGHTS_LOG
    if not log_path.parent.exists():
        log_path = Path(__file__).resolve().parents[1] / "docs" / "insights" / "anomaly_log.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    if not log_path.exists():
        lines.append("# Журнал аномалий (автоматический)\n\n")

    for a in anomalies:
        if a["severity"] == "high":
            lines.append(
                f"- **{a['anomaly_date']}** | {a['anomaly_type']} | "
                f"market={a['market_id']} | z={a['z_score']} | {a['details']}\n"
            )
    if lines:
        with open(log_path, "a", encoding="utf-8") as f:
            f.writelines(lines)


with DAG(
    dag_id="anomaly_detection",
    default_args=default_args,
    description="Ежедневное обнаружение аномалий fleet/revenue/maintenance",
    schedule_interval="0 7 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["jet", "anomaly", "adhoc"],
) as dag:
    detect_task = PythonOperator(task_id="detect_anomalies", python_callable=_detect)
