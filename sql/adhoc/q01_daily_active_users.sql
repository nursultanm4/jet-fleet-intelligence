-- q01: DAU по рынкам
-- Стейкхолдер: Growth
-- Параметры: {date_from}, {date_to}
-- Ожидаемый output: market, date, daily_active_users

SELECT
    m.country_code,
    m.city,
    r.ride_date AS activity_date,
    uniqExact(r.user_id) AS daily_active_users
FROM fact_rides r
JOIN dim_market m ON r.market_id = m.market_id
WHERE r.ride_date BETWEEN {date_from:Date} AND {date_to:Date}
GROUP BY m.country_code, m.city, r.ride_date
ORDER BY activity_date, m.country_code;
