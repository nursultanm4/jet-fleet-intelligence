-- q15: Самокаты с наибольшим простоем (maintenance + idle)
-- Стейкхолдер: Ops
-- Параметры: {date_from}, {date_to}, {market_code}, {limit}
-- Ожидаемый output: scooter_id, downtime, idle_pct

SELECT
    s.scooter_id,
    s.model,
    coalesce(maint.total_downtime, 0) AS maintenance_downtime_hours,
    coalesce(idle.idle_pct, 0) AS avg_idle_pct,
    coalesce(rides.ride_count, 0) AS ride_count
FROM dim_scooter s
LEFT JOIN (
    SELECT scooter_id, sum(downtime_hours) AS total_downtime
    FROM fact_maintenance
    WHERE event_date BETWEEN {date_from:Date} AND {date_to:Date}
    GROUP BY scooter_id
) maint ON s.scooter_id = maint.scooter_id
LEFT JOIN (
    SELECT scooter_id, avgIf(1, status = 'available') AS idle_pct
    FROM fact_scooter_status
    WHERE snapshot_date BETWEEN {date_from:Date} AND {date_to:Date}
    GROUP BY scooter_id
) idle ON s.scooter_id = idle.scooter_id
LEFT JOIN (
    SELECT scooter_id, count() AS ride_count
    FROM fact_rides
    WHERE ride_date BETWEEN {date_from:Date} AND {date_to:Date}
    GROUP BY scooter_id
) rides ON s.scooter_id = rides.scooter_id
JOIN dim_market m ON s.market_id = m.market_id
WHERE m.country_code = {market_code:String}
ORDER BY maintenance_downtime_hours DESC, avg_idle_pct DESC
LIMIT {limit:UInt32};
