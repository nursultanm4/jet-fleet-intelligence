from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.excel.report_builder import (  # noqa: E402
    build_plotly_html,
    build_rebalancing_sheet,
    build_weekly_market_report,
)


def main() -> None:
    excel = build_weekly_market_report()
    print(f"Weekly Excel: {excel}")
    for code in ("UZ", "BR", "KZ"):
        rb = build_rebalancing_sheet(code)
        print(f"Rebalancing {code}: {rb}")
    html = build_plotly_html()
    print(f"Plotly HTML: {html}")


if __name__ == "__main__":
    main()
