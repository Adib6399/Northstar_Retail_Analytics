"""
Northstar Retail Analytics Platform — Environment & Configuration Test Suite
Provides test cases across configuration, directory foundation, logging security,
Docker compose specifications, and database connectivity.
"""

import os
import sys
import logging
import unittest
from pathlib import Path
from unittest.mock import patch
from config.base import Settings, get_settings, PROJECT_ROOT
from config.database import get_database_url, check_database_connectivity
from config.logging_config import setup_logging, PIIRedactionFilter


class TestConfigurationAndSettings(unittest.TestCase):
    """Category 1: Configuration & Runtime Environment Tests."""

    def test_python_runtime_compatibility(self):
        """Ensure Python runtime is >= 3.11."""
        self.assertGreaterEqual(
            (sys.version_info.major, sys.version_info.minor),
            (3, 11),
            f"Python runtime must be >= 3.11, detected: {sys.version}",
        )

    def test_settings_initialization(self):
        """Verify application settings initialize and parse environment configuration."""
        settings = get_settings()
        self.assertEqual(settings.app_name, "Northstar_Retail_Analytics")
        expected_port = int(os.getenv("POSTGRES_PORT", "5432"))
        self.assertEqual(settings.postgres_port, expected_port)
        self.assertEqual(settings.param_discrepancy_threshold, 500.0)
        self.assertEqual(settings.pipeline_timezone, "Asia/Kolkata")
        self.assertTrue(settings.is_development)

    def test_default_postgres_port_without_override(self):
        """Verify default PostgreSQL port is 5432 when no environment override exists."""
        with patch.dict(os.environ):
            os.environ.pop("POSTGRES_PORT", None)
            settings = Settings()
            self.assertEqual(settings.postgres_port, 5432)

    def test_explicit_postgres_port_override(self):
        """Verify PostgreSQL port is overridden when POSTGRES_PORT is explicitly set in environment."""
        with patch.dict(os.environ, {"POSTGRES_PORT": "5433"}):
            settings = Settings()
            self.assertEqual(settings.postgres_port, 5433)

    def test_database_url_generation(self):
        """Verify standard database URL construction and password masking."""
        url_masked = get_database_url(hide_password=True)
        self.assertIn("postgresql+psycopg://", url_masked)
        self.assertIn("••••••••", url_masked)

        url_unmasked = get_database_url(hide_password=False)
        self.assertIn("postgresql+psycopg://", url_unmasked)
        self.assertNotIn("••••••••", url_unmasked)


class TestDirectoryFoundation(unittest.TestCase):
    """Category 2: Repository Structure & Directory Foundation Tests."""

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

    def test_gitkeep_files_exist(self):
        """Verify .gitkeep files exist in data subdirectories and logs."""
        gitkeep_dirs = ["data/raw", "data/bronze", "data/silver", "data/gold", "data/reference", "logs"]
        for rel_path in gitkeep_dirs:
            gitkeep_path = PROJECT_ROOT / rel_path / ".gitkeep"
            self.assertTrue(gitkeep_path.is_file(), f"Missing .gitkeep in: {rel_path}")


class TestLoggingSecurityRedaction(unittest.TestCase):
    """Category 3: Logging Security & Privacy Redaction Tests (Audit 6)."""

    def setUp(self):
        self.pii_filter = PIIRedactionFilter()

    def test_phone_number_redaction(self):
        """Verify 10-digit Indian mobile numbers are scrubbed."""
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py", lineno=1,
            msg="Customer mobile is 9845012345 for transaction", args=(), exc_info=None
        )
        self.pii_filter.filter(record)
        self.assertNotIn("9845012345", record.msg)
        self.assertIn("[REDACTED_PHONE]", record.msg)

    def test_email_address_redaction(self):
        """Verify customer and employee email addresses are scrubbed."""
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py", lineno=1,
            msg="Dispatching DSR to regional_lead@northstar.in and finance@company.com", args=(), exc_info=None
        )
        self.pii_filter.filter(record)
        self.assertNotIn("regional_lead@northstar.in", record.msg)
        self.assertNotIn("finance@company.com", record.msg)
        self.assertEqual(record.msg.count("[REDACTED_EMAIL]"), 2)

    def test_password_parameter_redaction(self):
        """Verify password key-value parameters are scrubbed."""
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py", lineno=1,
            msg="Connecting with password='super_secret_db_pass' to host", args=(), exc_info=None
        )
        self.pii_filter.filter(record)
        self.assertNotIn("super_secret_db_pass", record.msg)
        self.assertIn("password=[REDACTED]", record.msg)

    def test_database_uri_password_redaction(self):
        """Verify database URIs containing credentials in exceptions are scrubbed."""
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="test.py", lineno=1,
            msg="Connection failed for postgresql+psycopg://dbuser:mypassword123@localhost:5432/northstar_dev",
            args=(), exc_info=None
        )
        self.pii_filter.filter(record)
        self.assertNotIn("mypassword123", record.msg)
        self.assertIn("://dbuser:[REDACTED]@", record.msg)

    def test_payment_card_redaction(self):
        """Verify 16-digit card-like patterns are scrubbed."""
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py", lineno=1,
            msg="POS tender transaction card number 4111 2222 3333 4444 approved", args=(), exc_info=None
        )
        self.pii_filter.filter(record)
        self.assertNotIn("4111 2222 3333 4444", record.msg)
        self.assertIn("[REDACTED_CARD]", record.msg)


class TestDockerComposeSpecification(unittest.TestCase):
    """Category 4: Docker Compose Manifest Tests."""

    def test_docker_compose_structure(self):
        """Verify docker-compose.yml defines postgres 16 service, volume, and health check."""
        compose_path = PROJECT_ROOT / "docker-compose.yml"
        self.assertTrue(compose_path.exists(), "docker-compose.yml must exist")
        content = compose_path.read_text(encoding="utf-8")
        self.assertIn("postgres:16-alpine", content)
        self.assertIn("northstar_postgres_dev", content)
        self.assertIn("healthcheck:", content)
        self.assertIn("postgres_data:", content)


class TestDatabaseIntegration(unittest.TestCase):
    """Category 5: Database Integration Tests (Conditional / Live Execution)."""

    def test_database_live_connection(self):
        """Test live database connectivity if PostgreSQL container is running."""
        connected, msg = check_database_connectivity()
        if not connected:
            self.skipTest(f"PostgreSQL container is not running on host (NOT EXECUTED: {msg})")
        self.assertTrue(connected)


if __name__ == "__main__":
    unittest.main()
