"""
Centralized configuration management for Jet Fleet Intelligence

Uses pydantic for validation and environment-based settings.
Supports .env file loading via python-dotenv

Usage:
    from src.config import settings

    ch_host = settings.clickhouse.host
    log_level = settings.logging.level
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

# Load .env file
load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ClickHouseSettings(BaseModel):
    """ClickHouse database connection configuration."""

    host: str = Field(default="localhost", description="ClickHouse server host")
    port: int = Field(default=8123, description="ClickHouse HTTP port")
    username: str = Field(default="default", description="ClickHouse username")
    password: str = Field(default="jet_analytics", description="ClickHouse password")
    database: str = Field(default="jet_analytics", description="Database name")
    timeout_sec: int = Field(default=30, description="Query timeout in seconds")
    pool_size: int = Field(default=5, description="Connection pool size")

    @classmethod
    def from_env(cls) -> ClickHouseSettings:
        """Load settings from environment variables."""
        return cls(
            host=os.getenv("CLICKHOUSE_HOST", "localhost"),
            port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
            username=os.getenv("CLICKHOUSE_USER", "default"),
            password=os.getenv("CLICKHOUSE_PASSWORD", "jet_analytics"),
            database=os.getenv("CLICKHOUSE_DB", "jet_analytics"),
            timeout_sec=int(os.getenv("CLICKHOUSE_TIMEOUT_SEC", "30")),
            pool_size=int(os.getenv("CLICKHOUSE_POOL_SIZE", "5")),
        )


class AirflowSettings(BaseModel):
    """Apache Airflow configuration."""

    executor: str = Field(default="LocalExecutor", description="Airflow executor type")
    db_url: str = Field(
        default="postgresql+psycopg2://airflow:airflow@postgres:5432/airflow",
        description="Airflow metadata database URL",
    )
    fernet_key: str = Field(
        default="CHANGE_ME_GENERATE_WITH_python_-c_import_fernet_Fernet_generate_key",
        description="Airflow Fernet key for secrets",
    )
    secret_key: str = Field(default="change_me_secret_key", description="Webserver secret key")
    load_examples: bool = Field(default=False, description="Load example DAGs")
    uid: int = Field(default=50000, description="Airflow UID in Docker")

    @classmethod
    def from_env(cls) -> AirflowSettings:
        """Load settings from environment variables."""
        return cls(
            executor=os.getenv("AIRFLOW__CORE__EXECUTOR", "LocalExecutor"),
            db_url=os.getenv(
                "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN",
                "postgresql+psycopg2://airflow:airflow@postgres:5432/airflow",
            ),
            fernet_key=os.getenv(
                "AIRFLOW__CORE__FERNET_KEY",
                "CHANGE_ME_GENERATE_WITH_python_-c_import_fernet_Fernet_generate_key",
            ),
            secret_key=os.getenv("AIRFLOW__WEBSERVER__SECRET_KEY", "change_me_secret_key"),
            load_examples=os.getenv("AIRFLOW__CORE__LOAD_EXAMPLES", "false").lower() == "true",
            uid=int(os.getenv("AIRFLOW_UID", "50000")),
        )


class PathSettings(BaseModel):
    """Project paths configuration."""

    root: Path = Field(default=PROJECT_ROOT, description="Project root directory")
    data_raw: Path = Field(default=PROJECT_ROOT / "data" / "raw", description="Raw data directory")
    reports_weekly: Path = Field(
        default=PROJECT_ROOT / "reports" / "weekly", description="Weekly reports output"
    )
    excel_templates: Path = Field(
        default=PROJECT_ROOT / "excel_templates", description="Excel template files"
    )
    sql_dir: Path = Field(default=PROJECT_ROOT / "sql", description="SQL scripts directory")
    sql_adhoc: Path = Field(
        default=PROJECT_ROOT / "sql" / "adhoc", description="Ad-hoc SQL queries"
    )
    docs: Path = Field(default=PROJECT_ROOT / "docs", description="Documentation directory")
    dags: Path = Field(default=PROJECT_ROOT / "dags", description="Airflow DAGs directory")
    tests: Path = Field(default=PROJECT_ROOT / "tests", description="Test directory")

    def __init__(self, **data: Any) -> None:
        """Ensure paths exist on initialization."""
        super().__init__(**data)
        # Create data and report directories if they don't exist
        self.data_raw.mkdir(parents=True, exist_ok=True)
        self.reports_weekly.mkdir(parents=True, exist_ok=True)
        self.excel_templates.mkdir(parents=True, exist_ok=True)


class LoggingSettings(BaseModel):
    """Logging configuration."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Root logger level"
    )
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format",
    )
    file_path: Path | None = Field(default=None, description="Log file path (None = stdout only)")
    max_bytes: int = Field(default=10_485_760, description="Max log file size (10MB)")
    backup_count: int = Field(default=5, description="Number of rotated log backups")

    @classmethod
    def from_env(cls) -> LoggingSettings:
        """Load settings from environment variables."""
        return cls(
            level=os.getenv("LOG_LEVEL", "INFO"),  # type: ignore
            format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            file_path=Path(fp) if (fp := os.getenv("LOG_FILE")) else None,
            max_bytes=int(os.getenv("LOG_MAX_BYTES", "10485760")),
            backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5")),
        )


class AnomalySettings(BaseModel):
    """Anomaly detection configuration."""

    z_threshold: float = Field(default=-2.0, description="Z-score threshold for anomalies")
    lookback_days: int = Field(default=14, description="Days to use for baseline calculation")
    high_severity_threshold: float = Field(
        default=-3.0, description="Z-score threshold for 'high' severity"
    )

    @field_validator("z_threshold", "high_severity_threshold")
    @classmethod
    def validate_thresholds(cls, v: float) -> float:
        if v >= 0:
            raise ValueError("Threshold must be negative")
        return v

    @classmethod
    def from_env(cls) -> AnomalySettings:
        """Load settings from environment variables."""
        return cls(
            z_threshold=float(os.getenv("ANOMALY_Z_THRESHOLD", "-2.0")),
            lookback_days=int(os.getenv("ANOMALY_LOOKBACK_DAYS", "14")),
            high_severity_threshold=float(os.getenv("ANOMALY_HIGH_SEVERITY_THRESHOLD", "-3.0")),
        )


class ETLSettings(BaseModel):
    """ETL pipeline configuration."""

    batch_size: int = Field(default=5000, description="Batch size for data loading")
    staging_truncate: bool = Field(default=True, description="Truncate staging tables before load")
    full_refresh: bool = Field(
        default=True, description="Full refresh of dimension tables (vs incremental)"
    )
    dry_run: bool = Field(default=False, description="Simulate ETL without database writes")
    max_retries: int = Field(default=3, description="Max retries for failed operations")
    retry_delay_sec: int = Field(default=5, description="Delay between retries (seconds)")

    @classmethod
    def from_env(cls) -> ETLSettings:
        """Load settings from environment variables."""
        return cls(
            batch_size=int(os.getenv("ETL_BATCH_SIZE", "5000")),
            staging_truncate=os.getenv("ETL_STAGING_TRUNCATE", "true").lower() == "true",
            full_refresh=os.getenv("ETL_FULL_REFRESH", "true").lower() == "true",
            dry_run=os.getenv("ETL_DRY_RUN", "false").lower() == "true",
            max_retries=int(os.getenv("ETL_MAX_RETRIES", "3")),
            retry_delay_sec=int(os.getenv("ETL_RETRY_DELAY_SEC", "5")),
        )


class ExcelSettings(BaseModel):
    """Excel report configuration."""

    header_color: str = Field(default="1F4E79", description="Header cell background color")
    header_font_color: str = Field(default="FFFFFF", description="Header font color")
    date_format: str = Field(default="YYYY-MM-DD", description="Date format in Excel")
    freeze_panes: int = Field(default=1, description="Number of header rows to freeze")


class DataGeneratorSettings(BaseModel):
    """Synthetic data generator configuration."""

    default_days: int = Field(default=90, description="Default number of days to generate")
    seed: int | None = Field(default=None, description="Random seed for reproducibility")
    anomaly_scenarios: dict = Field(
        default={
            "tashkent_idle": {"market_id": 3, "weeks": [3, 4, 5], "idle_multiplier": 2.0},
            "sao_paulo_revenue": {"market_id": 7, "weeks": [8, 9, 10], "revenue_multiplier": 0.6},
            "almaty_maintenance": {"market_id": 1, "weeks": [6, 7], "maintenance_spike": 3.0},
        },
        description="Built-in anomaly scenarios for data generation",
    )

    @classmethod
    def from_env(cls) -> DataGeneratorSettings:
        """Load settings from environment variables."""
        return cls(
            default_days=int(os.getenv("DATA_GENERATOR_DAYS", "90")),
            seed=int(s) if (s := os.getenv("DATA_GENERATOR_SEED")) else None,
        )


class Settings(BaseModel):
    """Master settings configuration."""

    environment: Literal["development", "staging", "production"] = Field(
        default="development", description="Deployment environment"
    )
    debug: bool = Field(default=False, description="Enable debug mode")

    clickhouse: ClickHouseSettings
    airflow: AirflowSettings
    paths: PathSettings
    logging: LoggingSettings
    anomaly: AnomalySettings
    etl: ETLSettings
    excel: ExcelSettings
    data_generator: DataGeneratorSettings

    @classmethod
    def from_env(cls) -> Settings:
        """Load all settings from environment variables."""
        return cls(
            environment=os.getenv("ENVIRONMENT", "development"),  # type: ignore
            debug=os.getenv("DEBUG", "false").lower() == "true",
            clickhouse=ClickHouseSettings.from_env(),
            airflow=AirflowSettings.from_env(),
            paths=PathSettings(),
            logging=LoggingSettings.from_env(),
            anomaly=AnomalySettings.from_env(),
            etl=ETLSettings.from_env(),
            excel=ExcelSettings(),
            data_generator=DataGeneratorSettings.from_env(),
        )


# Global settings instance
settings = Settings.from_env()


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        logging.Logger configured with project settings
    """
    logger = logging.getLogger(name)

    # Only configure root logger once
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(settings.logging.format)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, settings.logging.level))

        # Add file handler if configured
        if settings.logging.file_path:
            from logging.handlers import RotatingFileHandler

            file_handler = RotatingFileHandler(
                settings.logging.file_path,
                maxBytes=settings.logging.max_bytes,
                backupCount=settings.logging.backup_count,
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


if __name__ == "__main__":
    # Print current configuration (useful for debugging)
    print("Jet Fleet Intelligence Configuration")
    print("=" * 60)
    print(f"Environment: {settings.environment}")
    print(f"Debug: {settings.debug}")
    print()
    print("ClickHouse:")
    print(f"  Host: {settings.clickhouse.host}:{settings.clickhouse.port}")
    print(f"  Database: {settings.clickhouse.database}")
    print(f"  Timeout: {settings.clickhouse.timeout_sec}s")
    print()
    print("Paths:")
    print(f"  Root: {settings.paths.root}")
    print(f"  Data (raw): {settings.paths.data_raw}")
    print(f"  Reports: {settings.paths.reports_weekly}")
    print()
    print("Anomaly Detection:")
    print(f"  Z-Threshold: {settings.anomaly.z_threshold}")
    print(f"  Lookback: {settings.anomaly.lookback_days} days")
    print()
    print("Logging:")
    print(f"  Level: {settings.logging.level}")
    print(f"  File: {settings.logging.file_path or '(stdout only)'}")
