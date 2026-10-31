"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.4: Payment, Returns & Inventory Data Generation Orchestrator

Sequentially executes:
1. Substage A: gold.fact_payments (496,800 rows)
2. Substage B: gold.fact_returns (34,500 rows)
3. Substage C: gold.fact_inventory_movements (92,000 rows)
4. Substage D: gold.fact_inventory_snapshot (1,380,000 rows)

Includes automated cross-table validation and idempotency verification.
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
from scripts.data_generation.loaders.stage_5_3_4_loader import Stage534Loader
from scripts.data_generation.validators.stage_5_3_4_validator import Stage534Validator


def run_pipeline(profile: ProfileType = ProfileType.INTEGRATION, test_idempotency: bool = True):
    print("=" * 80)
    print(f"NORTHSTAR RETAIL GROUP — STAGE 5.3.4 GENERATION: {profile.value}")
    print("PAYMENTS, RETURNS, INVENTORY MOVEMENTS & INVENTORY SNAPSHOTS")
    print("=" * 80)

    # 1. Connectivity Check
    ok, msg = check_database_connectivity()
    if not ok:
        print(f"[FATAL] Database connection failed: {msg}")
        sys.exit(1)
    print(f"[PRE-FLIGHT] Database connection verified: {msg}")

    config = get_profile_config(profile)
    loader = Stage534Loader()
    validator = Stage534Validator()

    t_total_0 = time.time()
    context = loader.fetch_master_context(config)

    # Substage A: Payments
    t_pay_0 = time.time()
    res_pay = loader.load_payments(config, context, chunk_size=5000)

    # Substage B: Returns
    t_ret_0 = time.time()
    res_ret = loader.load_returns(config, context, chunk_size=5000)

    # Substage C: Inventory Movements
    t_mov_0 = time.time()
    res_mov = loader.load_inventory_movements(config, context, chunk_size=5000)

    # Substage D: Inventory Snapshots
    t_snp_0 = time.time()
    res_snp = loader.load_inventory_snapshots(config, context, chunk_size=5000, log_interval_days=15)

    total_load_duration = time.time() - t_total_0

    print("\n" + "=" * 80)
    print("STAGE 5.3.4 ALL 4 SUBSTAGES INGESTION COMPLETE")
    print("=" * 80)
    print(f"  1. Payments:  {res_pay['rows_inserted']:,} rows in {res_pay['duration_seconds']}s ({res_pay['rows_per_second']:,} rows/s)")
    print(f"  2. Returns:   {res_ret['rows_inserted']:,} rows in {res_ret['duration_seconds']}s ({res_ret['rows_per_second']:,} rows/s)")
    print(f"  3. Movements: {res_mov['rows_inserted']:,} rows in {res_mov['duration_seconds']}s ({res_mov['rows_per_second']:,} rows/s)")
    print(f"  4. Snapshots: {res_snp['rows_inserted']:,} rows in {res_snp['duration_seconds']}s ({res_snp['rows_per_second']:,} rows/s)")
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
    print(f"  - fact_sales:              {counts.get('fact_sales', 0):,} rows")
    print(f"  - fact_payments:           {counts.get('fact_payments', 0):,} rows")
    print(f"  - fact_returns:            {counts.get('fact_returns', 0):,} rows")
    print(f"  - fact_inventory_movements:{counts.get('fact_inventory_movements', 0):,} rows")
    print(f"  - fact_inventory_snapshot: {counts.get('fact_inventory_snapshot', 0):,} rows")
    print(f"  - Unpopulated facts:       0 rows across all 4 out-of-scope fact tables")
    print(f"  - control_batch_audit:     0 rows")

    pay_totals = metrics.get("payment_totals", {})
    print("\n  Payments Reconciliation:")
    print(f"    - Total Tendered INR: ₹{pay_totals.get('total_tender_amount', 0):,.2f}")
    print(f"    - Total Gateway MDR:  ₹{pay_totals.get('total_mdr_fee', 0):,.2f}")
    print(f"    - Invoices Settled:   {pay_totals.get('settled_invoices', 0):,} (100% settled)")

    ret_totals = metrics.get("return_totals", {})
    print("\n  Returns Reconciliation:")
    print(f"    - Returned Units:     {ret_totals.get('total_returned_units', 0):,}")
    print(f"    - Total Refunds INR:  ₹{ret_totals.get('total_refund_amount', 0):,.2f}")
    print(f"    - Restocking Fees:    ₹{ret_totals.get('total_restocking_fees', 0):,.2f}")

    snap_totals = metrics.get("snapshot_totals", {})
    print("\n  Inventory Snapshots:")
    print(f"    - Saleable SOH Units: {snap_totals.get('total_soh_units', 0):,}")
    print(f"    - Quarantined Units:  {snap_totals.get('total_quarantine_units', 0):,}")
    print(f"    - In-Transit Units:   {snap_totals.get('total_in_transit_units', 0):,}")
    print(f"    - Total Valuation:    ₹{snap_totals.get('total_inventory_valuation', 0):,.2f}")
    print(f"    - Stockout Events:    {snap_totals.get('total_stockout_events', 0):,}")

    # 3. Idempotency Check
    if test_idempotency:
        print("\n3. Testing Idempotency (Re-running generation and load)...")
        t_idem_0 = time.time()
        loader.load_payments(config, context, chunk_size=5000)
        loader.load_returns(config, context, chunk_size=5000)
        loader.load_inventory_movements(config, context, chunk_size=5000)
        loader.load_inventory_snapshots(config, context, chunk_size=5000, log_interval_days=46)
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
                print(f"\n[FAILED] IDEMPOTENCY ROW COUNT CHANGED in gold.{tbl}: {exp_cnt} -> {counts_2.get(tbl)}")
                sys.exit(1)

        print(f"\n[IDEMPOTENT] Re-run completed in {idem_duration:.1f}s.")
        print("  - All table row counts remain strictly unchanged (Zero duplicates created).")
        print("  - All data quality rules and reconciliation assertions remain 100% compliant.")

    print("\n" + "=" * 80)
    print("STAGE 5.3.4 GENERATION COMPLETE AND VERIFIED")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Northstar Stage 5.3.4 Data Generation CLI")
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

