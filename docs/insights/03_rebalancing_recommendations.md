# Приоритизация rebalancing — ops playbook

**Дата:** актуально на последний snapshot  
**Стейкхолдер:** Ops (полевые команды)  
**Статус:** Еженедельный процесс

## Rebalancing Score

Метрика приоритизации перераспределения самокатов:

```
score = (idle_hours_pct × demand_gap) / sqrt(total_snapshots + 1)
```

- `idle_hours_pct` — доля snapshot'ов со status=`available`
- `demand_gap` — разница между max rides/zone и текущими rides в зоне

Реализация: view `v_rebalancing_score` в ClickHouse, см. [`sql/ddl/03_mviews.sql`](../sql/ddl/03_mviews.sql)

## SQL и Excel workflow

```bash
# Топ-20 зон UZ
python scripts/run_query.py -q q10 -p market_code=UZ limit=20

# Генерация ops-листа
make report
# → reports/weekly/rebalancing_UZ_*.xlsx
```

## Матрица действий

| Score | Действие | SLA |
|-------|----------|-----|
| > 0.5 | Срочно: вывезти самокаты | 24 ч |
| 0.2 – 0.5 | Средний приоритет: reposition | 72 ч |
| < 0.2 | Мониторинг | — |

## ROI расчёт (пример UZ, неделя 6)

| Метрика | До | После (прогноз) |
|---------|-----|-----------------|
| Idle rate suburb | 68% | 52% |
| Rides/day downtown | 420 | 470 |
| Revenue/day USD | $1,050 | $1,180 |

**ROI repositioning crew:** 2 смены × $120 = $240 → uplift $910/нед → **ROI 3.8x**

## Автоматизация

- **Airflow** `weekly_market_report` — каждый понедельник 08:00 UTC
- **Airflow** `anomaly_detection` — ежедневно, append в `anomaly_log`
- Excel conditional formatting: красный = высокий score

## Связанные инсайты

- [Простой парка в Ташкенте](01_tashkent_idle_fleet.md)
- [Падение выручки São Paulo](02_sao_paulo_revenue_drop.md)
