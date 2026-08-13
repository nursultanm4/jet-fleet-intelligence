-- q14: Декомпозиция падения выручки (volume vs ticket)
-- Стейкхолдер: Finance
-- Параметры: {market_code}, {current_week_start}, {prev_week_start}
-- Ожидаемый output: volume_effect, price_effect

WITH period AS (
    SELECT
        toMonday(ride_date) AS week_start,
        count() AS rides,
        sum(fare_usd) AS revenue,
        avg(fare_usd) AS avg_ticket
    FROM fact_rides r
    JOIN dim_market m ON r.market_id = m.market_id
    WHERE m.country_code = {market_code:String}
    GROUP BY week_start
)
SELECT
    c.week_start AS current_week,
    round(c.revenue, 2) AS current_revenue,
    round(p.revenue, 2) AS prev_revenue,
    round(c.revenue - p.revenue, 2) AS revenue_delta,
    round((c.rides - p.rides) * p.avg_ticket, 2) AS volume_effect_usd,
    round((c.avg_ticket - p.avg_ticket) * c.rides, 2) AS price_effect_usd,
    c.rides AS current_rides,
    p.rides AS prev_rides
FROM period c
JOIN period p ON p.week_start = c.week_start - 7
WHERE c.week_start = {current_week_start:Date};
