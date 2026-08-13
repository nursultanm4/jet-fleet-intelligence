-- q12: Новые vs returning пользователи
-- Стейкхолдер: Growth
-- Параметры: {date_from}, {date_to}, {market_code}
-- Ожидаемый output: segment breakdown of riders

SELECT
    u.segment,
    uniqExact(r.user_id) AS riders,
    count() AS rides,
    round(sum(r.fare_usd), 2) AS revenue_usd,
    round(avg(r.duration_sec) / 60, 2) AS avg_duration_min
FROM fact_rides r
JOIN dim_user u ON r.user_id = u.user_id
JOIN dim_market m ON r.market_id = m.market_id
WHERE r.ride_date BETWEEN {date_from:Date} AND {date_to:Date}
  AND m.country_code = {market_code:String}
GROUP BY u.segment
ORDER BY revenue_usd DESC;
