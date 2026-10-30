"""
Northstar Retail Analytics Platform — Base Configuration
Manages environment variables, execution environments (dev/stage/prod),
and application-wide settings with zero hardcoded credentials.
"""

import os
from pathlib import Path
from typing import Optional
from functools import lru_cache

# Base project root directory (absolute path)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load .env file if it exists (using local file or standard fallback)
try:
    from dotenv import load_dotenv
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        load_dotenv(dotenv_path=env_file)
except ImportError:
    pass


class Settings:
    """
    Central application settings container.
    Reads strictly from environment variables with sensible development fallbacks.
    Never hardcodes production secrets.
    """

    def __init__(self) -> None:
        # Execution Environment Mode
        self.app_env: str = os.getenv("APP_ENV", "development").lower()
        self.app_name: str = os.getenv("APP_NAME", "Northstar_Retail_Analytics")
        self.app_version: str = os.getenv("APP_VERSION", "1.0.0")

        # Database Configuration Parameters
        self.postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
        self.postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
        self.postgres_db: str = os.getenv("POSTGRES_DB", "northstar_analytics_dev")
        self.postgres_user: str = os.getenv("POSTGRES_USER", "northstar_dev_user")
        self.postgres_password: str = os.getenv("POSTGRES_PASSWORD", "placeholder_dev_password_change_me")
        self.postgres_schema: str = os.getenv("POSTGRES_SCHEMA", "public")
        self.postgres_sslmode: str = os.getenv("POSTGRES_SSLMODE", "prefer")

        # Local Data Storage Paths (relative to project root)
        self.data_raw_dir: Path = PROJECT_ROOT / os.getenv("DATA_RAW_DIR", "data/raw")
        self.data_bronze_dir: Path = PROJECT_ROOT / os.getenv("DATA_BRONZE_DIR", "data/bronze")
        self.data_silver_dir: Path = PROJECT_ROOT / os.getenv("DATA_SILVER_DIR", "data/silver")
        self.data_gold_dir: Path = PROJECT_ROOT / os.getenv("DATA_GOLD_DIR", "data/gold")
        self.data_reference_dir: Path = PROJECT_ROOT / os.getenv("DATA_REFERENCE_DIR", "data/reference")

        # Logging Parameters
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
        self.log_dir: Path = PROJECT_ROOT / os.getenv("LOG_DIR", "logs")
        self.log_file_name: str = os.getenv("LOG_FILE_NAME", "northstar_pipeline.log")
        self.log_rotation_bytes: int = int(os.getenv("LOG_ROTATION_BYTES", "10485760"))  # 10 MB
        self.log_backup_count: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))

        # Cryptographic Pseudonymization (Provisional BDL-05, FR-014)
        self.hmac_pepper_secret: Optional[str] = os.getenv("HMAC_PEPPER_SECRET", None)

        # Operational Thresholds (Configurable BDL-06)
        self.param_discrepancy_threshold: float = float(os.getenv("PARAM_DISCREPANCY_THRESHOLD", "500.0"))

        # Timezone & Cadence
        self.pipeline_timezone: str = os.getenv("PIPELINE_TIMEZONE", "Asia/Kolkata")
        self.batch_start_time_ist: str = os.getenv("BATCH_START_TIME_IST", "01:00")
        self.dsr_delivery_time_ist: str = os.getenv("DSR_DELIVERY_TIME_IST", "06:00")

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_staging(self) -> bool:
        return self.app_env == "staging"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def ensure_directories(self) -> None:
        """Ensures that required local runtime data and log directories exist."""
        for directory in [
            self.data_raw_dir,
            self.data_bronze_dir,
            self.data_silver_dir,
            self.data_gold_dir,
            self.data_reference_dir,
            self.log_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Returns a singleton cached instance of the application Settings."""
    settings = Settings()
    settings.ensure_directories()
    return settings

