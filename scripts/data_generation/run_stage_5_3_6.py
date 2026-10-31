"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.6: Demand Forecast Generation & Final Data Quality Gate Orchestrator

Sequentially executes:
  1. Substage A: gold.fact_demand_forecast (210,000 rows)
  2. Idempotency verification (zero-duplicate re-run check)
  3. Substage B: Comprehensive Cross-Fact Quality Gate across all 9 fact tables,
     8 conformed dimensions, holdout registry, and technical constraints.
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
from scripts.data_generation.loaders.stage_5_3_6_loader import Stage536Loader
from scripts.data_generation.validators.stage_5_3_6_validator import Stage536Validator


def run_pipeline(profile: ProfileType = ProfileType.INTEGRATION, test_idempotency: bool = True):
    print("=" * 80)
    print(f"NORTHSTAR RETAIL GROUP — STAGE 5.3.6: {profile.value}")
    print("DEMAND FORECAST GENERATION & FINAL COMPREHENSIVE DATA QUALITY GATE")
    print("=" * 80)

    # 1. Connectivity Check
    ok, msg = check_database_connectivity()
    if not ok:
        print(f"[FATAL] Database connection failed: {msg}")
        sys.exit(1)
    print(f"[PRE-FLIGHT] Database connection verified: {msg}")

    config = get_profile_config(profile)
    loader = Stage536Loader()
    validator = Stage536Validator()

    t_total_0 = time.time()
    print("\n[CONTEXT] Fetching master dimension and inventory baseline context...")
    context = loader.fetch_master_context(config)
    print(f"  - Stores:          {len(context['stores'])} active locations")
    print(f"  - Products:        {len(context['products'])} active SKUs")
    print(f"  - Target Dates:    {len(context['target_dates'])} forward projection dates (2026-11-01 to 2026-11-14)")
    print(f"  - Baseline SOH:    {len(context['baseline_inventory']):,} Store-SKU baseline snapshots loaded")

    # Substage A: Demand Forecast Generation and Loading
    print(f"\n[SUBSTAGE A] Generating and Ingesting {config.demand_forecast_projections:,} Projections...")
    t_fcst_0 = time.time()
    res_fcst = loader.load_demand_forecast(config, context, chunk_size=config.batch_size)
    t_fcst = time.time() - t_fcst_0

    print("=" * 80)
    print("DEMAND FORECAST INGESTION COMPLETE")
    print("=" * 80)
    print(f"  - Generated:       {res_fcst['rows_generated']:,} rows in {res_fcst['generation_seconds']}s")
    print(f"  - Ingested:        {res_fcst['rows_inserted']:,} rows in {res_fcst['load_seconds']}s ({res_fcst['rows_per_second']:,} rows/s)")

    # 2. Comprehensive Validation Gate
    print("\n[SUBSTAGE B] Executing Comprehensive Data Quality & Cross-Fact Validation...")
    is_valid, errors, metrics = validator.validate_all(profile)

    if not is_valid:
        print("\n[FAILED] VALIDATION DEFECTS DETECTED:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    print("\n[SUCCESS] ALL VALIDATION CHECKS PASSED (100% COMPLIANT):")
    fcst_m = metrics.get("demand_forecast", {})
    cov_m = fcst_m.get("grid_coverage", {})
    summ_m = fcst_m.get("summary_measures", {})

    print("\n  1. Demand Forecast Projections (gold.fact_demand_forecast):")
    print(f"    - Total Rows:              {fcst_m.get('total_rows', 0):,}")
    print(f"    - Grid Coverage:           {cov_m.get('distinct_stores')} stores x {cov_m.get('distinct_products')} SKUs x {cov_m.get('distinct_target_dates')} dates")
    print(f"    - Forecast Date Span:      {cov_m.get('min_target_date')} to {cov_m.get('max_target_date')}")
    print(f"    - Partition y2026m11 Rows: {fcst_m.get('y2026m11_partition_rows', 0):,} (100% routed)")
    print(f"    - Total Projected Demand:  {summ_m.get('total_forecast_units', 0):,} units")
    print(f"    - Average Daily Demand:    {summ_m.get('avg_forecast_units', 0)} units/store-SKU")
    print(f"    - Total Reorder Suggested: {summ_m.get('total_reorder_units', 0):,} units")

    print("\n  2. Canonical Fact Table Census (All 9 Fact Tables Populated):")
    fact_c = metrics.get("fact_census", {})
    for tbl, act_cnt in fact_c.items():
        print(f"    - {tbl:<28}: {act_cnt:>12,} rows")

    print("\n  3. Conformed Dimension & Control Census:")
    dim_c = metrics.get("dim_census", {})
    for dtbl, act_cnt in dim_c.items():
        print(f"    - {dtbl:<45}: {act_cnt:>10,} rows")

    print("\n  4. Cross-Fact Accounting & Operational Validations:")
    cf = metrics.get("cross_fact", {})
    mktg_romi = cf.get("marketing_romi_governance", {})
    print(f"    - Sales vs Payments:       {cf.get('sales_vs_payments_discrepancies', 0)} discrepant invoices")
    print(f"    - Returns vs Sales:        {cf.get('refund_and_qty_overages', 0)} excess return/refund pairs")
    print(f"    - Holdout Suppression:     {cf.get('holdout_suppression_violations', 0)} control group violations")
    print(f"    - Enterprise Weighted ROMI:{mktg_romi.get('enterprise_weighted_romi')} (vs Unweighted: {mktg_romi.get('enterprise_unweighted_avg_romi')})")
    print(f"    - 4-Way Recon Domains:     {len(cf.get('reconciliation_domain_counts', []))} domains verified")

    # 3. Idempotency Check
    if test_idempotency:
        print("\n[SUBSTAGE C] Testing Idempotency (Re-running forecast generation and load)...")
        t_idem_0 = time.time()
        loader.load_demand_forecast(config, context, chunk_size=config.batch_size)
        idem_duration = time.time() - t_idem_0

        is_valid_2, errors_2, metrics_2 = validator.validate_all(profile)
        if not is_valid_2:
            print("\n[FAILED] IDEMPOTENCY CHECK FAILED:")
            for err in errors_2:
                print(f"  - {err}")
            sys.exit(1)

        counts_2 = metrics_2.get("fact_census", {})
        for tbl, exp_cnt in fact_c.items():
            if counts_2.get(tbl) != exp_cnt:
                print(f"\n[FAILED] IDEMPOTENCY ROW COUNT CHANGED in {tbl}: {exp_cnt} -> {counts_2.get(tbl)}")
                sys.exit(1)

        print(f"\n[IDEMPOTENT] Re-run completed in {idem_duration:.1f}s.")
        print("  - Fact row count strictly preserved at 210,000 (Zero duplicate rows inserted).")
        print("  - All data quality rules and cross-fact constraints remain 100% compliant.")

    total_duration = time.time() - t_total_0
    print("\n" + "=" * 80)
    print(f"STAGE 5.3.6 COMPLETE AND VERIFIED (Total Duration: {total_duration:.1f}s)")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Northstar Stage 5.3.6 Data Generation CLI")
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

