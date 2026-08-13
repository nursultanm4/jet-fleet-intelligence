"""Synthetic multi-market micromobility dataset for the JET Fleet Intelligence"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42

MARKETS = [
    {"market_id": 1, "country_code": "KZ", "city": "Almaty", "fleet": 120, "base_fare": 350, "per_min": 45},
    {"market_id": 2, "country_code": "KZ", "city": "Astana", "fleet": 80, "base_fare": 350, "per_min": 45},
    {"market_id": 3, "country_code": "UZ", "city": "Tashkent", "fleet": 100, "base_fare": 8000, "per_min": 900},
    {"market_id": 4, "country_code": "AZ", "city": "Baku", "fleet": 70, "base_fare": 1.5, "per_min": 0.15},
    {"market_id": 5, "country_code": "GE", "city": "Tbilisi", "fleet": 60, "base_fare": 2.0, "per_min": 0.20},
    {"market_id": 6, "country_code": "MN", "city": "Ulaanbaatar", "fleet": 40, "base_fare": 1500, "per_min": 180},
    {"market_id": 7, "country_code": "BR", "city": "Sao Paulo", "fleet": 150, "base_fare": 4.0, "per_min": 0.50},
]

ZONE_TYPES = ["downtown", "suburb", "university", "transit_hub"]
USD_RATES = {1: 0.0022, 2: 0.0022, 3: 0.00008, 4: 0.59, 5: 0.37, 6: 0.00029, 7: 0.20}


@dataclass
class GeneratorConfig:
    days: int = 90
    seed: int = SEED
    start_date: date | None = None


def _hash_id(prefix: str, idx: int) -> str:
    return hashlib.sha256(f"{prefix}-{idx}".encode()).hexdigest()[:16]


def generate_zones(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    zone_id = 1
    for market in MARKETS:
        n_zones = max(6, market["fleet"] // 10)
        for i in range(n_zones):
            zone_type = ZONE_TYPES[i % len(ZONE_TYPES)]
            rows.append(
                {
                    "zone_id": zone_id,
                    "geofence_id": f"GF-{market['country_code']}-{i+1:02d}",
                    "market_id": market["market_id"],
                    "zone_name": f"{market['city']} {zone_type.replace('_', ' ').title()} {i+1}",
                    "zone_type": zone_type,
                    "center_lat": round(40 + rng.uniform(-5, 5), 6),
                    "center_lon": round(50 + rng.uniform(-10, 10), 6),
                }
            )
            zone_id += 1
    return pd.DataFrame(rows)


def generate_scooters(zones: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    scooter_idx = 0
    for market in MARKETS:
        market_zones = zones[zones["market_id"] == market["market_id"]]["zone_id"].tolist()
        for _ in range(market["fleet"]):
            rows.append(
                {
                    "scooter_id": f"S-{market['country_code']}-{scooter_idx:04d}",
                    "market_id": market["market_id"],
                    "model": rng.choice(["Jet Pro", "Jet Lite", "Jet Max"]),
                    "battery_capacity": int(rng.choice([300, 400, 500])),
                    "deploy_date": date(2024, 1, 1) + timedelta(days=int(rng.integers(0, 180))),
                    "home_zone_id": int(rng.choice(market_zones)),
                }
            )
            scooter_idx += 1
    return pd.DataFrame(rows)


def generate_users(rng: np.random.Generator, n_users: int = 8000) -> pd.DataFrame:
    rows = []
    for i in range(n_users):
        market = MARKETS[int(rng.integers(0, len(MARKETS)))]
        first = date(2025, 1, 1) + timedelta(days=int(rng.integers(0, 120)))
        last = first + timedelta(days=int(rng.integers(0, 60)))
        segment = rng.choice(["new", "returning", "returning", "churned"], p=[0.2, 0.5, 0.2, 0.1])
        rows.append(
            {
                "user_id": _hash_id("user", i),
                "market_id": market["market_id"],
                "segment": segment,
                "first_ride_date": first,
                "last_ride_date": last,
            }
        )
    return pd.DataFrame(rows)


def _hour_weight(hour: int) -> float:
    if 7 <= hour <= 9 or 17 <= hour <= 20:
        return 2.5
    if 12 <= hour <= 14:
        return 1.5
    if 22 <= hour or hour <= 5:
        return 0.3
    return 1.0


def _anomaly_multiplier(market_id: int, d: date, start: date) -> tuple[float, float]:
    """Return (ride_multiplier, idle_multiplier) for embedded scenarios."""
    week = (d - start).days // 7 + 1
    ride_mult, idle_mult = 1.0, 1.0
    # Tashkent week 6: idle fleet +40%
    if market_id == 3 and week == 6:
        idle_mult = 1.4
    # Sao Paulo week 8: revenue/rides -25%
    if market_id == 7 and week == 8:
        ride_mult = 0.75
    # Almaty week 4: maintenance spike handled separately
    return ride_mult, idle_mult


def _hour_probs() -> np.ndarray:
    weights = np.array([_hour_weight(h) for h in range(24)], dtype=float)
    return weights / weights.sum()


def generate_rides(
    config: GeneratorConfig,
    zones: pd.DataFrame,
    scooters: pd.DataFrame,
    users: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    start = config.start_date or (date.today() - timedelta(days=config.days))
    hour_probs = _hour_probs()
    chunks: list[pd.DataFrame] = []
    ride_idx = 0

    zone_lookup = zones.groupby("market_id")["zone_id"].apply(list).to_dict()

    for day_offset in range(config.days):
        d = start + timedelta(days=day_offset)
        is_weekend = d.weekday() >= 5
        day_base = datetime.combine(d, datetime.min.time())

        for market in MARKETS:
            ride_mult, _ = _anomaly_multiplier(market["market_id"], d, start)
            market_scooters = scooters[scooters["market_id"] == market["market_id"]]
            market_zones = zone_lookup.get(market["market_id"], [])
            market_users = users[users["market_id"] == market["market_id"]]["user_id"].values
            if len(market_users) == 0 or len(market_zones) == 0 or market_scooters.empty:
                continue

            n = int(market["fleet"] * (1.8 if not is_weekend else 2.2) * ride_mult)
            if n == 0:
                continue

            hours = rng.choice(24, size=n, p=hour_probs)
            minutes = rng.integers(0, 60, size=n)
            durations = rng.integers(180, 2400, size=n)
            distances = (durations * rng.uniform(0.08, 0.15, size=n)).astype(int)
            fare_local = np.round(
                market["base_fare"] + (durations / 60) * market["per_min"], 2
            )
            fare_usd = np.round(fare_local * USD_RATES[market["market_id"]], 4)

            scooter_ids = market_scooters["scooter_id"].values
            picked_scooters = scooter_ids[rng.integers(0, len(scooter_ids), size=n)]
            picked_users = rng.choice(market_users, size=n)
            start_zones = rng.choice(market_zones, size=n)
            end_zones = rng.choice(market_zones, size=n)

            started_at = [
                day_base + timedelta(hours=int(h), minutes=int(m))
                for h, m in zip(hours, minutes, strict=True)
            ]
            ended_at = [
                s + timedelta(seconds=int(dur))
                for s, dur in zip(started_at, durations, strict=True)
            ]

            chunks.append(
                pd.DataFrame(
                    {
                        "ride_id": [f"R-{ride_idx + i:07d}" for i in range(n)],
                        "user_id": picked_users,
                        "scooter_id": picked_scooters,
                        "market_id": market["market_id"],
                        "start_zone_id": start_zones,
                        "end_zone_id": end_zones,
                        "started_at": started_at,
                        "ended_at": ended_at,
                        "distance_m": distances,
                        "duration_sec": durations,
                        "fare_local": fare_local,
                        "fare_usd": fare_usd,
                        "ride_date": d,
                    }
                )
            )
            ride_idx += n

    return pd.concat(chunks, ignore_index=True)


def _status_probs(idle_mult: float) -> np.ndarray:
    """Normalized status probabilities; idle_mult > 1 increases available share."""
    p_available = 0.55 / idle_mult if idle_mult > 1 else 0.55
    p_ride = 0.35
    p_maint = 0.10 if idle_mult <= 1 else 0.05
    probs = np.array([p_available, p_ride, p_maint], dtype=float)
    return probs / probs.sum()


def _sample_statuses(n: int, probs: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Vectorized status sampling for n scooters."""
    labels = np.array(["available", "ride", "maintenance"])
    return rng.choice(labels, size=n, p=probs)


def generate_scooter_status(
    config: GeneratorConfig,
    zones: pd.DataFrame,
    scooters: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    start = config.start_date or (date.today() - timedelta(days=config.days))
    zone_lookup = zones.groupby("market_id")["zone_id"].apply(list).to_dict()
    zone_coords = zones.set_index("zone_id")[["center_lat", "center_lon"]]

    chunks: list[pd.DataFrame] = []
    for day_offset in range(config.days):
        d = start + timedelta(days=day_offset)
        for hour in range(0, 24, 3):
            snapshot_at = datetime.combine(d, datetime.min.time()) + timedelta(hours=hour)
            for market in MARKETS:
                market_scooters = scooters[scooters["market_id"] == market["market_id"]]
                n = len(market_scooters)
                if n == 0:
                    continue

                _, idle_mult = _anomaly_multiplier(market["market_id"], d, start)
                probs = _status_probs(idle_mult)
                market_zones = zone_lookup[market["market_id"]]
                zone_ids = rng.choice(market_zones, size=n)

                chunk = pd.DataFrame(
                    {
                        "snapshot_at": snapshot_at,
                        "scooter_id": market_scooters["scooter_id"].values,
                        "market_id": market["market_id"],
                        "zone_id": zone_ids,
                        "battery_pct": rng.integers(15, 100, size=n),
                        "status": _sample_statuses(n, probs, rng),
                        "snapshot_date": d,
                    }
                )
                coords = zone_coords.loc[zone_ids]
                chunk["lat"] = coords["center_lat"].values + rng.uniform(-0.01, 0.01, size=n)
                chunk["lon"] = coords["center_lon"].values + rng.uniform(-0.01, 0.01, size=n)
                chunks.append(chunk)

    return pd.concat(chunks, ignore_index=True)


def generate_maintenance(
    config: GeneratorConfig,
    scooters: pd.DataFrame,
    zones: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    start = config.start_date or (date.today() - timedelta(days=config.days))
    rows = []
    event_idx = 0
    issue_types = ["battery", "brake", "tire", "electronics", "vandalism"]

    for day_offset in range(config.days):
        d = start + timedelta(days=day_offset)
        week = day_offset // 7 + 1
        for market in MARKETS:
            mult = 3.0 if market["market_id"] == 1 and week == 4 else 1.0
            n_events = int(rng.poisson(max(1, market["fleet"] * 0.02 * mult)))
            market_scooters = scooters[scooters["market_id"] == market["market_id"]]
            market_zones = zones[zones["market_id"] == market["market_id"]]["zone_id"].tolist()
            for _ in range(n_events):
                scooter = market_scooters.sample(1).iloc[0]
                started = datetime.combine(d, datetime.min.time()) + timedelta(hours=int(rng.integers(6, 20)))
                downtime = round(float(rng.uniform(1, 12)), 2)
                rows.append(
                    {
                        "event_id": f"M-{event_idx:06d}",
                        "scooter_id": scooter["scooter_id"],
                        "market_id": market["market_id"],
                        "zone_id": int(rng.choice(market_zones)),
                        "started_at": started,
                        "ended_at": started + timedelta(hours=downtime),
                        "downtime_hours": downtime,
                        "issue_type": str(rng.choice(issue_types)),
                        "event_date": d,
                    }
                )
                event_idx += 1
    return pd.DataFrame(rows)


def generate_all(config: GeneratorConfig | None = None) -> dict[str, pd.DataFrame]:
    config = config or GeneratorConfig()
    rng = np.random.default_rng(config.seed)
    print("Generating dimensions...")
    zones = generate_zones(rng)
    scooters = generate_scooters(zones, rng)
    users = generate_users(rng)
    print("Generating rides...")
    rides = generate_rides(config, zones, scooters, users, rng)
    print("Generating scooter status snapshots...")
    status = generate_scooter_status(config, zones, scooters, rng)
    print("Generating maintenance events...")
    maintenance = generate_maintenance(config, scooters, zones, rng)
    return {
        "dim_zone": zones,
        "dim_scooter": scooters.drop(columns=["home_zone_id"]),
        "dim_user": users,
        "rides": rides,
        "scooter_status": status,
        "maintenance": maintenance,
    }


def save_csv(datasets: dict[str, pd.DataFrame], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    mapping = {
        "rides": "rides.csv",
        "scooter_status": "scooter_status.csv",
        "maintenance": "maintenance.csv",
        "dim_zone": "dim_zone.csv",
        "dim_scooter": "dim_scooter.csv",
        "dim_user": "dim_user.csv",
    }
    for key, filename in mapping.items():
        path = output_dir / filename
        datasets[key].to_csv(path, index=False)
        print(f"Saved {path} ({len(datasets[key]):,} rows)")
