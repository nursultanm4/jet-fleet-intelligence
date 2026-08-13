-- KPI: utilization by market (analytics layer)
SELECT
    m.country_code,
    m.city,
    round(avg(s.total_rides), 0) AS avg_daily_rides,
    round(avg(s.total_revenue_usd), 2) AS avg_daily_revenue_usd,
    round(avg(s.active_users), 0) AS avg_dau
FROM mv_market_daily_summary s
JOIN dim_market m ON s.market_id = m.market_id
WHERE s.summary_date >= today() - 30
GROUP BY m.country_code, m.city
ORDER BY avg_daily_revenue_usd DESC;
