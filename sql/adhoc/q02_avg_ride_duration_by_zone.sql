-- q02: Средняя длительность поездок по зонам
-- Стейкхолдер: Ops
-- Параметры: {market_code}, {date_from}, {date_to}
-- Ожидаемый output: zone, avg_duration_min, ride_count

SELECT
    z.zone_name,
    z.zone_type,
    count() AS ride_count,
    round(avg(r.duration_sec) / 60, 2) AS avg_duration_min,
    round(avg(r.distance_m), 0) AS avg_distance_m
FROM fact_rides r
JOIN dim_zone z ON r.start_zone_id = z.zone_id
JOIN dim_market m ON r.market_id = m.market_id
WHERE m.country_code = {market_code:String}
  AND r.ride_date BETWEEN {date_from:Date} AND {date_to:Date}
GROUP BY z.zone_name, z.zone_type
ORDER BY avg_duration_min ASC
LIMIT 30;
