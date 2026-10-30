"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.2: Master Data Generation Pipeline CLI

Executes master data generation for DEV and INTEGRATION profiles with automated validation
and idempotency verification. Adheres strictly to Stage 5.3.2 governance boundaries.
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
from scripts.data_generation.config import ProfileType, get_profile_config
from scripts.data_generation.loaders.dimension_loader import DimensionLoader
from scripts.data_generation.validators.master_data_validator import MasterDataValidator


def run_pipeline(profile: ProfileType = ProfileType.DEV, test_idempotency: bool = True):
    print("=" * 80)
    print(f"NORTHSTAR RETAIL GROUP — STAGE 5.3.2 MASTER DATA GENERATION: {profile.value}")
    print("=" * 80)

    loader = DimensionLoader()
    validator = MasterDataValidator()
    config = get_profile_config(profile)

    print(f"\n1. Ingesting {profile.value} Dimension Master Data...")
    counts_after_load = loader.load_profile(config)

    print("\n   Dimension Counts Immediately After Load:")
    for dim, cnt in counts_after_load.items():
        print(f"     - gold.{dim}: {cnt} rows")

    print(f"\n2. Validating {profile.value} Master Data Quality and Constraints...")
    is_valid, errors, metrics = validator.validate_profile(profile)

    if not is_valid:
        print("\n[FAILED] VALIDATION DEFECTS DETECTED:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    print("\n   [PASSED] All dimension row counts, unique constraints, check constraints,")
    print("            foreign keys, privacy hashes, and fact-table zero-row boundaries verified!")

    if test_idempotency:
        print(f"\n3. Running Idempotency Verification for {profile.value} (Re-executing Load)...")
        counts_idempotent = loader.load_profile(config)
        is_idem_valid, idem_errors, _ = validator.validate_profile(profile)

        if not is_idem_valid or counts_idempotent != counts_after_load:
            print("\n[FAILED] IDEMPOTENCY FAILURE DETECTED:")
            for err in idem_errors:
                print(f"  - {err}")
            for dim in counts_after_load:
                if counts_after_load[dim] != counts_idempotent[dim]:
                    print(f"  - gold.{dim} row count changed: {counts_after_load[dim]} -> {counts_idempotent[dim]}")
            sys.exit(1)

        print("   [PASSED] Idempotency confirmed: row counts remained exactly identical!")

    print("\n" + "=" * 80)
    print(f"STAGE 5.3.2 MASTER DATA GENERATION SUCCESSFUL: {profile.value}")
    print("=" * 80)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Northstar Master Data Generation Pipeline")
    parser.add_argument(
        "--profile",
        type=str,
        choices=["DEV", "INTEGRATION"],
        default="DEV",
        help="Target generation profile (DEV or INTEGRATION)",
    )
    parser.add_argument(
        "--skip-idempotency",
        action="store_true",
        help="Skip secondary idempotency verification pass",
    )

    args = parser.parse_args()
    target_profile = ProfileType(args.profile)
    run_pipeline(profile=target_profile, test_idempotency=not args.skip_idempotency)
