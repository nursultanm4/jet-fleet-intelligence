-- q05: Пиковые часы по городам
-- Стейкхолдер: Ops
-- Параметры: {date_from}, {date_to}
-- Ожидаемый output: city, hour, ride_count

SELECT
    m.city,
    toHour(r.started_at) AS hour_of_day,
    count() AS ride_count,
    round(sum(r.fare_usd), 2) AS revenue_usd
FROM fact_rides r
JOIN dim_market m ON r.market_id = m.market_id
WHERE r.ride_date BETWEEN {date_from:Date} AND {date_to:Date}
GROUP BY m.city, hour_of_day
ORDER BY m.city, ride_count DESC;
