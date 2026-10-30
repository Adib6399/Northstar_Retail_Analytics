"""
Northstar Retail Analytics Platform — Logging Configuration
Establishes structured, rotating file and console logging with automatic PII redaction filters.
Enforces that no sensitive personal data (phone numbers, passwords) is ever written to disk.
"""

import logging
import logging.handlers
import re
from pathlib import Path
from config.base import get_settings


class PIIRedactionFilter(logging.Filter):
    """
    Security filter that scrubs sensitive customer PII and credential patterns
    from log records before writing to disk or console.

    IMPORTANT ARCHITECTURAL NOTICE:
    Regex-based redaction is a defense-in-depth sanitization safeguard and NOT
    a complete or foolproof PII protection system. Unstructured text, non-standard
    formats, or encoded data can bypass pattern matching. The primary protection
    remains strict pipeline data minimization, immediate pseudonymization
    (Keyed HMAC-SHA256 per BDL-05/FR-014), and never passing sensitive PII to loggers.
    """

    # 10-digit Indian mobile numbers (starting with 6-9)
    PHONE_REGEX = re.compile(r"\b[6-9]\d{9}\b")
    # Email addresses
    EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    # Password parameters in key-value or query string formats
    PASSWORD_REGEX = re.compile(r"(password=['\"][^'\"]+['\"]|password=[^\s&]+)", re.IGNORECASE)
    # Database connection URIs containing credentials (e.g. postgresql://user:pass@host)
    URI_PASSWORD_REGEX = re.compile(r"://([^:]+):([^@]+)@")
    # 16-digit payment card patterns
    CARD_REGEX = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.PHONE_REGEX.sub("[REDACTED_PHONE]", record.msg)
            record.msg = self.EMAIL_REGEX.sub("[REDACTED_EMAIL]", record.msg)
            record.msg = self.PASSWORD_REGEX.sub("password=[REDACTED]", record.msg)
            record.msg = self.URI_PASSWORD_REGEX.sub(r"://\1:[REDACTED]@", record.msg)
            record.msg = self.CARD_REGEX.sub("[REDACTED_CARD]", record.msg)
        return True


def setup_logging(name: str = "northstar") -> logging.Logger:
    """
    Configures and returns an application logger with console and rotating file handlers.
    """
    settings = get_settings()
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if already configured
    if logger.hasHandlers():
        return logger

    log_level = getattr(logging, settings.log_level, logging.INFO)
    logger.setLevel(log_level)

    # Standard enterprise log format with IST timestamp indicator
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | [%(name)s:%(module)s:%(lineno)d] | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S IST",
    )

    # 1. Console Handler (stdout)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(PIIRedactionFilter())
    logger.addHandler(console_handler)

    # 2. Rotating File Handler
    try:
        settings.log_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = settings.log_dir / settings.log_file_name
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_file_path),
            maxBytes=settings.log_rotation_bytes,
            backupCount=settings.log_backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(PIIRedactionFilter())
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning("Could not initialize file logging handler: %s", e)

    return logger

