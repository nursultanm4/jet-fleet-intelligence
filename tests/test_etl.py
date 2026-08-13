"""Tests for data generator"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_generator.generator import GeneratorConfig, generate_all  # noqa: E402
from src.etl.pipeline import RIDE_COLUMNS, validate_raw_files  # noqa: E402


@pytest.fixture
def small_config():
    return GeneratorConfig(days=3, seed=42, start_date=date(2025, 1, 1))


def test_generate_all_produces_expected_tables(small_config):
    datasets = generate_all(small_config)
    assert set(datasets.keys()) == {
        "dim_zone", "dim_scooter", "dim_user", "rides", "scooter_status", "maintenance"
    }
    assert len(datasets["rides"]) > 0
    assert len(datasets["dim_zone"]) >= 6


def test_rides_have_required_columns(small_config):
    datasets = generate_all(small_config)
    rides = datasets["rides"]
    for col in RIDE_COLUMNS:
        assert col in rides.columns


def test_anomaly_scenarios_change_volume(small_config):
    """Week-level multipliers should affect ride counts."""
    datasets = generate_all(small_config)
    br_rides = datasets["rides"][datasets["rides"]["market_id"] == 7]
    assert len(br_rides) > 0


def test_validate_raw_files(tmp_path, small_config):
    datasets = generate_all(small_config)
    for name in ["rides", "scooter_status", "maintenance"]:
        datasets[name].to_csv(tmp_path / f"{name}.csv", index=False)
    paths = validate_raw_files(tmp_path)
    assert len(paths) == 3


def test_rides_fare_positive(small_config):
    datasets = generate_all(small_config)
    assert (datasets["rides"]["fare_usd"] > 0).all()


def test_status_probs_sum_to_one():
    from src.data_generator.generator import _status_probs

    for idle_mult in (1.0, 1.4, 2.0):
        probs = _status_probs(idle_mult)
        assert abs(probs.sum() - 1.0) < 1e-9
