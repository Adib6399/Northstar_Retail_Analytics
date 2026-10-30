"""
Northstar Retail Analytics Platform — Database Configuration
Provides database connection factories, SQLAlchemy engines, and connection health checks.
Strictly separates configuration from physical DDL implementation.
"""

from typing import Tuple, Optional
from urllib.parse import quote_plus
from config.base import get_settings


def get_database_url(hide_password: bool = False) -> str:
    """
    Constructs the standard PostgreSQL connection URI from environment settings.
    Uses psycopg 3 / SQLAlchemy protocol format.
    """
    settings = get_settings()
    user = quote_plus(settings.postgres_user)
    password = "••••••••" if hide_password else quote_plus(settings.postgres_password)
    host = settings.postgres_host
    port = settings.postgres_port
    db = settings.postgres_db
    sslmode = settings.postgres_sslmode

    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}?sslmode={sslmode}"


def get_db_engine(pool_size: int = 5, max_overflow: int = 10, pool_timeout: int = 30):
    """
    Factory creating a SQLAlchemy Engine configured with connection pooling.
    Deferred import ensures scripts can load settings even without SQLAlchemy installed.
    """
    try:
        from sqlalchemy import create_engine
    except ImportError as e:
        raise ImportError(
            "SQLAlchemy is required to create a database engine. "
            "Install dependencies via: pip install -r requirements.txt"
        ) from e

    url = get_database_url(hide_password=False)
    settings = get_settings()

    engine = create_engine(
        url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        echo=settings.is_development and False,  # Keep SQL echo off by default for clean logs
        future=True,
    )
    return engine


def check_database_connectivity() -> Tuple[bool, str]:
    """
    Performs a lightweight connectivity check against the configured PostgreSQL instance.
    Executes 'SELECT 1;' to verify database availability.
    Returns (status: bool, message: str).
    """
    settings = get_settings()
    masked_url = get_database_url(hide_password=True)

    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(
            get_database_url(hide_password=False),
            connect_args={"connect_timeout": 5},
            future=True,
        )
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 AS healthcheck;")).scalar()
            if result == 1:
                return True, f"Successfully connected to PostgreSQL at {masked_url} (Health check passed: SELECT 1)"
            return False, f"Unexpected response from PostgreSQL: {result}"
    except ImportError:
        # Fallback to direct socket or psycopg attempt
        try:
            import psycopg
            conn_info = (
                f"host={settings.postgres_host} port={settings.postgres_port} "
                f"dbname={settings.postgres_db} user={settings.postgres_user} "
                f"password={settings.postgres_password} connect_timeout=5"
            )
            with psycopg.connect(conn_info) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
                    val = cur.fetchone()[0]
                    if val == 1:
                        return True, f"Successfully connected to PostgreSQL via psycopg at {masked_url}"
        except ImportError:
            return False, "Neither SQLAlchemy nor psycopg is installed in the current environment."
        except Exception as e:
            return False, f"PostgreSQL connection failed ({masked_url}): {type(e).__name__}: {str(e)}"
    except Exception as e:
        return False, f"PostgreSQL connection failed ({masked_url}): {type(e).__name__}: {str(e)}"

    return False, f"Unable to establish database connection to {masked_url}"
