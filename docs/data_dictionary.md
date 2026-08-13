# Словарь данных - Jet Fleet Intelligence

## dim_market

| Поле | Тип | Описание |
|------|-----|----------|
| market_id | UInt8 | PK рынка |
| country_code | String | ISO код (KZ, UZ, BR…) |
| city | String | Город операции |
| currency | String | Локальная валюта |
| fleet_size_target | UInt16 | Целевой размер парка |
| base_fare_local | Float32 | Базовый тариф |
| per_minute_local | Float32 | Тариф за минуту |

## dim_zone

| Поле | Тип | Описание |
|------|-----|----------|
| zone_id | UInt16 | PK зоны |
| geofence_id | String | ID геозоны |
| zone_type | String | downtown / suburb / university / transit_hub |
| center_lat, center_lon | Float64 | Центр зоны |

## fact_rides

| Поле | Тип | Описание |
|------|-----|----------|
| ride_id | String | Уникальный ID поездки |
| duration_sec | UInt32 | Длительность поездки |
| fare_usd | Float32 | Выручка в USD |
| ride_date | Date | Дата (partition key) |

## mv_daily_zone_kpi

Агрегат KPI по зонам и дням: rides, revenue, utilization_rate.

## mv_fleet_idle_hours

Почасовые snapshot'ы → idle_hours_pct по зонам. Основа Rebalancing Score.

## mv_market_daily_summary

Сводка для Excel weekly report: rides, revenue, DAU, maintenance.

## v_rebalancing_score

View с формулой приоритизации rebalancing (см. insights/03).

## anomaly_log

Автоматически заполняется DAG `anomaly_detection`: тип, z-score, severity.

## Бизнес-метрики

| Метрика | Формула |
|---------|---------|
| Utilization rate | rides / active_scooters |
| Revenue/scooter/day | sum(fare_usd) / uniq(scooters) / days |
| Idle rate | idle_snapshots / total_snapshots |
| Rebalancing Score | (idle_pct × demand_gap) / sqrt(n+1) |
| Churn proxy | users без поездок 14+ дней |
