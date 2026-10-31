"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.3: Historical Sales Fact Generation Pipeline CLI

Executes synthetic historical sales generation for INTEGRATION (or DEV) profile
with automated post-load quality validation and idempotency verification.
Strictly adheres to Stage 5.3.3 governance boundaries: populates gold.fact_sales only.
"""

import sys
from pathlib import Path

# Ensure project root is prioritized and script directory does not shadow top-level config package
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
script_dir = str(Path(__file__).resolve().parent)
if script_dir in sys.path:
    sys.path.remove(script_dir)

import argparse
import time
from sqlalchemy import text
from config.database import get_db_engine, check_database_connectivity
from scripts.data_generation.config import ProfileType, get_profile_config
from scripts.data_generation.loaders.sales_loader import SalesLoader
from scripts.data_generation.validators.sales_validator import SalesValidator


def run_pipeline(profile: ProfileType = ProfileType.INTEGRATION, test_idempotency: bool = True):
    print("=" * 80)
    print(f"NORTHSTAR RETAIL GROUP — STAGE 5.3.3 SALES DATA GENERATION: {profile.value}")
    print("=" * 80)

    # 1. Pre-flight connectivity and boundary verification
    ok, msg = check_database_connectivity()
    if not ok:
        print(f"[FATAL] Database connectivity check failed: {msg}")
        sys.exit(1)
    print(f"[PRE-FLIGHT] Database connectivity verified: {msg}")

    config = get_profile_config(profile)
    loader = SalesLoader()
    validator = SalesValidator()

    print(f"\n1. Ingesting {profile.value} Historical Sales Data ({config.sales_line_items:,} rows)...")
    load_metrics = loader.load_sales(config, chunk_size=5000, log_interval_days=10)

    print("\n   Load Execution Metrics:")
    for k, v in load_metrics.items():
        print(f"     - {k}: {v}")

    print(f"\n2. Validating {profile.value} Sales Data Quality, Constraints, and Accounting...")
    is_valid, errors, metrics = validator.validate_profile(profile)

    if not is_valid:
        print("\n[FAILED] VALIDATION DEFECTS DETECTED:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    print("\n[SUCCESS] ALL VALIDATION CHECKS PASSED:")
    print(f"  - Total fact_sales rows: {metrics.get('fact_sales_row_count', 0):,}")
    print(f"  - Distinct stores covered: {metrics.get('distinct_stores_covered', 0)} of {config.store_count}")
    print(f"  - Distinct products covered: {metrics.get('distinct_products_covered', 0)} of {config.product_count}")
    print(f"  - Distinct dates covered: {metrics.get('distinct_dates_covered', 0)} of {config.generation_days}")
    print(f"  - Duplicate business keys: {metrics.get('duplicate_business_keys', 0)}")

    totals = metrics.get("financial_totals", {})
    print("\n   Financial Summary:")
    print(f"     - Gross Sales INR:   ₹{totals.get('total_gross_sales', 0):,.2f}")
    print(f"     - Discount INR:      ₹{totals.get('total_discount', 0):,.2f}")
    print(f"     - Net Taxable INR:   ₹{totals.get('total_taxable', 0):,.2f}")
    print(f"     - GST Tax INR:       ₹{totals.get('total_tax', 0):,.2f}")
    print(f"     - Net Sales INR:     ₹{totals.get('total_net_sales', 0):,.2f}")
    print(f"     - Standard Cost INR: ₹{totals.get('total_cost', 0):,.2f}")
    print(f"     - Gross Margin INR:  ₹{totals.get('total_margin', 0):,.2f} ({totals.get('avg_margin_pct', 0):.2f}%)")

    # 3. Idempotency Verification
    if test_idempotency:
        print("\n3. Testing Idempotency (Re-running generation and load)...")
        t_idempotent_0 = time.time()
        second_load_metrics = loader.load_sales(config, chunk_size=5000, log_interval_days=46)
        idempotent_duration = time.time() - t_idempotent_0

        is_valid_2, errors_2, metrics_2 = validator.validate_profile(profile)
        if not is_valid_2:
            print("\n[FAILED] IDEMPOTENCY CHECK FAILED (Validation errors after rerun):")
            for err in errors_2:
                print(f"  - {err}")
            sys.exit(1)

        row_count_after_rerun = metrics_2.get("fact_sales_row_count", 0)
        if row_count_after_rerun != config.sales_line_items:
            print(
                f"\n[FAILED] IDEMPOTENCY VIOLATION: Row count changed from {config.sales_line_items:,} "
                f"to {row_count_after_rerun:,}"
            )
            sys.exit(1)

        print(f"\n[IDEMPOTENT] Re-run completed in {idempotent_duration:.1f}s.")
        print(f"  - Final fact_sales count: {row_count_after_rerun:,} (Zero duplicates created)")
        print("  - All data quality rules and accounting assertions remain 100% compliant.")

    print("\n" + "=" * 80)
    print("STAGE 5.3.3 SALES DATA GENERATION COMPLETE AND VERIFIED")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Northstar Stage 5.3.3 Historical Sales Generator CLI")
    parser.add_argument(
        "--profile",
        type=str,
        default="INTEGRATION",
        choices=["DEV", "INTEGRATION"],
        help="Target generation profile (default: INTEGRATION)",
    )
    parser.add_argument(
        "--skip-idempotency",
        action="store_true",
        help="Skip secondary execution idempotency verification",
    )

    args = parser.parse_args()
    target_profile = ProfileType(args.profile)
    run_pipeline(profile=target_profile, test_idempotency=not args.skip_idempotency)

