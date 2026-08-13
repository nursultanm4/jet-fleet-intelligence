from __future__ import annotations

import argparse
import re
import sys
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.clickhouse.client import get_client  # noqa: E402

SQL_DIR = PROJECT_ROOT / "sql" / "adhoc"

# Default params for demo queries
DEFAULTS = {
    "date_from": (date.today() - timedelta(days=30)).isoformat(),
    "date_to": date.today().isoformat(),
    "as_of_date": date.today().isoformat(),
    "target_date": (date.today() - timedelta(days=1)).isoformat(),
    "market_code": "UZ",
    "week_end_date": date.today().isoformat(),
    "current_week_start": (date.today() - timedelta(days=date.today().weekday())).isoformat(),
    "prev_week_start": (date.today() - timedelta(days=date.today().weekday() + 7)).isoformat(),
    "limit": "20",
}


def parse_params(param_strings: list[str]) -> dict:
    params = dict(DEFAULTS)
    for item in param_strings:
        if "=" not in item:
            raise ValueError(f"Invalid param format: {item}. Use key=value")
        key, value = item.split("=", 1)
        params[key.strip()] = value.strip()
    return params


def load_query(name: str) -> str:
    base = name.removesuffix(".sql")
    path = SQL_DIR / f"{base}.sql"
    if path.exists():
        return path.read_text(encoding="utf-8")
    matches = sorted(SQL_DIR.glob(f"{base}*.sql"))
    if len(matches) == 1:
        return matches[0].read_text(encoding="utf-8")
    if matches:
        return matches[0].read_text(encoding="utf-8")
    raise FileNotFoundError(f"Query not found: {name}")


def substitute_params(query: str, params: dict) -> str:
    """Replace {param:Type} placeholders with literal values for CLI demo."""

    def replacer(match: re.Match) -> str:
        name = match.group(1)
        ptype = match.group(2)
        value = params.get(name, DEFAULTS.get(name, ""))
        if ptype in ("String",):
            return f"'{value}'"
        if ptype in ("Date",):
            return f"toDate('{value}')"
        if ptype in ("UInt32", "UInt8", "Int32"):
            return str(value)
        return f"'{value}'"

    return re.sub(r"\{(\w+):(\w+)\}", replacer, query)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ad-hoc ClickHouse queries")
    parser.add_argument("--query", "-q", required=True, help="Query name e.g. q03 or q03_revenue_per_scooter")
    parser.add_argument("--params", "-p", nargs="*", default=[], help="key=value params")
    parser.add_argument("--output", "-o", help="Save results to CSV")
    args = parser.parse_args()

    params = parse_params(args.params)
    raw_query = load_query(args.query)
    query = substitute_params(raw_query, params)

    # Strip SQL comments for cleaner output
    print(f"--- Query: {args.query} ---")
    client = get_client()
    df = client.query_df(query)

    if df.empty:
        print("No results.")
    else:
        print(df.to_string(index=False))
        print(f"\n({len(df)} rows)")

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out, index=False)
        print(f"Saved to {out}")


if __name__ == "__main__":
    main()
