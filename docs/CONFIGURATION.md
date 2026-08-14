# Configuration Management

## Overview

The project uses a centralized configuration system via `src/config.py` with pydantic for validation and type safety. See all configs by running:
```
python -m src.config
```
Configuration can be set via:

1. **Environment variables** (highest priority)
2. **.env file** (auto-loaded via python-dotenv)
3. **Default values** (lowest priority)

## Usage

### Basic Import

```python
from src.config import settings

# Access configuration
clickhouse_host = settings.clickhouse.host
log_level = settings.logging.level
data_dir = settings.paths.data_raw
```

### Available Settings

| Category | Setting | Example |
|----------|---------|---------|
| **ClickHouse** | `settings.clickhouse.host` | `localhost` |
| | `settings.clickhouse.port` | `8123` |
| | `settings.clickhouse.database` | `jet_analytics` |
| | `settings.clickhouse.timeout_sec` | `30` |
| **Paths** | `settings.paths.data_raw` | `/data/raw` |
| | `settings.paths.reports_weekly` | `/reports/weekly` |
| | `settings.paths.sql_adhoc` | `/sql/adhoc` |
| **Logging** | `settings.logging.level` | `INFO` |
| | `settings.logging.format` | `%(asctime)s - %(name)s...` |
| | `settings.logging.file_path` | `/var/log/jet.log` (optional) |
| **Anomaly Detection** | `settings.anomaly.z_threshold` | `-2.0` |
| | `settings.anomaly.lookback_days` | `14` |
| **ETL** | `settings.etl.batch_size` | `5000` |
| | `settings.etl.dry_run` | `False` |
| **Excel Reports** | `settings.excel.header_color` | `1F4E79` |

## Environment Variables

### ClickHouse

```bash
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=jet_analytics
CLICKHOUSE_DB=jet_analytics
CLICKHOUSE_TIMEOUT_SEC=30
CLICKHOUSE_POOL_SIZE=5
```

### Airflow

```bash
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://...
AIRFLOW__CORE__FERNET_KEY=...
AIRFLOW__WEBSERVER__SECRET_KEY=...
AIRFLOW_UID=50000
```

### Logging

```bash
LOG_LEVEL=INFO                                          # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s..."
LOG_FILE=/var/log/jet_analytics.log                     # Optional
LOG_MAX_BYTES=10485760                                  # 10MB
LOG_BACKUP_COUNT=5
```

### Anomaly Detection

```bash
ANOMALY_Z_THRESHOLD=-2.0                                # Must be negative
ANOMALY_LOOKBACK_DAYS=14
ANOMALY_HIGH_SEVERITY_THRESHOLD=-3.0
```

### ETL Pipeline

```bash
ETL_BATCH_SIZE=5000
ETL_STAGING_TRUNCATE=true
ETL_FULL_REFRESH=true
ETL_DRY_RUN=false
ETL_MAX_RETRIES=3
ETL_RETRY_DELAY_SEC=5
```

### General

```bash
ENVIRONMENT=development                                 # development, staging, production
DEBUG=false
```

## .env File Example

```bash
# ClickHouse
CLICKHOUSE_HOST=clickhouse
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=jet_analytics
CLICKHOUSE_DB=jet_analytics

# Logging
LOG_LEVEL=INFO
LOG_FILE=/opt/jet_analytics/logs/app.log

# ETL
ETL_BATCH_SIZE=5000
ETL_DRY_RUN=false

# Anomaly
ANOMALY_Z_THRESHOLD=-2.0

# Environment
ENVIRONMENT=production
DEBUG=false
```

## Using Logging

```python
from src.config import get_logger

logger = get_logger(__name__)

logger.info("Processing data...")
logger.error("Failed to load data", exc_info=True)
```

## Configuration in Code

### ETL Pipeline Example

```python
from src.config import settings
from src.etl.pipeline import load_staging

# Use configuration
load_staging(batch_size=settings.etl.batch_size)

# Check dry-run mode
if settings.etl.dry_run:
    print("DRY RUN - no database changes")
```

### ClickHouse Connection Example

```python
from src.config import settings
import clickhouse_connect

client = clickhouse_connect.get_client(
    host=settings.clickhouse.host,
    port=settings.clickhouse.port,
    username=settings.clickhouse.username,
    password=settings.clickhouse.password,
    database=settings.clickhouse.database,
)
```

## Validation

All settings are validated with pydantic. Invalid values will raise an error:

```python
# Example: Z-threshold must be negative
# This will fail:
ANOMALY_Z_THRESHOLD=2.0  # ❌ ValueError: Threshold must be negative
ANOMALY_Z_THRESHOLD=-2.0  # ✅ Valid
```



# 🧩 Testing

Print current configuration:

```bash
python -m src.config
```

Output:
```
Jet Fleet Intelligence Configuration
============================================================
Environment: development
Debug: False

ClickHouse:
  Host: localhost:8123
  Database: jet_analytics
  Timeout: 30s

Paths:
  Root: /opt/jet_analytics
  Data (raw): /opt/jet_analytics/data/raw
  Reports: /opt/jet_analytics/reports/weekly

Anomaly Detection:
  Z-Threshold: -2.0
  Lookback: 14 days

Logging:
  Level: INFO
  File: (stdout only)
```

## Priority Order

Settings are resolved in this order (first match wins):

1. **Environment variables** - `CLICKHOUSE_HOST=myhost`
2. **.env file** - Loaded via python-dotenv
3. **Default values** - Defined in `src/config.py`

## Adding New Settings

To add a new configuration:

1. Create a new `BaseModel` class in `src/config.py`
2. Add a `from_env()` classmethod to load from environment variables
3. Add it to the `Settings` class
4. Update `.env.example` with the new variable
5. Document in this file

Example:

```python
class MyFeatureSettings(BaseModel):
    enabled: bool = Field(default=True, description="Enable my feature")
    timeout: int = Field(default=30, description="Timeout in seconds")

    @classmethod
    def from_env(cls) -> MyFeatureSettings:
        return cls(
            enabled=os.getenv("MY_FEATURE_ENABLED", "true").lower() == "true",
            timeout=int(os.getenv("MY_FEATURE_TIMEOUT", "30")),
        )

# In Settings class:
my_feature: MyFeatureSettings = Field(default_factory=MyFeatureSettings.from_env)
```

## Benefits

✅

**Type-safe** - Pydantic validates all settings
**Environment-aware** - Easy to configure per environment
**Centralized** - Single source of truth for configuration
**Documented** - All settings have descriptions
**Tested** - Settings are validated on load
**Overridable** - Environment variables override defaults
