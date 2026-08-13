from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import clickhouse_connect
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def get_client(database: str | None = None):
    """Create ClickHouse client from environment variables."""
    password = os.getenv("CLICKHOUSE_PASSWORD")
    if password is None:
        password = "jet_analytics"
    kwargs = {
        "host": os.getenv("CLICKHOUSE_HOST", "localhost"),
        "port": int(os.getenv("CLICKHOUSE_PORT", "8123")),
        "username": os.getenv("CLICKHOUSE_USER", "default"),
        "database": database or os.getenv("CLICKHOUSE_DB", "jet_analytics"),
    }
    if password != "":
        kwargs["password"] = password
    return clickhouse_connect.get_client(**kwargs)


def execute_sql_file(client, sql_path: Path) -> None:
    """Execute SQL statements from a file."""
    content = sql_path.read_text(encoding="utf-8")
    # Strip line comments to avoid splitting on semicolons inside comments
    lines = []
    for line in content.splitlines():
        stripped = line.split("--", 1)[0].strip()
        if stripped:
            lines.append(stripped)
    cleaned = "\n".join(lines)
    statements = [s.strip() for s in cleaned.split(";") if s.strip()]
    for statement in statements:
        client.command(statement)


def execute_query(client, query: str, params: dict[str, Any] | None = None):
    """Run SELECT query and return pandas DataFrame."""
    return client.query_df(query, parameters=params or {})


def insert_dataframe(client, table: str, df) -> None:
    """Bulk insert pandas DataFrame into ClickHouse table."""
    if df.empty:
        return
    client.insert_df(table, df)


def read_sql(relative_path: str) -> str:
    """Read SQL file relative to sql/ directory."""
    path = PROJECT_ROOT / "sql" / relative_path
    return path.read_text(encoding="utf-8")
