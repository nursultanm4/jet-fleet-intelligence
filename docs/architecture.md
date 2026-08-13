# Архитектура Jet Fleet Intelligence

## Обзор

Платформа аналитики микромобильности JET Group: синтетические данные → CSV → Airflow ETL → ClickHouse → Excel/HTML отчёты и ad-hoc SQL.

## Компоненты

| Компонент | Технология | Назначение |
|-----------|------------|------------|
| Orchestration | Apache Airflow 2.9 | 3 DAG: ETL, reports, anomalies |
| Storage | ClickHouse 24 | OLAP, star schema, aggregates |
| Transform | Python + pandas | ETL, validation, DQ |
| Reports | openpyxl, Plotly | Excel + HTML визуализация |
| Ad-hoc | SQL + CLI | 15 business queries |

## DAG dependencies

```
daily_fleet_etl (06:00 UTC)
    └── anomaly_detection (07:00 UTC)

weekly_market_report (Mon 08:00 UTC)
    └── depends on marts populated
```

## Data flow

1. `scripts/generate_data.py` → `data/raw/*.csv`
2. `daily_fleet_etl` → staging → facts → aggregates
3. `weekly_market_report` → `reports/weekly/*.xlsx`
4. `anomaly_detection` → `anomaly_log` + `docs/insights/anomaly_log.md`

## Локальный запуск

```bash
make up          # Docker: ClickHouse + Airflow
make seed        # generate + init-db
make run-etl     # ETL без Airflow
make report      # Excel + HTML
```

## CI

GitHub Actions: ruff, pytest (generator + ETL unit tests), SQL file validation.
