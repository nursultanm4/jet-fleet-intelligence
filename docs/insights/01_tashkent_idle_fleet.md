# Простой парка в Ташкенте (UZ)

**Дата анализа:** неделя 6 синтетического периода  
**Стейкхолдер:** Ops (Ташкент)  
**Статус:** Root cause установлен, рекомендации готовы

## Контекст

В 6-й неделе наблюдается рост простоя парка на **+40%** в suburb-зонах Ташкента при стабильном спросе в downtown. Метрика `idle_hours_pct` превышает baseline более чем на 2σ (см. DAG `anomaly_detection`, тип `idle_fleet`).

## SQL-анализ

```bash
python scripts/run_query.py -q q13 -p market_code=UZ target_date=2025-03-15
python scripts/run_query.py -q q10 -p market_code=UZ target_date=2025-03-15 limit=20
```

Ключевые запросы:
- [`sql/adhoc/q13_idle_fleet_by_zone.sql`](../sql/adhoc/q13_idle_fleet_by_zone.sql) — зоны с максимальным idle %
- [`sql/adhoc/q10_rebalancing_score.sql`](../sql/adhoc/q10_rebalancing_score.sql) — приоритизация вывоза

## Root cause

1. **Переизбыток самокатов** в 4 suburb-зонах (GF-UZ-03 … GF-UZ-06) после массового deploy
2. **Низкий demand_gap** — пиковый спрос в downtown не компенсирует избыток в periphery
3. Rebalancing Score > 0.5 у 6 зон → «Срочно: вывезти самокаты»

## Рекомендации

| Действие | Зоны | Самокатов к вывозу | Срок |
|----------|------|-------------------|------|
| Вывоз в downtown | Suburb 3-6 | 35-40 | 48 ч |
| Dynamic repositioning | Transit hub 1-2 | 15 | 72 ч |

## Ожидаемый эффект

- Снижение idle rate с 68% → 52% в suburb
- **+12% rides** в downtown за 2 недели
- Uplift выручки ~$800/нед (USD)

## Deliverables

- Excel: `reports/weekly/rebalancing_UZ_*.xlsx` (лист Rebalancing)
- Airflow: `weekly_market_report` → Zone Heatmap UZ
