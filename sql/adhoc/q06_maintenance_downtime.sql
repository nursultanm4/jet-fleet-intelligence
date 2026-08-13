-- q06: Простой из-за ремонта
-- Стeykholder: Ops
-- Параметры: {date_from}, {date_to}, {market_code}
-- Ожидаемый output: issue_type, events, total_downtime_hours

SELECT
    m.city,
    fm.issue_type,
    count() AS maintenance_events,
    round(sum(fm.downtime_hours), 2) AS total_downtime_hours,
    round(avg(fm.downtime_hours), 2) AS avg_downtime_hours
FROM fact_maintenance fm
JOIN dim_market m ON fm.market_id = m.market_id
WHERE fm.event_date BETWEEN {date_from:Date} AND {date_to:Date}
  AND m.country_code = {market_code:String}
GROUP BY m.city, fm.issue_type
ORDER BY total_downtime_hours DESC;
