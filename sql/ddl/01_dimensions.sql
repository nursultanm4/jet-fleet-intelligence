-- Jet Fleet Intelligence: database and dimensions
CREATE DATABASE IF NOT EXISTS jet_analytics;

-- Markets (6 countries)
CREATE TABLE IF NOT EXISTS jet_analytics.dim_market
(
    market_id       UInt8,
    country_code    LowCardinality(String),
    city            String,
    currency        LowCardinality(String),
    timezone        LowCardinality(String),
    fleet_size_target UInt16,
    base_fare_local Float32,
    per_minute_local Float32
)
ENGINE = MergeTree()
ORDER BY market_id;

-- Geofence zones
CREATE TABLE IF NOT EXISTS jet_analytics.dim_zone
(
    zone_id         UInt16,
    geofence_id     String,
    market_id       UInt8,
    zone_name       String,
    zone_type       LowCardinality(String),
    center_lat      Float64,
    center_lon      Float64
)
ENGINE = MergeTree()
ORDER BY (market_id, zone_id);

-- Scooters
CREATE TABLE IF NOT EXISTS jet_analytics.dim_scooter
(
    scooter_id      String,
    market_id       UInt8,
    model           LowCardinality(String),
    battery_capacity UInt16,
    deploy_date     Date
)
ENGINE = MergeTree()
ORDER BY (market_id, scooter_id);

-- Users (hashed IDs)
CREATE TABLE IF NOT EXISTS jet_analytics.dim_user
(
    user_id         String,
    market_id       UInt8,
    segment         LowCardinality(String),
    first_ride_date Date,
    last_ride_date  Date
)
ENGINE = MergeTree()
ORDER BY (market_id, user_id);
