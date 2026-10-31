"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.5: Marketing & Reconciliation Data Loader

Orchestrates sequential batch loading for:
  1. gold.fact_marketing_performance (1,840 records)
  2. control.control_campaign_assignment_registry (50,000 records)
  3. gold.fact_campaign_exposure (50,000 records)
  4. gold.fact_reconciliation (11,040 records)

Enforces explicit transactions, bounded chunks, ON CONFLICT idempotency, and audit logging.
"""

import time
from datetime import date
from decimal import Decimal
from typing import Dict, Any, List, Tuple
from sqlalchemy import text
from config.database import get_db_engine
from scripts.data_generation.config import GenerationProfileConfig
from scripts.data_generation.generators.marketing_performance_generator import MarketingPerformanceGenerator
from scripts.data_generation.generators.campaign_exposure_generator import CampaignExposureGenerator
from scripts.data_generation.generators.reconciliation_generator import ReconciliationGenerator


class Stage535Loader:
    """Sequential loader for marketing performance, exposures, and reconciliation datasets."""

    INSERT_MARKETING_PERF_STMT = text("""
        INSERT INTO gold.fact_marketing_performance (
            date_key, store_key, campaign_key, promotion_key,
            test_cohort_sales_amount, control_cohort_sales_amount,
            incremental_sales_lift_amount, incremental_gross_margin_amount,
            attributed_marketing_spend_amount, test_customer_count,
            control_customer_count, incremental_romi_ratio,
            attribution_status, source_system, source_record_id,
            ingestion_batch_id, record_hash, data_quality_status
        ) VALUES (
            :date_key, :store_key, :campaign_key, :promotion_key,
            :test_cohort_sales_amount, :control_cohort_sales_amount,
            :incremental_sales_lift_amount, :incremental_gross_margin_amount,
            :attributed_marketing_spend_amount, :test_customer_count,
            :control_customer_count, :incremental_romi_ratio,
            :attribution_status, :source_system, :source_record_id,
            :ingestion_batch_id, :record_hash, :data_quality_status
        )
        ON CONFLICT (date_key, store_key, campaign_key) DO NOTHING;
    """)

    INSERT_REGISTRY_STMT = text("""
        INSERT INTO control.control_campaign_assignment_registry (
            campaign_id, customer_sk, campaign_key, customer_key,
            assignment_date_key, assignment_timestamp, is_holdout_control_flag,
            assignment_hash_value, holdout_key_version, is_locked_flag,
            ingestion_batch_id
        ) VALUES (
            :campaign_id, :customer_sk, :campaign_key, :customer_key,
            :assignment_date_key, :assignment_timestamp, :is_holdout_control_flag,
            :assignment_hash_value, :holdout_key_version, :is_locked_flag,
            :ingestion_batch_id
        )
        ON CONFLICT (campaign_key, customer_key) DO NOTHING;
    """)

    INSERT_EXPOSURE_STMT = text("""
        INSERT INTO gold.fact_campaign_exposure (
            assignment_id, assignment_date_key, campaign_key, customer_key,
            is_holdout_control_flag, communication_channel, dispatch_status,
            dispatch_timestamp, dispatch_attempt_count, delivery_status,
            delivery_timestamp, coupon_redeemed_flag, redemption_date_key,
            redemption_timestamp, redemption_lag_days, source_system,
            source_record_id, ingestion_batch_id, record_hash,
            data_quality_status
        ) VALUES (
            :assignment_id, :assignment_date_key, :campaign_key, :customer_key,
            :is_holdout_control_flag, :communication_channel, :dispatch_status,
            :dispatch_timestamp, :dispatch_attempt_count, :delivery_status,
            :delivery_timestamp, :coupon_redeemed_flag, :redemption_date_key,
            :redemption_timestamp, :redemption_lag_days, :source_system,
            :source_record_id, :ingestion_batch_id, :record_hash,
            :data_quality_status
        )
        ON CONFLICT (assignment_id, assignment_date_key) DO NOTHING;
    """)

    INSERT_RECON_STMT = text("""
        INSERT INTO gold.fact_reconciliation (
            date_key, store_key, recon_domain_key, discrepancy_ticket_id,
            audit_entity_identifier, source_system_a_amount, source_system_b_amount,
            variance_amount, absolute_variance_amount, ticket_generated_flag,
            discrepancy_threshold_applied, investigation_status,
            resolution_reason_code, source_system, source_record_id,
            ingestion_batch_id, record_hash, data_quality_status
        ) VALUES (
            :date_key, :store_key, :recon_domain_key, :discrepancy_ticket_id,
            :audit_entity_identifier, :source_system_a_amount, :source_system_b_amount,
            :variance_amount, :absolute_variance_amount, :ticket_generated_flag,
            :discrepancy_threshold_applied, :investigation_status,
            :resolution_reason_code, :source_system, :source_record_id,
            :ingestion_batch_id, :record_hash, :data_quality_status
        )
        ON CONFLICT (date_key, recon_domain_key, audit_entity_identifier) DO NOTHING;
    """)

    def __init__(self, engine=None):
        self.engine = engine or get_db_engine()

    def fetch_master_context(self, config: GenerationProfileConfig) -> Dict[str, Any]:
        """Loads reference and dimension metadata, plus pre-aggregated sales/payment/inventory summaries."""
        with self.engine.connect() as conn:
            print("  Fetching dimension and reference metadata...")
            stores = [
                dict(r._mapping) for r in conn.execute(text("""
                    SELECT store_key, store_id, store_name, store_tier
                    FROM gold.dim_store
                    ORDER BY store_key
                    LIMIT :cnt;
                """), {"cnt": config.store_count}).fetchall()
            ]

            campaigns = [
                dict(r._mapping) for r in conn.execute(text("""
                    SELECT campaign_key, campaign_id, campaign_name, communication_channel,
                           start_date, end_date, total_budget_inr, target_category_name
                    FROM gold.dim_campaign
                    ORDER BY campaign_key
                    LIMIT :cnt;
                """), {"cnt": config.campaign_count}).fetchall()
            ]

            promotions = [
                dict(r._mapping) for r in conn.execute(text("""
                    SELECT promotion_key, promo_code, promo_name, discount_type,
                           discount_value, start_date, end_date
                    FROM gold.dim_promotion
                    ORDER BY promotion_key
                    LIMIT :cnt;
                """), {"cnt": config.promotion_count}).fetchall()
            ]

            customers = [
                dict(r._mapping) for r in conn.execute(text("""
                    SELECT customer_key, customer_sk, loyalty_tier
                    FROM gold.dim_customer
                    WHERE customer_key > 0
                    ORDER BY customer_key
                    LIMIT :cnt;
                """), {"cnt": config.customer_count}).fetchall()
            ]

            recon_domains = [
                dict(r._mapping) for r in conn.execute(text("""
                    SELECT recon_domain_key, domain_code, domain_name, system_a_name, system_b_name
                    FROM gold.ref_reconciliation_domain
                    ORDER BY recon_domain_key;
                """)).fetchall()
            ]

            print("  Pre-aggregating source measurements by (store, date) for reconciliation...")
            # 1. Sales by store, date
            sales_rows = conn.execute(text("""
                SELECT store_key, date_key,
                       ROUND(SUM(net_sales_amount), 2) AS net_sales,
                       SUM(quantity_sold) AS units
                FROM gold.fact_sales
                GROUP BY store_key, date_key;
            """)).fetchall()
            sales_by_sd = {
                (r.store_key, r.date_key): {"net_sales": r.net_sales, "units": r.units}
                for r in sales_rows
            }

            # 2. Payments by store, date
            pay_rows = conn.execute(text("""
                SELECT store_key, date_key,
                       ROUND(SUM(tender_amount), 2) AS tender_amount
                FROM gold.fact_payments
                GROUP BY store_key, date_key;
            """)).fetchall()
            pay_by_sd = {
                (r.store_key, r.date_key): {"tender_amount": r.tender_amount}
                for r in pay_rows
            }

            # 3. Returns by store, date
            ret_rows = conn.execute(text("""
                SELECT store_key, date_key,
                       SUM(returned_units) AS returned_units
                FROM gold.fact_returns
                GROUP BY store_key, date_key;
            """)).fetchall()
            ret_by_sd = {
                (r.store_key, r.date_key): {"returned_units": r.returned_units}
                for r in ret_rows
            }

            # 4. Movements by store, date (Movement 251 and 451)
            mov_rows = conn.execute(text("""
                SELECT source_store_key AS store_key, date_key,
                       SUM(CASE WHEN mt.provisional_movement_code = '251' THEN ABS(movement_units) ELSE 0 END) AS mov_251_units,
                       SUM(CASE WHEN mt.provisional_movement_code = '451' THEN movement_units ELSE 0 END) AS mov_451_units
                FROM gold.fact_inventory_movements m
                JOIN gold.ref_inventory_movement_type mt ON m.movement_type_key = mt.movement_type_key
                GROUP BY source_store_key, date_key;
            """)).fetchall()
            mov_by_sd = {
                (r.store_key, r.date_key): {"mov_251_units": r.mov_251_units, "mov_451_units": r.mov_451_units}
                for r in mov_rows
            }

        return {
            "stores": stores,
            "campaigns": campaigns,
            "promotions": promotions,
            "customers": customers,
            "recon_domains": recon_domains,
            "sales_by_sd": sales_by_sd,
            "pay_by_sd": pay_by_sd,
            "ret_by_sd": ret_by_sd,
            "mov_by_sd": mov_by_sd,
        }

    def load_marketing_performance(
        self,
        config: GenerationProfileConfig,
        context: Dict[str, Any],
        chunk_size: int = 2000,
    ) -> Dict[str, Any]:
        """Loads gold.fact_marketing_performance (1,840 records)."""
        t0 = time.time()
        print("\n--- SUBSTAGE A: MARKETING PERFORMANCE INGESTION (Target: 1,840 rows) ---")

        generator = MarketingPerformanceGenerator(
            config=config,
            stores=context["stores"],
            campaigns=context["campaigns"],
            promotions=context["promotions"],
            seed=config.random_seed,
        )

        records = generator.generate_all_performance()
        total_records = len(records)

        with self.engine.begin() as conn:
            for start_idx in range(0, total_records, chunk_size):
                chunk = records[start_idx : start_idx + chunk_size]
                conn.execute(self.INSERT_MARKETING_PERF_STMT, chunk)

        duration = time.time() - t0
        print(f"    Marketing performance loaded: {total_records:,} rows in {duration:.2f}s")
        return {
            "table": "gold.fact_marketing_performance",
            "rows_inserted": total_records,
            "duration_seconds": round(duration, 2),
            "rows_per_second": round(total_records / max(0.1, duration), 1),
        }

    def load_campaign_exposures_and_registry(
        self,
        config: GenerationProfileConfig,
        context: Dict[str, Any],
        chunk_size: int = 5000,
    ) -> Dict[str, Any]:
        """
        Loads control.control_campaign_assignment_registry (50,000 records)
        and gold.fact_campaign_exposure (50,000 records).
        """
        t0 = time.time()
        print("\n--- SUBSTAGE B: CAMPAIGN EXPOSURES & REGISTRY (Target: 50,000 rows each) ---")

        generator = CampaignExposureGenerator(
            config=config,
            campaigns=context["campaigns"],
            customers=context["customers"],
            seed=config.random_seed,
        )

        reg_records, exp_records = generator.generate_assignments_and_exposures()
        total_rows = len(reg_records)

        # 1. Ingest into control.control_campaign_assignment_registry
        print("  1. Ingesting campaign assignment registry...")
        with self.engine.begin() as conn:
            for start_idx in range(0, total_rows, chunk_size):
                chunk = reg_records[start_idx : start_idx + chunk_size]
                conn.execute(self.INSERT_REGISTRY_STMT, chunk)

        # 2. Query assignment IDs to populate fact table composite FK
        print("  2. Resolving generated assignment IDs from registry...")
        with self.engine.connect() as conn:
            assigned_rows = conn.execute(text("""
                SELECT assignment_id, assignment_date_key, campaign_key, customer_key
                FROM control.control_campaign_assignment_registry;
            """)).fetchall()
            id_map = {
                (r.campaign_key, r.customer_key): (r.assignment_id, r.assignment_date_key)
                for r in assigned_rows
            }

        # Attach assignment_id to exposure records
        for exp in exp_records:
            key_pair = (exp["campaign_key"], exp["customer_key"])
            assign_id, assign_date = id_map[key_pair]
            exp["assignment_id"] = assign_id
            exp["assignment_date_key"] = assign_date

        # 3. Ingest into gold.fact_campaign_exposure
        print("  3. Ingesting fact_campaign_exposure...")
        with self.engine.begin() as conn:
            for start_idx in range(0, total_rows, chunk_size):
                chunk = exp_records[start_idx : start_idx + chunk_size]
                conn.execute(self.INSERT_EXPOSURE_STMT, chunk)

        duration = time.time() - t0
        print(f"    Registry and exposures loaded: {total_rows:,} rows each in {duration:.2f}s")
        return {
            "registry_table": "control.control_campaign_assignment_registry",
            "exposure_table": "gold.fact_campaign_exposure",
            "rows_inserted": total_rows,
            "duration_seconds": round(duration, 2),
            "rows_per_second": round(total_rows / max(0.1, duration), 1),
        }

    def load_reconciliations(
        self,
        config: GenerationProfileConfig,
        context: Dict[str, Any],
        chunk_size: int = 5000,
    ) -> Dict[str, Any]:
        """Loads gold.fact_reconciliation (11,040 records)."""
        t0 = time.time()
        print("\n--- SUBSTAGE C: RECONCILIATION INGESTION (Target: 11,040 rows) ---")

        generator = ReconciliationGenerator(
            config=config,
            stores=context["stores"],
            recon_domains=context["recon_domains"],
            sales_by_store_date=context["sales_by_sd"],
            payments_by_store_date=context["pay_by_sd"],
            returns_by_store_date=context["ret_by_sd"],
            movements_by_store_date=context["mov_by_sd"],
            seed=config.random_seed,
        )

        records = generator.generate_all_reconciliations()
        total_records = len(records)

        with self.engine.begin() as conn:
            for start_idx in range(0, total_records, chunk_size):
                chunk = records[start_idx : start_idx + chunk_size]
                conn.execute(self.INSERT_RECON_STMT, chunk)

        duration = time.time() - t0
        print(f"    Reconciliations loaded: {total_records:,} rows in {duration:.2f}s")
        return {
            "table": "gold.fact_reconciliation",
            "rows_inserted": total_records,
            "duration_seconds": round(duration, 2),
            "rows_per_second": round(total_records / max(0.1, duration), 1),
        }

