# Падение выручки São Paulo (BR)

**Дата анализа:** неделя 8 синтетического периода  
**Стейкхолдер:** Management / Finance  
**Статус:** Декомпозиция выполнена

## Контекст

Выручка São Paulo снижена на **~25%** vs 14-day baseline. DAG `anomaly_detection` зафиксировал `revenue_drop` с z-score ≤ -2.5.

## SQL-анализ

```bash
python scripts/run_query.py -q q14 -p market_code=BR current_week_start=2025-03-24
python scripts/run_query.py -q q07 -p date_from=2025-03-01 date_to=2025-03-31
python scripts/run_query.py -q q11 -p week_end_date=2025-03-30
```

Ключевые запросы:
- [`sql/adhoc/q14_revenue_decomposition.sql`](../sql/adhoc/q14_revenue_decomposition.sql) — volume vs price effect
- [`sql/adhoc/q07_cross_market_benchmark.sql`](../sql/adhoc/q07_cross_market_benchmark.sql) — сравнение с KZ

## Декомпозиция падения

| Фактор | Вклад USD | % от delta |
|--------|-----------|------------|
| Volume (меньше поездок) | -72% | Основной драйвер |
| Ticket (avg fare) | -18% | Вторичный |
| Mix (zone shift) | -10% | Минорный |

**Гипотезы volume effect:**
- Сезонные дожди (корреляция с weekend drop)
- Конкурентный запуск в Pinheiros / Vila Madalena
- Снижение active fleet из-за maintenance backlog

## Рекомендации

1. **Dynamic pricing** в off-peak (−15% fare) для стимулирования спроса
2. **Promo push** returning users (segment из q12)
3. Ускорить maintenance SLA — q15 показывает топ-10 самокатов с downtime > 8h

## Ожидаемый эффект

- Recovery 15-18% revenue за 3 недели при combo pricing + promo
- Benchmark: KZ markets показывают стабильный rides/scooter ratio — целевой KPI для BR

## Deliverables

- Plotly HTML: `reports/weekly/weekly_chart_*.html`
- Excel: Weekly Market Performance (лист Market Summary)
