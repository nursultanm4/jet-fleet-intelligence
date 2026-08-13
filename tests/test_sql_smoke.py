"""the Smoke tests for SQL query library"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

SQL_DIR = PROJECT_ROOT / "sql" / "adhoc"


def test_minimum_query_count():
    queries = list(SQL_DIR.glob("q*.sql"))
    assert len(queries) >= 15, f"Expected 15+ queries, found {len(queries)}"


@pytest.mark.parametrize("sql_file", sorted(SQL_DIR.glob("q*.sql")), ids=lambda p: p.name)
def test_sql_file_has_comment_header(sql_file: Path):
    content = sql_file.read_text(encoding="utf-8")
    assert content.strip().startswith("--"), f"{sql_file.name} missing header comment"


@pytest.mark.parametrize("sql_file", sorted(SQL_DIR.glob("q*.sql")), ids=lambda p: p.name)
def test_sql_file_has_select(sql_file: Path):
    content = sql_file.read_text(encoding="utf-8").upper()
    assert "SELECT" in content


def test_run_query_substitution():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "run_query", PROJECT_ROOT / "scripts" / "run_query.py"
    )
    run_query = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(run_query)

    query = run_query.load_query("q03")
    result = run_query.substitute_params(query, {
        "date_from": "2025-01-01",
        "date_to": "2025-01-31",
    })
    assert "toDate('2025-01-01')" in result
    assert "{date_from:Date}" not in result


def test_all_queries_substitutable():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "run_query", PROJECT_ROOT / "scripts" / "run_query.py"
    )
    run_query = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(run_query)

    for sql_file in SQL_DIR.glob("q*.sql"):
        query = run_query.load_query(sql_file.stem)
        params = {m.group(1): run_query.DEFAULTS.get(m.group(1), "1")
                  for m in re.finditer(r"\{(\w+):\w+\}", query)}
        result = run_query.substitute_params(query, params)
        assert not re.search(r"\{\w+:\w+\}", result), f"Unresolved params in {sql_file.name}"
