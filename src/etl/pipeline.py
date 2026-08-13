from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.clickhouse.client import get_client, insert_dataframe

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

RIDE_COLUMNS = [
    "ride_id", "user_id", "scooter_id", "market_id", "start_zone_id", "end_zone_id",
    "started_at", "ended_at", "distance_m", "duration_sec", "fare_local", "fare_usd", "ride_date",
]
STATUS_COLUMNS = [
    "snapshot_at", "scooter_id", "market_id", "zone_id", "lat", "lon",
    "battery_pct", "status", "snapshot_date",
]
MAINTENANCE_COLUMNS = [
    "event_id", "scooter_id", "market_id", "zone_id", "started_at",
    "ended_at", "downtime_hours", "issue_type", "event_date",
]


def validate_raw_files(raw_dir: Path | None = None) -> dict[str, Path]:
    """Ensure required CSV files exist and have expected columns."""
    raw_dir = raw_dir or RAW_DIR
    required = {
        "rides": RIDE_COLUMNS,
        "scooter_status": STATUS_COLUMNS,
        "maintenance": MAINTENANCE_COLUMNS,
    }
    paths = {}
    for name, columns in required.items():
        path = raw_dir / f"{name}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing raw file: {path}")
        df = pd.read_csv(path, nrows=5)
        missing = set(columns) - set(df.columns)
        if missing:
            raise ValueError(f"{path.name} missing columns: {missing}")
        paths[name] = path
        logger.info("Validated %s (%d columns)", path.name, len(columns))
    return paths


def _parse_dates(df: pd.DataFrame, datetime_cols: list[str], date_cols: list[str]) -> pd.DataFrame:
    for col in datetime_cols:
        df[col] = pd.to_datetime(df[col])
    for col in date_cols:
        df[col] = pd.to_datetime(df[col]).dt.date
    return df


def load_dimensions(raw_dir: Path | None = None) -> None:
    """Load dimension CSVs into ClickHouse (truncate + reload)."""
    raw_dir = raw_dir or RAW_DIR
    client = get_client()

    for table, file in [
        ("dim_zone", "dim_zone.csv"),
        ("dim_scooter", "dim_scooter.csv"),
        ("dim_user", "dim_user.csv"),
    ]:
        path = raw_dir / file
        if not path.exists():
            logger.warning("Skipping %s — file not found", file)
            continue
        df = pd.read_csv(path)
        if table == "dim_user":
            df["first_ride_date"] = pd.to_datetime(df["first_ride_date"]).dt.date
            df["last_ride_date"] = pd.to_datetime(df["last_ride_date"]).dt.date
        if table == "dim_scooter":
            df["deploy_date"] = pd.to_datetime(df["deploy_date"]).dt.date
            df["battery_capacity"] = df["battery_capacity"].astype("uint16")
        client.command(f"TRUNCATE TABLE IF EXISTS {table}")
        insert_dataframe(client, table, df)
        logger.info("Loaded %d rows into %s", len(df), table)


def load_staging(raw_dir: Path | None = None) -> dict[str, int]:
    """Load raw CSVs into staging tables."""
    paths = validate_raw_files(raw_dir)
    client = get_client()
    counts = {}

    rides = pd.read_csv(paths["rides"])
    rides = _parse_dates(rides, ["started_at", "ended_at"], ["ride_date"])
    client.command("TRUNCATE TABLE IF EXISTS stg_rides")
    insert_dataframe(client, "stg_rides", rides)
    counts["stg_rides"] = len(rides)

    status = pd.read_csv(paths["scooter_status"])
    status = _parse_dates(status, ["snapshot_at"], ["snapshot_date"])
    client.command("TRUNCATE TABLE IF EXISTS stg_scooter_status")
    insert_dataframe(client, "stg_scooter_status", status)
    counts["stg_scooter_status"] = len(status)

    maint = pd.read_csv(paths["maintenance"])
    maint = _parse_dates(maint, ["started_at", "ended_at"], ["event_date"])
    client.command("TRUNCATE TABLE IF EXISTS stg_maintenance")
    insert_dataframe(client, "stg_maintenance", maint)
    counts["stg_maintenance"] = len(maint)

    logger.info("Staging load complete: %s", counts)
    return counts


def transform_to_marts() -> None:
    """Copy staging → fact tables (idempotent full refresh for demo)."""
    client = get_client()
    transforms = [
        ("fact_rides", "stg_rides", RIDE_COLUMNS),
        ("fact_scooter_status", "stg_scooter_status", STATUS_COLUMNS),
        ("fact_maintenance", "stg_maintenance", MAINTENANCE_COLUMNS),
    ]
    for fact, staging, cols in transforms:
        client.command(f"TRUNCATE TABLE IF EXISTS {fact}")
        col_list = ", ".join(cols)
        client.command(f"INSERT INTO {fact} ({col_list}) SELECT {col_list} FROM {staging}")
        count = client.command(f"SELECT count() FROM {fact}")
        logger.info("Loaded %s rows into %s", count, fact)


def refresh_aggregates() -> None:
    """Rebuild aggregate tables from facts (MV targets for demo reliability)."""
    client = get_client()
    client.command("TRUNCATE TABLE IF EXISTS mv_daily_zone_kpi")
    client.command(
        """
        INSERT INTO mv_daily_zone_kpi
        SELECT
            ride_date AS kpi_date,
            market_id,
            start_zone_id AS zone_id,
            count() AS ride_count,
            sum(fare_usd) AS revenue_usd,
            avg(duration_sec) AS avg_duration_sec,
            avg(distance_m) AS avg_distance_m,
            uniqExact(user_id) AS unique_users,
            count() / greatest(uniqExact(scooter_id), 1) AS utilization_rate
        FROM fact_rides
        GROUP BY kpi_date, market_id, zone_id
        """
    )
    client.command("TRUNCATE TABLE IF EXISTS mv_fleet_idle_hours")
    client.command(
        """
        INSERT INTO mv_fleet_idle_hours
        SELECT
            snapshot_date,
            market_id,
            zone_id,
            count() AS total_snapshots,
            countIf(status = 'available') AS idle_snapshots,
            countIf(status = 'available') / count() AS idle_hours_pct,
            avg(battery_pct) AS avg_battery_pct
        FROM fact_scooter_status
        GROUP BY snapshot_date, market_id, zone_id
        """
    )
    client.command("TRUNCATE TABLE IF EXISTS mv_market_daily_summary")
    client.command(
        """
        INSERT INTO mv_market_daily_summary
        SELECT
            r.ride_date AS summary_date,
            r.market_id,
            count() AS total_rides,
            sum(r.fare_usd) AS total_revenue_usd,
            uniqExact(r.user_id) AS active_users,
            uniqExact(r.scooter_id) AS active_scooters,
            avg(r.duration_sec) AS avg_ride_duration_sec,
            coalesce(m.cnt, 0) AS maintenance_events,
            coalesce(m.hours, 0) AS maintenance_downtime_hours
        FROM fact_rides r
        LEFT JOIN (
            SELECT market_id, event_date, count() AS cnt, sum(downtime_hours) AS hours
            FROM fact_maintenance
            GROUP BY market_id, event_date
        ) m ON r.market_id = m.market_id AND r.ride_date = m.event_date
        GROUP BY r.ride_date, r.market_id, m.cnt, m.hours
        """
    )
    logger.info("Aggregate tables refreshed.")


def data_quality_checks() -> list[str]:
    """Run basic DQ checks; return list of issues."""
    client = get_client()
    issues = []

    dup_rides = client.command(
        "SELECT count() - uniqExact(ride_id) FROM fact_rides"
    )
    if dup_rides > 0:
        issues.append(f"Duplicate ride_ids: {dup_rides}")

    null_fares = client.command(
        "SELECT countIf(fare_usd IS NULL OR fare_usd = 0) FROM fact_rides"
    )
    if null_fares > 0:
        issues.append(f"Null/zero fares: {null_fares}")

    for table in ["fact_rides", "fact_scooter_status", "fact_maintenance"]:
        cnt = client.command(f"SELECT count() FROM {table}")
        if cnt == 0:
            issues.append(f"Empty table: {table}")
        logger.info("%s row count: %s", table, cnt)

    if issues:
        logger.warning("DQ issues: %s", issues)
    else:
        logger.info("All data quality checks passed.")
    return issues


def run_full_etl(raw_dir: Path | None = None) -> None:
    """Execute complete ETL pipeline."""
    load_dimensions(raw_dir)
    load_staging(raw_dir)
    transform_to_marts()
    refresh_aggregates()
    data_quality_checks()
