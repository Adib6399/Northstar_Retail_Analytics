#!/usr/bin/env python3
"""
Northstar Retail Analytics Platform — Environment Verification Utility
Validates the local development environment setup, dependencies, directory structure,
Git configuration, environment variables, and database connectivity.
"""

import sys
import os
import shutil
import subprocess
from pathlib import Path

# Add project root to Python sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def print_header(title: str) -> None:
    print(f"\n{'=' * 75}")
    print(f"  {title}")
    print(f"{'=' * 75}")


def check_python_version() -> bool:
    print_header("1. Python Version Check & Compatibility Evaluation")
    major = sys.version_info.major
    minor = sys.version_info.minor
    micro = sys.version_info.micro
    version_str = f"{major}.{minor}.{micro}"
    print(f"Detected Host Python: {version_str} ({sys.executable})")

    if major == 3 and minor >= 11:
        print("  -> RUNTIME CHECK: Python runtime meets minimum platform requirement (>= 3.11).")
        if minor == 14:
            print("  -> COMPATIBILITY FINDING: Python 3.14 lacks upstream binary wheel support for dbt-core 1.7+")
            print("     and compiled extensions (psycopg/pandas).")
            print("  -> RECOMMENDED BASELINE: Python 3.12.x established as authoritative implementation baseline.")
        return True
    else:
        print("  -> FAIL: Python version does not meet requirement (>= 3.11).")
        return False


def check_directory_structure() -> bool:
    print_header("2. Repository Directory Structure Check")
    required_dirs = [
        "docs/01_business_discovery",
        "docs/02_requirements_engineering",
        "docs/03_business_process_modeling",
        "docs/04_technical_architecture",
        "docs/05_data_engineering",
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
    ]

    all_ok = True
    for rel_path in required_dirs:
        dir_path = PROJECT_ROOT / rel_path
        if dir_path.is_dir():
            print(f"  [OK] {rel_path}/")
        else:
            print(f"  [MISSING] {rel_path}/")
            all_ok = False

    return all_ok


def check_core_packages() -> dict:
    print_header("3. Python Package Import Check")
    packages = [
        ("pandas", "Pandas"),
        ("sqlalchemy", "SQLAlchemy"),
        ("psycopg", "Psycopg 3"),
        ("dotenv", "python-dotenv"),
        ("pydantic", "Pydantic"),
        ("yaml", "PyYAML"),
        ("pytest", "Pytest"),
        ("requests", "Requests"),
        ("dbt", "dbt Core"),
    ]

    results = {}
    for mod_name, label in packages:
        try:
            mod = __import__(mod_name)
            version = getattr(mod, "__version__", "installed")
            print(f"  [INSTALLED] {label:18} -> Version: {version}")
            results[label] = True
        except ImportError:
            print(f"  [NOT INSTALLED] {label:18} -> Run: pip install -r requirements.txt")
            results[label] = False

    return results


def check_configuration_loading() -> bool:
    print_header("4. Configuration & Environment Variables Check")
    try:
        from config.base import get_settings
        settings = get_settings()
        print(f"  APP_ENV:               {settings.app_env}")
        print(f"  APP_NAME:              {settings.app_name}")
        print(f"  Database Host:         {settings.postgres_host}:{settings.postgres_port}")
        print(f"  Database Name:         {settings.postgres_db}")
        print(f"  Database User:         {settings.postgres_user}")
        print(f"  Discrepancy Threshold: ₹{settings.param_discrepancy_threshold:.2f}")
        print(f"  Pipeline Timezone:     {settings.pipeline_timezone}")
        print("  -> PASS: Settings loaded and parsed successfully.")
        return True
    except Exception as e:
        print(f"  -> FAIL: Configuration loading error: {e}")
        return False


def check_git_status() -> bool:
    print_header("5. Version Control (Git) Status Check")
    git_bin = shutil.which("git")
    if not git_bin:
        print("  -> FAIL: Git executable not found in PATH.")
        return False

    git_dir = PROJECT_ROOT / ".git"
    if not git_dir.exists():
        print("  -> WARNING: .git directory not found (Git repository not yet initialized).")
        return False

    try:
        res = subprocess.run(["git", "status", "--short"], cwd=PROJECT_ROOT, capture_output=True, text=True)
        print(f"  Git status return code: {res.returncode}")
        tracked_count = len(res.stdout.strip().split("\n")) if res.stdout.strip() else 0
        print(f"  Pending untracked / modified items: {tracked_count}")
        print("  -> PASS: Git repository initialized.")
        return True
    except Exception as e:
        print(f"  -> ERROR querying Git: {e}")
        return False


def check_docker_availability() -> bool:
    print_header("6. Docker & Docker Compose Check")
    docker_bin = shutil.which("docker")
    compose_file = PROJECT_ROOT / "docker-compose.yml"

    if compose_file.exists():
        print(f"  [OK] docker-compose.yml configuration present at {compose_file.name}")
    else:
        print("  [MISSING] docker-compose.yml not found.")

    if docker_bin:
        print(f"  [OK] Docker executable found at: {docker_bin}")
        try:
            res = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            print(f"  Docker version: {res.stdout.strip()}")
            return True
        except Exception as e:
            print(f"  Could not execute docker command: {e}")
            return False
    else:
        print("  [NOTE] Docker binary not found in current PATH.")
        print("  Local PostgreSQL container requires Docker Desktop or an external PostgreSQL 16+ instance.")
        return False


def check_database_connection() -> bool:
    print_header("7. PostgreSQL Database Connectivity Check")
    try:
        from config.database import check_database_connectivity
        connected, msg = check_database_connectivity()
        if connected:
            print(f"  [PASS] {msg}")
            return True
        else:
            print(f"  [INFO] {msg}")
            print("  Note: This is expected if the PostgreSQL container is not currently running.")
            return False
    except Exception as e:
        print(f"  [ERROR] Database check failed: {e}")
        return False


def main():
    print(f"\nStarting Northstar Retail Analytics Stage 5.1 Environment Audit...")
    py_ok = check_python_version()
    dir_ok = check_directory_structure()
    pkg_results = check_core_packages()
    cfg_ok = check_configuration_loading()
    git_ok = check_git_status()
    docker_ok = check_docker_availability()
    db_ok = check_database_connection()

    print_header("Stage 5.1 Verification Audit Summary")
    print(f"  Python 3.11+ Runtime:      {'PASS' if py_ok else 'FAIL'}")
    print(f"  Directory Foundation:      {'PASS' if dir_ok else 'FAIL'}")
    print(f"  Configuration Management:  {'PASS' if cfg_ok else 'FAIL'}")
    print(f"  Git Initialization:        {'PASS' if git_ok else 'ATTENTION NEEDED'}")
    print(f"  Docker Host Runtime:       {'AVAILABLE' if docker_ok else 'NOT DETECTED IN PATH'}")
    print(f"  PostgreSQL Live Connection:{'CONNECTED' if db_ok else 'NOT RUNNING (EXPECTED IN LOCAL PREP)'}")
    print(f"{'=' * 75}\n")


if __name__ == "__main__":
    main()

