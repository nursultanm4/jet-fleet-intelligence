-- q08: Топ зон по выручке
-- Стейкхолдер: Finance
-- Параметры: {market_code}, {date_from}, {date_to}, {limit}
-- Ожидаемый output: zone ranking by revenue

SELECT
    z.zone_name,
    z.zone_type,
    count() AS rides,
    round(sum(r.fare_usd), 2) AS revenue_usd,
    round(avg(r.fare_usd), 4) AS avg_fare_usd
FROM fact_rides r
JOIN dim_zone z ON r.start_zone_id = z.zone_id
JOIN dim_market m ON r.market_id = m.market_id
WHERE m.country_code = {market_code:String}
  AND r.ride_date BETWEEN {date_from:Date} AND {date_to:Date}
GROUP BY z.zone_name, z.zone_type
ORDER BY revenue_usd DESC
LIMIT {limit:UInt32};
