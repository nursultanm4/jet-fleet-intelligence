from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def test_report_builder_imports():
    from src.excel import report_builder

    assert hasattr(report_builder, "build_weekly_market_report")
    assert hasattr(report_builder, "build_rebalancing_sheet")
    assert hasattr(report_builder, "build_plotly_html")


def test_openpyxl_workbook_creation(tmp_path):
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Test"
    ws["A1"] = "JET Test"
    path = tmp_path / "test.xlsx"
    wb.save(path)
    assert path.exists()
    assert path.stat().st_size > 0
