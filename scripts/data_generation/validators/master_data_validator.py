"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.2: Master Data Validator

Performs exhaustive verification of dimension row counts, primary keys, business keys,
SCD2 temporal validity, foreign key relationships, check constraints, privacy guarantees,
and fact-table zero-row boundaries in live PostgreSQL 16.
"""

import re
from typing import Dict, Any, List, Tuple
from sqlalchemy import text
from config.database import get_db_engine
from scripts.data_generation.config import ProfileType, get_profile_config


class MasterDataValidator:
    """Audits live PostgreSQL database against Stage 5.3.2 quality and volume requirements."""

    def __init__(self):
        self.engine = get_db_engine()

    def validate_profile(self, profile_type: ProfileType) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Validates the database against the specified profile (DEV or INTEGRATION).
        Returns:
            is_valid (bool)
            errors (List[str])
            metrics (Dict[str, Any])
        """
        config = get_profile_config(profile_type)
        errors = []
        metrics = {}

        with self.engine.connect() as conn:
            # 1. Exact Row Counts
            expected_counts = {
                "dim_date": 2556,
                "dim_store": config.store_count,
                "dim_supplier": config.supplier_count,
                "dim_product": config.product_count,
                "dim_customer": config.customer_count + 1,  # +1 for sentinel
                "dim_payment_method": 8,
                "dim_promotion": config.promotion_count,
                "dim_campaign": config.campaign_count,
            }

            actual_counts = {}
            for table, exp_cnt in expected_counts.items():
                act_cnt = conn.execute(text(f"SELECT count(*) FROM gold.{table};")).scalar()
                actual_counts[table] = act_cnt
                if act_cnt != exp_cnt:
                    errors.append(f"Row count mismatch in gold.{table}: expected {exp_cnt}, found {act_cnt}")

            metrics["row_counts"] = actual_counts

            # 2. Fact Tables Zero-Row Boundary
            facts = [
                "fact_sales", "fact_payments", "fact_returns", "fact_inventory_snapshot",
                "fact_inventory_movements", "fact_reconciliation", "fact_marketing_performance",
                "fact_campaign_exposure", "fact_demand_forecast"
            ]
            fact_counts = {}
            for fact in facts:
                act_cnt = conn.execute(text(f"SELECT count(*) FROM gold.{fact};")).scalar()
                fact_counts[fact] = act_cnt
                if act_cnt != 0:
                    errors.append(f"BOUNDARY VIOLATION: Fact table gold.{fact} has {act_cnt} rows (must be 0)")

            batch_audit_cnt = conn.execute(text("SELECT count(*) FROM control.control_batch_audit;")).scalar()
            fact_counts["control_batch_audit"] = batch_audit_cnt
            if batch_audit_cnt != 0:
                errors.append(f"BOUNDARY VIOLATION: control.control_batch_audit has {batch_audit_cnt} rows (must be 0)")

            metrics["fact_counts"] = fact_counts

            # 3. Sentinel Customer Member Integrity
            sentinel = conn.execute(text("""
                SELECT customer_key, customer_sk, registration_store_id, loyalty_tier, rfm_segment_name
                FROM gold.dim_customer
                WHERE customer_key = -1;
            """)).fetchone()

            if not sentinel:
                errors.append("Sentinel customer member (customer_key = -1) is MISSING")
            else:
                sentinel_dict = dict(sentinel._mapping)
                metrics["sentinel_customer"] = sentinel_dict
                if sentinel_dict["customer_sk"] != "0" * 64:
                    errors.append(f"Sentinel customer_sk invalid: {sentinel_dict['customer_sk']}")
                if sentinel_dict["registration_store_id"] != "STORE_SYSTEM":
                    errors.append(f"Sentinel registration_store_id invalid: {sentinel_dict['registration_store_id']}")

            # 4. Primary Key & Business Key Uniqueness
            pk_checks = [
                ("gold.dim_date", "date_key", "calendar_date"),
                ("gold.dim_store", "store_key", "store_id"),
                ("gold.dim_supplier", "supplier_key", "vendor_id"),
                ("gold.dim_product", "product_key", "sku_id"),
                ("gold.dim_customer", "customer_key", "customer_sk"),
                ("gold.dim_promotion", "promotion_key", "promo_code"),
                ("gold.dim_campaign", "campaign_key", "campaign_id"),
            ]

            for table, pk_col, bk_col in pk_checks:
                pk_diff = conn.execute(text(f"""
                    SELECT count(*) - count(DISTINCT {pk_col}) FROM {table};
                """)).scalar()
                if pk_diff != 0:
                    errors.append(f"Duplicate primary key values in {table}.{pk_col}: {pk_diff}")

                if table in ("gold.dim_store", "gold.dim_product"):
                    # For SCD2, uniqueness applies to current records
                    bk_diff = conn.execute(text(f"""
                        SELECT count(*) - count(DISTINCT {bk_col}) FROM {table} WHERE is_current_flag = true;
                    """)).scalar()
                else:
                    bk_diff = conn.execute(text(f"""
                        SELECT count(*) - count(DISTINCT {bk_col}) FROM {table};
                    """)).scalar()

                if bk_diff != 0:
                    errors.append(f"Duplicate business key values in {table}.{bk_col}: {bk_diff}")

            # 5. SCD2 Temporal Validity (effective_from < effective_to)
            scd2_invalid_stores = conn.execute(text("""
                SELECT count(*) FROM gold.dim_store WHERE effective_from_timestamp >= effective_to_timestamp;
            """)).scalar()
            if scd2_invalid_stores > 0:
                errors.append(f"Invalid SCD2 timestamps in dim_store: {scd2_invalid_stores} rows")

            scd2_invalid_prods = conn.execute(text("""
                SELECT count(*) FROM gold.dim_product WHERE effective_from_timestamp >= effective_to_timestamp;
            """)).scalar()
            if scd2_invalid_prods > 0:
                errors.append(f"Invalid SCD2 timestamps in dim_product: {scd2_invalid_prods} rows")

            # 6. Foreign Key Integrity (dim_product -> dim_supplier)
            orphan_prods = conn.execute(text("""
                SELECT count(*)
                FROM gold.dim_product p
                LEFT JOIN gold.dim_supplier s ON p.primary_supplier_key = s.supplier_key
                WHERE p.primary_supplier_key IS NOT NULL AND s.supplier_key IS NULL;
            """)).scalar()
            if orphan_prods > 0:
                errors.append(f"Foreign key violation: {orphan_prods} products reference non-existent suppliers")

            # 7. Customer Privacy & HMAC Hash Format (64 hex characters)
            invalid_hashes = conn.execute(text("""
                SELECT count(*)
                FROM gold.dim_customer
                WHERE customer_key != -1 AND customer_sk !~ '^[a-f0-9]{64}$';
            """)).scalar()
            if invalid_hashes > 0:
                errors.append(f"Privacy validation failure: {invalid_hashes} customer_sk values are not 64-character hex digests")

            # 8. Check Constraints
            # Product price checks
            invalid_prices = conn.execute(text("""
                SELECT count(*)
                FROM gold.dim_product
                WHERE standard_cost_price <= 0.0000 OR mrp < standard_cost_price;
            """)).scalar()
            if invalid_prices > 0:
                errors.append(f"Product pricing check failure: {invalid_prices} products have non-positive cost or mrp < cost")

            # Supplier rating range
            invalid_ratings = conn.execute(text("""
                SELECT count(*) FROM gold.dim_supplier WHERE vendor_reliability_rating < 0.00 OR vendor_reliability_rating > 1.00;
            """)).scalar()
            if invalid_ratings > 0:
                errors.append(f"Supplier rating failure: {invalid_ratings} suppliers have rating outside [0.00, 1.00]")

            # Date dimension constraints
            invalid_dates = conn.execute(text("""
                SELECT count(*)
                FROM gold.dim_date
                WHERE calendar_quarter NOT BETWEEN 1 AND 4
                   OR calendar_month_number NOT BETWEEN 1 AND 12
                   OR fiscal_quarter NOT BETWEEN 1 AND 4;
            """)).scalar()
            if invalid_dates > 0:
                errors.append(f"Date dimension constraint failure: {invalid_dates} records have invalid quarters/months")

        is_valid = len(errors) == 0
        return is_valid, errors, metrics
