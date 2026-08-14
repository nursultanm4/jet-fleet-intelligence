from __future__ import annotations

import logging
from datetime import date, timedelta

from src.clickhouse.client import get_client

logger = logging.getLogger(__name__)

Z_THRESHOLD = 2.0


def _z_score(current: float, baseline_mean: float, baseline_std: float) -> float:
    if baseline_std == 0:
        return 0.0
    return (current - baseline_mean) / baseline_std


def detect_market_anomalies(target_date: date | None = None, lookback: int = 14) -> list[dict]:
    """Detect revenue and ride count anomalies vs rolling baseline."""
    client = get_client()
    target = target_date or (date.today() - timedelta(days=1))
    baseline_start = target - timedelta(days=lookback)

    query = f"""
    WITH daily AS (
        SELECT
            market_id,
            summary_date,
            total_rides,
            total_revenue_usd
        FROM mv_market_daily_summary
        WHERE summary_date BETWEEN toDate('{baseline_start}') AND toDate('{target}')
    ),
    baseline AS (
        SELECT
            market_id,
            avg(total_rides) AS avg_rides,
            stddevPop(total_rides) AS std_rides,
            avg(total_revenue_usd) AS avg_revenue,
            stddevPop(total_revenue_usd) AS std_revenue
        FROM daily
        WHERE summary_date < toDate('{target}')
        GROUP BY market_id
    ),
    current_day AS (
        SELECT market_id, total_rides, total_revenue_usd
        FROM daily
        WHERE summary_date = toDate('{target}')
    )
    SELECT
        c.market_id,
        m.country_code,
        m.city,
        c.total_rides,
        b.avg_rides,
        b.std_rides,
        c.total_revenue_usd,
        b.avg_revenue,
        b.std_revenue
    FROM current_day c
    JOIN baseline b ON c.market_id = b.market_id
    JOIN dim_market m ON c.market_id = m.market_id
    """
    df = client.query_df(query)
    anomalies = []

    for _, row in df.iterrows():
        z_rides = _z_score(row["total_rides"], row["avg_rides"], row["std_rides"])
        z_revenue = _z_score(row["total_revenue_usd"], row["avg_revenue"], row["std_revenue"])

        if z_revenue <= -Z_THRESHOLD:
            anomalies.append(
                {
                    "anomaly_date": target,
                    "market_id": int(row["market_id"]),
                    "zone_id": None,
                    "anomaly_type": "revenue_drop",
                    "metric_name": "total_revenue_usd",
                    "metric_value": float(row["total_revenue_usd"]),
                    "baseline_value": float(row["avg_revenue"]),
                    "z_score": round(z_revenue, 3),
                    "severity": "high" if z_revenue <= -3 else "medium",
                    "details": f"{row['city']}: выручка ниже baseline (z={z_revenue:.2f})",
                }
            )
        if z_rides <= -Z_THRESHOLD:
            anomalies.append(
                {
                    "anomaly_date": target,
                    "market_id": int(row["market_id"]),
                    "zone_id": None,
                    "anomaly_type": "ride_volume_drop",
                    "metric_name": "total_rides",
                    "metric_value": float(row["total_rides"]),
                    "baseline_value": float(row["avg_rides"]),
                    "z_score": round(z_rides, 3),
                    "severity": "high" if z_rides <= -3 else "medium",
                    "details": f"{row['city']}: падение поездок (z={z_rides:.2f})",
                }
            )

    return anomalies


def detect_idle_fleet_anomalies(target_date: date | None = None, lookback: int = 14) -> list[dict]:
    """Detect zones with abnormally high idle fleet."""
    client = get_client()
    target = target_date or (date.today() - timedelta(days=1))
    baseline_start = target - timedelta(days=lookback)

    query = f"""
    WITH zone_daily AS (
        SELECT market_id, zone_id, snapshot_date, idle_hours_pct
        FROM mv_fleet_idle_hours
        WHERE snapshot_date BETWEEN toDate('{baseline_start}') AND toDate('{target}')
    ),
    baseline AS (
        SELECT market_id, zone_id, avg(idle_hours_pct) AS avg_idle, stddevPop(idle_hours_pct) AS std_idle
        FROM zone_daily
        WHERE snapshot_date < toDate('{target}')
        GROUP BY market_id, zone_id
    ),
    current AS (
        SELECT market_id, zone_id, idle_hours_pct
        FROM zone_daily
        WHERE snapshot_date = toDate('{target}')
    )
    SELECT
        c.market_id, c.zone_id, m.city, z.zone_name,
        c.idle_hours_pct, b.avg_idle, b.std_idle
    FROM current c
    JOIN baseline b ON c.market_id = b.market_id AND c.zone_id = b.zone_id
    JOIN dim_market m ON c.market_id = m.market_id
    JOIN dim_zone z ON c.zone_id = z.zone_id
    WHERE b.std_idle > 0
    """
    df = client.query_df(query)
    anomalies = []

    for _, row in df.iterrows():
        z_idle = _z_score(row["idle_hours_pct"], row["avg_idle"], row["std_idle"])
        if z_idle >= Z_THRESHOLD:
            anomalies.append(
                {
                    "anomaly_date": target,
                    "market_id": int(row["market_id"]),
                    "zone_id": int(row["zone_id"]),
                    "anomaly_type": "idle_fleet",
                    "metric_name": "idle_hours_pct",
                    "metric_value": float(row["idle_hours_pct"]),
                    "baseline_value": float(row["avg_idle"]),
                    "z_score": round(z_idle, 3),
                    "severity": "high" if z_idle >= 3 else "medium",
                    "details": f"{row['city']} / {row['zone_name']}: простой парка +{(row['idle_hours_pct']-row['avg_idle'])*100:.1f}pp",
                }
            )
    return anomalies


def detect_maintenance_spikes(target_date: date | None = None, lookback: int = 14) -> list[dict]:
    client = get_client()
    target = target_date or (date.today() - timedelta(days=1))
    baseline_start = target - timedelta(days=lookback)

    query = f"""
    WITH daily AS (
        SELECT market_id, event_date, count() AS events, sum(downtime_hours) AS hours
        FROM fact_maintenance
        WHERE event_date BETWEEN toDate('{baseline_start}') AND toDate('{target}')
        GROUP BY market_id, event_date
    ),
    baseline AS (
        SELECT market_id, avg(events) AS avg_events, stddevPop(events) AS std_events
        FROM daily WHERE event_date < toDate('{target}')
        GROUP BY market_id
    ),
    current AS (
        SELECT market_id, events FROM daily WHERE event_date = toDate('{target}')
    )
    SELECT c.market_id, m.city, c.events, b.avg_events, b.std_events
    FROM current c
    JOIN baseline b ON c.market_id = b.market_id
    JOIN dim_market m ON c.market_id = m.market_id
    WHERE b.std_events > 0
    """
    df = client.query_df(query)
    anomalies = []
    for _, row in df.iterrows():
        z = _z_score(row["events"], row["avg_events"], row["std_events"])
        if z >= Z_THRESHOLD:
            anomalies.append(
                {
                    "anomaly_date": target,
                    "market_id": int(row["market_id"]),
                    "zone_id": None,
                    "anomaly_type": "maintenance_spike",
                    "metric_name": "maintenance_events",
                    "metric_value": float(row["events"]),
                    "baseline_value": float(row["avg_events"]),
                    "z_score": round(z, 3),
                    "severity": "high" if z >= 3 else "medium",
                    "details": f"{row['city']}: всплеск ремонтов ({row['events']} vs avg {row['avg_events']:.1f})",
                }
            )
    return anomalies


def persist_anomalies(anomalies: list[dict]) -> int:
    if not anomalies:
        return 0
    client = get_client()
    import pandas as pd

    df = pd.DataFrame(anomalies)
    client.insert_df("anomaly_log", df)
    logger.info("Persisted %d anomalies", len(anomalies))
    return len(anomalies)


def run_detection(target_date: date | None = None) -> list[dict]:
    all_anomalies = []
    all_anomalies.extend(detect_market_anomalies(target_date))
    all_anomalies.extend(detect_idle_fleet_anomalies(target_date))
    all_anomalies.extend(detect_maintenance_spikes(target_date))
    persist_anomalies(all_anomalies)
    return all_anomalies
