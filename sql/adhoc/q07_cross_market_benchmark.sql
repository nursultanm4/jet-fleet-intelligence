-- q07: Кросс-рыночный бенчмарк KZ vs BR
-- Стейкхолдер: Management
-- Параметры: {date_from}, {date_to}
-- Ожидаемый output: market metrics side-by-side

SELECT
    m.country_code,
    m.city,
    count() AS total_rides,
    round(sum(r.fare_usd), 2) AS revenue_usd,
    round(avg(r.duration_sec) / 60, 2) AS avg_duration_min,
    round(avg(r.distance_m), 0) AS avg_distance_m,
    uniqExact(r.user_id) AS unique_users,
    round(count() / uniqExact(r.scooter_id), 2) AS rides_per_scooter
FROM fact_rides r
JOIN dim_market m ON r.market_id = m.market_id
WHERE r.ride_date BETWEEN {date_from:Date} AND {date_to:Date}
  AND m.country_code IN ('KZ', 'BR')
GROUP BY m.country_code, m.city
ORDER BY m.country_code, revenue_usd DESC;
