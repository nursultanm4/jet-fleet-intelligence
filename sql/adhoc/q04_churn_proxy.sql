-- q04: Churn proxy — пользователи без поездок 14+ дней
-- Стейкхолдер: Growth
-- Параметры: {as_of_date}, {market_code}
-- Ожидаемый output: segment, user_count, pct_of_base

WITH last_ride AS (
    SELECT
        user_id,
        market_id,
        max(ride_date) AS last_ride_date
    FROM fact_rides
    GROUP BY user_id, market_id
)
SELECT
    u.segment,
    count() AS user_count,
    round(count() * 100.0 / sum(count()) OVER (), 2) AS pct_of_base,
    round(avg(dateDiff('day', lr.last_ride_date, {as_of_date:Date})), 1) AS avg_days_since_last_ride
FROM dim_user u
JOIN last_ride lr ON u.user_id = lr.user_id
JOIN dim_market m ON u.market_id = m.market_id
WHERE m.country_code = {market_code:String}
  AND dateDiff('day', lr.last_ride_date, {as_of_date:Date}) >= 14
GROUP BY u.segment
ORDER BY user_count DESC;
