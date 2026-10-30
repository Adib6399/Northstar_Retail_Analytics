"""
Northstar Retail Analytics Platform — Environment & Configuration Unit Tests
Validates the repository foundation, directory structure, environment configuration,
and logging redaction filters.
"""

import sys
import logging
import unittest
from pathlib import Path
from config.base import get_settings, PROJECT_ROOT
from config.database import get_database_url
from config.logging_config import setup_logging, PIIRedactionFilter


class TestEnvironmentSetup(unittest.TestCase):
    """Test suite validating repository structure, environment settings, and security filters."""

    def test_python_version(self):
        """Ensure Python version is 3.11 or higher."""
        self.assertGreaterEqual(
            (sys.version_info.major, sys.version_info.minor),
            (3, 11),
            f"Python version must be >= 3.11, found: {sys.version}",
        )

    def test_directory_structure_exists(self):
        """Verify that all core project directories exist."""
        required_dirs = [
            "config",
            "data/raw",
            "data/bronze",
            "data/silver",
            "data/gold",
            "data/reference",
            "ingestion",
            "transformations",
            "reconciliation",
            "analytics",
            "forecasting",
            "tests",
            "logs",
            "scripts",
            "dbt_project",
            "docker",
            "docs/01_business_discovery",
            "docs/02_requirements_engineering",
            "docs/03_business_process_modeling",
            "docs/04_technical_architecture",
            "docs/05_data_engineering",
        ]
        for rel_path in required_dirs:
            dir_path = PROJECT_ROOT / rel_path
            self.assertTrue(dir_path.is_dir(), f"Expected directory missing: {rel_path}")

    def test_settings_initialization(self):
        """Verify application settings initialize and parse environment defaults."""
        settings = get_settings()
        self.assertEqual(settings.app_name, "Northstar_Retail_Analytics")
        self.assertEqual(settings.postgres_port, 5432)
        self.assertEqual(settings.param_discrepancy_threshold, 500.0)
        self.assertEqual(settings.pipeline_timezone, "Asia/Kolkata")
        self.assertTrue(settings.is_development)

    def test_database_url_generation(self):
        """Verify standard database URL construction and password masking."""
        url_masked = get_database_url(hide_password=True)
        self.assertIn("postgresql+psycopg://", url_masked)
        self.assertIn("••••••••", url_masked)

        url_unmasked = get_database_url(hide_password=False)
        self.assertIn("postgresql+psycopg://", url_unmasked)
        self.assertNotIn("••••••••", url_unmasked)

    def test_pii_redaction_logging_filter(self):
        """Verify that phone numbers and passwords are scrubbed from log messages."""
        pii_filter = PIIRedactionFilter()

        # Test phone number scrubbing
        record_phone = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py", lineno=1,
            msg="Customer mobile number is 9845012345 for transaction", args=(), exc_info=None
        )
        pii_filter.filter(record_phone)
        self.assertNotIn("9845012345", record_phone.msg)
        self.assertIn("[REDACTED_PHONE]", record_phone.msg)

        # Test password scrubbing
        record_pwd = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py", lineno=1,
            msg="Connecting with password='super_secret_db_pass' to database", args=(), exc_info=None
        )
        pii_filter.filter(record_pwd)
        self.assertNotIn("super_secret_db_pass", record_pwd.msg)
        self.assertIn("password=[REDACTED]", record_pwd.msg)

    def test_docker_compose_exists(self):
        """Verify docker-compose.yml exists and contains postgres service definition."""
        compose_path = PROJECT_ROOT / "docker-compose.yml"
        self.assertTrue(compose_path.exists(), "docker-compose.yml must exist")
        content = compose_path.read_text(encoding="utf-8")
        self.assertIn("postgres:16-alpine", content)
        self.assertIn("northstar_postgres_dev", content)
        self.assertIn("healthcheck:", content)


if __name__ == "__main__":
    unittest.main()

