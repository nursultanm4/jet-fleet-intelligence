-- Staging tables (raw CSV loads)
CREATE TABLE IF NOT EXISTS jet_analytics.stg_rides
(
    ride_id         String,
    user_id         String,
    scooter_id      String,
    market_id       UInt8,
    start_zone_id   UInt16,
    end_zone_id     UInt16,
    started_at      DateTime,
    ended_at        DateTime,
    distance_m      UInt32,
    duration_sec    UInt32,
    fare_local      Float32,
    fare_usd        Float32,
    ride_date       Date
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(ride_date)
ORDER BY (ride_date, ride_id);

CREATE TABLE IF NOT EXISTS jet_analytics.stg_scooter_status
(
    snapshot_at     DateTime,
    scooter_id      String,
    market_id       UInt8,
    zone_id         UInt16,
    lat             Float64,
    lon             Float64,
    battery_pct     UInt8,
    status          LowCardinality(String),
    snapshot_date   Date
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(snapshot_date)
ORDER BY (snapshot_date, scooter_id, snapshot_at);

CREATE TABLE IF NOT EXISTS jet_analytics.stg_maintenance
(
    event_id        String,
    scooter_id      String,
    market_id       UInt8,
    zone_id         UInt16,
    started_at      DateTime,
    ended_at        Nullable(DateTime),
    downtime_hours  Float32,
    issue_type      LowCardinality(String),
    event_date      Date
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_date, event_id);

-- Fact tables (marts)
CREATE TABLE IF NOT EXISTS jet_analytics.fact_rides
(
    ride_id         String,
    user_id         String,
    scooter_id      String,
    market_id       UInt8,
    start_zone_id   UInt16,
    end_zone_id     UInt16,
    started_at      DateTime,
    ended_at        DateTime,
    distance_m      UInt32,
    duration_sec    UInt32,
    fare_local      Float32,
    fare_usd        Float32,
    ride_date       Date
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(ride_date)
ORDER BY (market_id, ride_date, ride_id);

CREATE TABLE IF NOT EXISTS jet_analytics.fact_scooter_status
(
    snapshot_at     DateTime,
    scooter_id      String,
    market_id       UInt8,
    zone_id         UInt16,
    lat             Float64,
    lon             Float64,
    battery_pct     UInt8,
    status          LowCardinality(String),
    snapshot_date   Date
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(snapshot_date)
ORDER BY (market_id, snapshot_date, scooter_id);

CREATE TABLE IF NOT EXISTS jet_analytics.fact_maintenance
(
    event_id        String,
    scooter_id      String,
    market_id       UInt8,
    zone_id         UInt16,
    started_at      DateTime,
    ended_at        Nullable(DateTime),
    downtime_hours  Float32,
    issue_type      LowCardinality(String),
    event_date      Date
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (market_id, event_date, event_id);

-- Anomaly log
CREATE TABLE IF NOT EXISTS jet_analytics.anomaly_log
(
    detected_at     DateTime DEFAULT now(),
    anomaly_date    Date,
    market_id       UInt8,
    zone_id         Nullable(UInt16),
    anomaly_type    LowCardinality(String),
    metric_name     String,
    metric_value    Float64,
    baseline_value  Float64,
    z_score         Float64,
    severity        LowCardinality(String),
    details         String
)
ENGINE = MergeTree()
ORDER BY (anomaly_date, market_id, anomaly_type);
