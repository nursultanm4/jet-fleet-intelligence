-- q09: Utilization rate по рынкам
-- Стейкхолдер: Ops
-- Параметры: {date_from}, {date_to}
-- Ожидаемый output: market daily utilization

SELECT
    m.country_code,
    m.city,
    k.kpi_date,
    sum(k.ride_count) AS rides,
    round(avg(k.utilization_rate), 4) AS avg_utilization_rate,
    round(sum(k.revenue_usd), 2) AS revenue_usd
FROM mv_daily_zone_kpi k
JOIN dim_market m ON k.market_id = m.market_id
WHERE k.kpi_date BETWEEN {date_from:Date} AND {date_to:Date}
GROUP BY m.country_code, m.city, k.kpi_date
ORDER BY k.kpi_date, m.country_code;
