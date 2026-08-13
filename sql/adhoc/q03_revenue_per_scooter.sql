-- q03: Выручка на самокат (unit economics)
-- Стейкхолдер: Finance
-- Параметры: {date_from}, {date_to}
-- Ожидаемый output: market, revenue_per_scooter_per_day

SELECT
    m.country_code,
    m.city,
    round(sum(r.fare_usd) / uniqExact(r.scooter_id) /
        greatest(dateDiff('day', {date_from:Date}, {date_to:Date}) + 1, 1), 4) AS revenue_per_scooter_per_day,
    uniqExact(r.scooter_id) AS active_scooters,
    count() AS total_rides,
    round(sum(r.fare_usd), 2) AS total_revenue_usd
FROM fact_rides r
JOIN dim_market m ON r.market_id = m.market_id
WHERE r.ride_date BETWEEN {date_from:Date} AND {date_to:Date}
GROUP BY m.country_code, m.city, m.market_id
ORDER BY revenue_per_scooter_per_day DESC;
