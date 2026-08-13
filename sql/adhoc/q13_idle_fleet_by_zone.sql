-- q13: Простой парка по зонам (idle fleet analysis)
-- Стейкхолдер: Ops
-- Параметры: {target_date}, {market_code}
-- Ожидаемый output: zone idle metrics

SELECT
    z.zone_name,
    z.zone_type,
    i.total_snapshots,
    i.idle_snapshots,
    round(i.idle_hours_pct * 100, 2) AS idle_pct,
    round(i.avg_battery_pct, 1) AS avg_battery_pct
FROM mv_fleet_idle_hours i
JOIN dim_zone z ON i.zone_id = z.zone_id
JOIN dim_market m ON i.market_id = m.market_id
WHERE i.snapshot_date = {target_date:Date}
  AND m.country_code = {market_code:String}
ORDER BY idle_pct DESC
LIMIT 25;
