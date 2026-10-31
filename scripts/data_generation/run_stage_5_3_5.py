"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.5: Marketing & Reconciliation Data Generation Orchestrator

Sequentially executes:
  1. Substage A: gold.fact_marketing_performance (1,840 rows)
  2. Substage B: control.control_campaign_assignment_registry (50,000 rows)
                 gold.fact_campaign_exposure (50,000 rows)
  3. Substage C: gold.fact_reconciliation (11,040 rows)

Includes automated validation and idempotency verification.
"""

import sys
from pathlib import Path

# Prioritize project root and prevent script directory from shadowing top-level packages
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
from scripts.data_generation.loaders.stage_5_3_5_loader import Stage535Loader
from scripts.data_generation.validators.stage_5_3_5_validator import Stage535Validator


def run_pipeline(profile: ProfileType = ProfileType.INTEGRATION, test_idempotency: bool = True):
    print("=" * 80)
    print(f"NORTHSTAR RETAIL GROUP — STAGE 5.3.5 GENERATION: {profile.value}")
    print("MARKETING PERFORMANCE, CAMPAIGN EXPOSURES & 4-WAY RECONCILIATION")
    print("=" * 80)

    # 1. Connectivity Check
    ok, msg = check_database_connectivity()
    if not ok:
        print(f"[FATAL] Database connection failed: {msg}")
        sys.exit(1)
    print(f"[PRE-FLIGHT] Database connection verified: {msg}")

    config = get_profile_config(profile)
    loader = Stage535Loader()
    validator = Stage535Validator()

    t_total_0 = time.time()
    context = loader.fetch_master_context(config)

    # Substage A: Marketing Performance
    t_mktg_0 = time.time()
    res_mktg = loader.load_marketing_performance(config, context, chunk_size=2000)

    # Substage B: Exposures & Registry
    t_exp_0 = time.time()
    res_exp = loader.load_campaign_exposures_and_registry(config, context, chunk_size=5000)

    # Substage C: Reconciliations
    t_rcn_0 = time.time()
    res_rcn = loader.load_reconciliations(config, context, chunk_size=5000)

    total_load_duration = time.time() - t_total_0

    print("\n" + "=" * 80)
    print("STAGE 5.3.5 ALL 3 SUBSTAGES INGESTION COMPLETE")
    print("=" * 80)
    print(f"  1. Marketing Perf: {res_mktg['rows_inserted']:,} rows in {res_mktg['duration_seconds']}s ({res_mktg['rows_per_second']:,} rows/s)")
    print(f"  2. Registry/Exp:   {res_exp['rows_inserted']:,} rows each in {res_exp['duration_seconds']}s ({res_exp['rows_per_second']:,} rows/s)")
    print(f"  3. Reconciliation: {res_rcn['rows_inserted']:,} rows in {res_rcn['duration_seconds']}s ({res_rcn['rows_per_second']:,} rows/s)")
    print(f"  Total Ingestion Time: {total_load_duration:.1f} seconds")

    # 2. Comprehensive Validation
    print("\nValidating Data Quality, Accounting Identities, and Boundaries...")
    is_valid, errors, metrics = validator.validate_all(profile)

    if not is_valid:
        print("\n[FAILED] VALIDATION DEFECTS DETECTED:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    print("\n[SUCCESS] ALL VALIDATION CHECKS PASSED (100% COMPLIANT):")
    counts = metrics.get("fact_row_counts", {})
    for tbl, act_cnt in counts.items():
        print(f"  - {tbl:<36}: {act_cnt:>10,} rows")

    mktg_s = metrics.get("marketing_summary", {})
    print("\n  Marketing Performance Metrics:")
    print(f"    - Attributed Spend:     ₹{mktg_s.get('total_spend', 0):,.2f}")
    print(f"    - Incremental Lift:     ₹{mktg_s.get('total_lift', 0):,.2f}")
    print(f"    - Incremental Margin:   ₹{mktg_s.get('total_incremental_margin', 0):,.2f}")
    print(f"    - Average ROMI Ratio:   {mktg_s.get('avg_romi', 0)}")

    print("\n  Campaign Exposure & Holdout Metrics:")
    for h in metrics.get("holdout_distribution", []):
        group_name = "CONTROL (Holdout)" if h["is_holdout_control_flag"] else "TREATMENT (Dispatched)"
        print(f"    - {group_name:<24}: {h['assignment_count']:,} assignments ({h['pct_of_total']}%)")
    red_s = metrics.get("exposure_redemptions", {})
    print(f"    - Coupon Redemptions:    {red_s.get('redeemed_coupons', 0):,} (Avg lag: {red_s.get('avg_lag_days', 0)} days)")

    print("\n  4-Way Reconciliation Metrics:")
    for d in metrics.get("reconciliation_domain_counts", []):
        print(f"    - Domain {d['recon_domain_key']}: {d['audit_count']:,} audits")
    print(f"    - Pending Review Tickets: {metrics.get('pending_review_tickets', 0):,} (Exercising partial index)")

    # 3. Idempotency Check
    if test_idempotency:
        print("\n3. Testing Idempotency (Re-running generation and load)...")
        t_idem_0 = time.time()
        loader.load_marketing_performance(config, context, chunk_size=2000)
        loader.load_campaign_exposures_and_registry(config, context, chunk_size=5000)
        loader.load_reconciliations(config, context, chunk_size=5000)
        idem_duration = time.time() - t_idem_0

        is_valid_2, errors_2, metrics_2 = validator.validate_all(profile)
        if not is_valid_2:
            print("\n[FAILED] IDEMPOTENCY CHECK FAILED:")
            for err in errors_2:
                print(f"  - {err}")
            sys.exit(1)

        counts_2 = metrics_2.get("fact_row_counts", {})
        for tbl, exp_cnt in counts.items():
            if counts_2.get(tbl) != exp_cnt:
                print(f"\n[FAILED] IDEMPOTENCY ROW COUNT CHANGED in {tbl}: {exp_cnt} -> {counts_2.get(tbl)}")
                sys.exit(1)

        print(f"\n[IDEMPOTENT] Re-run completed in {idem_duration:.1f}s.")
        print("  - All table row counts remain strictly unchanged (Zero duplicates created).")
        print("  - All data quality rules and reconciliation assertions remain 100% compliant.")

    print("\n" + "=" * 80)
    print("STAGE 5.3.5 GENERATION COMPLETE AND VERIFIED")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Northstar Stage 5.3.5 Data Generation CLI")
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
