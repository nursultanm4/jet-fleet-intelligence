"""Run ETL pipeline locally with out Airflow"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.etl.pipeline import run_full_etl  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main() -> None:
    run_full_etl()
    print("ETL completed successfully.")


if __name__ == "__main__":
    main()
