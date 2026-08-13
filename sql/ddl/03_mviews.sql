-- Daily zone KPIs
CREATE TABLE IF NOT EXISTS jet_analytics.mv_daily_zone_kpi
(
    kpi_date        Date,
    market_id       UInt8,
    zone_id         UInt16,
    ride_count      UInt32,
    revenue_usd     Float64,
    avg_duration_sec Float64,
    avg_distance_m  Float64,
    unique_users    UInt32,
    utilization_rate Float64
)
ENGINE = SummingMergeTree()
ORDER BY (kpi_date, market_id, zone_id);

CREATE MATERIALIZED VIEW IF NOT EXISTS jet_analytics.mv_daily_zone_kpi_mv
TO jet_analytics.mv_daily_zone_kpi
AS
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
FROM jet_analytics.fact_rides
GROUP BY kpi_date, market_id, zone_id;

-- Fleet idle hours by zone (hourly snapshots)
CREATE TABLE IF NOT EXISTS jet_analytics.mv_fleet_idle_hours
(
    snapshot_date   Date,
    market_id       UInt8,
    zone_id         UInt16,
    total_snapshots UInt32,
    idle_snapshots  UInt32,
    idle_hours_pct  Float64,
    avg_battery_pct Float64
)
ENGINE = SummingMergeTree()
ORDER BY (snapshot_date, market_id, zone_id);

CREATE MATERIALIZED VIEW IF NOT EXISTS jet_analytics.mv_fleet_idle_hours_mv
TO jet_analytics.mv_fleet_idle_hours
AS
SELECT
    snapshot_date,
    market_id,
    zone_id,
    count() AS total_snapshots,
    countIf(status = 'available') AS idle_snapshots,
    countIf(status = 'available') / count() AS idle_hours_pct,
    avg(battery_pct) AS avg_battery_pct
FROM jet_analytics.fact_scooter_status
GROUP BY snapshot_date, market_id, zone_id;

-- Market daily summary for Excel reports
CREATE TABLE IF NOT EXISTS jet_analytics.mv_market_daily_summary
(
    summary_date    Date,
    market_id       UInt8,
    total_rides     UInt32,
    total_revenue_usd Float64,
    active_users    UInt32,
    active_scooters UInt32,
    avg_ride_duration_sec Float64,
    maintenance_events UInt32,
    maintenance_downtime_hours Float64
)
ENGINE = SummingMergeTree()
ORDER BY (summary_date, market_id);

CREATE MATERIALIZED VIEW IF NOT EXISTS jet_analytics.mv_market_daily_summary_rides_mv
TO jet_analytics.mv_market_daily_summary
AS
SELECT
    ride_date AS summary_date,
    market_id,
    count() AS total_rides,
    sum(fare_usd) AS total_revenue_usd,
    uniqExact(user_id) AS active_users,
    uniqExact(scooter_id) AS active_scooters,
    avg(duration_sec) AS avg_ride_duration_sec,
    0 AS maintenance_events,
    0 AS maintenance_downtime_hours
FROM jet_analytics.fact_rides
GROUP BY summary_date, market_id;

-- Rebalancing score view (JOIN-based for ClickHouse 24.x)
DROP VIEW IF EXISTS jet_analytics.v_rebalancing_score;

CREATE VIEW jet_analytics.v_rebalancing_score AS
SELECT
    i.snapshot_date AS snapshot_date,
    i.market_id AS market_id,
    m.city AS city,
    i.zone_id AS zone_id,
    z.zone_name AS zone_name,
    z.zone_type AS zone_type,
    z.center_lat AS center_lat,
    z.center_lon AS center_lon,
    i.idle_hours_pct AS idle_hours_pct,
    coalesce(k.ride_count, 0) AS daily_rides,
    greatest(toFloat64(coalesce(peak.max_rides, 0) - coalesce(k.ride_count, 0)), 0.) AS demand_gap,
    (i.idle_hours_pct * greatest(toFloat64(coalesce(peak.max_rides, 0) - coalesce(k.ride_count, 0)), 0.1))
        / sqrt(i.total_snapshots + 1) AS rebalancing_score
FROM jet_analytics.mv_fleet_idle_hours i
JOIN jet_analytics.dim_zone z ON i.zone_id = z.zone_id
JOIN jet_analytics.dim_market m ON i.market_id = m.market_id
LEFT JOIN jet_analytics.mv_daily_zone_kpi k
    ON i.snapshot_date = k.kpi_date AND i.market_id = k.market_id AND i.zone_id = k.zone_id
LEFT JOIN (
    SELECT kpi_date, market_id, max(ride_count) AS max_rides
    FROM jet_analytics.mv_daily_zone_kpi
    GROUP BY kpi_date, market_id
) AS peak ON i.snapshot_date = peak.kpi_date AND i.market_id = peak.market_id;
