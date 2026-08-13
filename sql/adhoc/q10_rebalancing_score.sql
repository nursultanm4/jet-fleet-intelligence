-- q10: Rebalancing Score — топ зон для перераспределения
-- Стейкхолдер: Ops (полевые команды)
-- Параметры: {target_date}, {market_code}, {limit}
-- Формула: score = (idle_hours_pct × demand_gap) / sqrt(nearby_scooters + 1)

SELECT
    v.city,
    v.zone_name,
    v.zone_type,
    v.center_lat,
    v.center_lon,
    round(v.idle_hours_pct, 4) AS idle_hours_pct,
    v.daily_rides,
    round(v.demand_gap, 2) AS demand_gap,
    round(v.rebalancing_score, 4) AS rebalancing_score,
    multiIf(
        v.rebalancing_score > 0.5, 'Срочно: вывезти самокаты',
        v.rebalancing_score > 0.2, 'Средний приоритет',
        'Низкий приоритет'
    ) AS recommended_action
FROM v_rebalancing_score v
WHERE v.snapshot_date = {target_date:Date}
  AND v.market_id = (SELECT market_id FROM dim_market WHERE country_code = {market_code:String} LIMIT 1)
ORDER BY v.rebalancing_score DESC
LIMIT {limit:UInt32};
