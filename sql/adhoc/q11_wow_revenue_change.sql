-- q11: WoW изменение выручки по рынкам
-- Стейкхолдер: Management
-- Параметры: {week_end_date}
-- Ожидаемый output: market, current_week_revenue, prev_week_revenue, wow_pct

WITH weekly AS (
    SELECT
        market_id,
        toMonday(ride_date) AS week_start,
        sum(fare_usd) AS revenue_usd
    FROM fact_rides
    GROUP BY market_id, week_start
)
SELECT
    m.country_code,
    m.city,
    round(c.revenue_usd, 2) AS current_week_revenue,
    round(p.revenue_usd, 2) AS prev_week_revenue,
    round((c.revenue_usd - p.revenue_usd) / greatest(p.revenue_usd, 0.01) * 100, 2) AS wow_pct
FROM weekly c
JOIN weekly p ON c.market_id = p.market_id
    AND p.week_start = c.week_start - 7
JOIN dim_market m ON c.market_id = m.market_id
WHERE c.week_start = toMonday({week_end_date:Date})
ORDER BY wow_pct ASC;
