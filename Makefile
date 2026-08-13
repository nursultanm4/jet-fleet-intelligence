.PHONY: up down seed init-db generate test lint run-etl report clean help

PYTHON ?= python
COMPOSE = docker compose

help:
	@echo "Jet Fleet Intelligence — команды"
	@echo "  make up          — запуск ClickHouse + Airflow"
	@echo "  make down        — остановка сервисов"
	@echo "  make init-db     — инициализация схемы ClickHouse"
	@echo "  make generate    — генерация синтетических данных"
	@echo "  make seed        — generate + init-db"
	@echo "  make test        — pytest"
	@echo "  make lint        — ruff check"
	@echo "  make run-etl     — локальный ETL без Airflow"
	@echo "  make report      — генерация Excel-отчёта"

up:
	$(COMPOSE) up -d
	@echo "Airflow UI: http://localhost:8080 (admin/admin)"
	@echo "ClickHouse: http://localhost:8123"

down:
	$(COMPOSE) down

init-db:
	$(PYTHON) scripts/init_clickhouse.py

generate:
	$(PYTHON) scripts/generate_data.py --days 90 --output data/raw

seed: generate init-db

test:
	$(PYTHON) -m pytest tests/ -v

lint:
	$(PYTHON) -m ruff check src scripts dags tests

run-etl:
	$(PYTHON) scripts/run_etl_local.py

report:
	$(PYTHON) scripts/generate_weekly_report.py

clean:
	rm -rf data/raw/*.csv reports/weekly/*.xlsx reports/weekly/*.html
	$(COMPOSE) down -v
