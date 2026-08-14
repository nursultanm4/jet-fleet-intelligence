"""Initialize ClickHouse our cool schema and seed dimensions"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.clickhouse.client import execute_sql_file, get_client  # noqa: E402

MARKET_SEED = """
INSERT INTO dim_market VALUES
(1, 'KZ', 'Almaty', 'KZT', 'Asia/Almaty', 120, 350, 45),
(2, 'KZ', 'Astana', 'KZT', 'Asia/Almaty', 80, 350, 45),
(3, 'UZ', 'Tashkent', 'UZS', 'Asia/Tashkent', 100, 8000, 900),
(4, 'AZ', 'Baku', 'AZN', 'Asia/Baku', 70, 1.5, 0.15),
(5, 'GE', 'Tbilisi', 'GEL', 'Asia/Tbilisi', 60, 2.0, 0.20),
(6, 'MN', 'Ulaanbaatar', 'MNT', 'Asia/Ulaanbaatar', 40, 1500, 180),
(7, 'BR', 'Sao Paulo', 'BRL', 'America/Sao_Paulo', 150, 4.0, 0.50)
"""


def main() -> None:
    client = get_client()
    ddl_dir = PROJECT_ROOT / "sql" / "ddl"
    for sql_file in sorted(ddl_dir.glob("*.sql")):
        print(f"Executing {sql_file.name}...")
        execute_sql_file(client, sql_file)
    count = client.command("SELECT count() FROM dim_market")
    if count == 0:
        print("Seeding dim_market...")
        client.command(MARKET_SEED)
    # Migration: battery_capacity Wh values exceed UInt8
    try:
        client.command("ALTER TABLE dim_scooter MODIFY COLUMN battery_capacity UInt16")
    except Exception:
        pass
    print("ClickHouse schema initialized.")


if __name__ == "__main__":
    main()
