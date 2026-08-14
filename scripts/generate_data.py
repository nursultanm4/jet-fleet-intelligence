"""Generate synthetic (fake) JET micromobility datasets"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_generator.generator import GeneratorConfig, generate_all, save_csv  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic JET fleet data")
    parser.add_argument("--days", type=int, default=90, help="Number of days to generate")
    parser.add_argument("--output", type=str, default="data/raw", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    start_date = date.today() - timedelta(days=args.days)
    config = GeneratorConfig(days=args.days, seed=args.seed, start_date=start_date)
    datasets = generate_all(config)
    print("Saving CSV files...")
    save_csv(datasets, PROJECT_ROOT / args.output)
    print(f"Generated {len(datasets['rides']):,} rides over {args.days} days.")


if __name__ == "__main__":
    main()
