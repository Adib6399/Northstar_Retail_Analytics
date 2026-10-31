"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.4: Payment, Returns & Inventory Loaders

Orchestrates sequential batch loading for:
1. gold.fact_payments (496,800 records)
2. gold.fact_returns (34,500 records)
3. gold.fact_inventory_movements (92,000 records)
4. gold.fact_inventory_snapshot (1,380,000 records)

Enforces explicit transactions, bounded chunks, ON CONFLICT idempotency, and audit logging.
"""

import time
from datetime import date, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import text
from config.database import get_db_engine
from scripts.data_generation.config import GenerationProfileConfig, ProfileType, get_profile_config
from scripts.data_generation.generators.payment_generator import PaymentGenerator
from scripts.data_generation.generators.return_generator import ReturnGenerator
from scripts.data_generation.generators.inventory_generator import InventoryGenerator


class Stage534Loader:
    """Sequential loader for payments, returns, and inventory datasets."""

    INSERT_PAYMENTS_STMT = text("""
        INSERT INTO gold.fact_payments (
            date_key, store_key, payment_method_key, customer_key,
            pos_invoice_number, payment_line_number, payment_transaction_id,
            bank_utr_number, gateway_batch_id, tender_amount,
            gateway_deducted_fee_amount, expected_mdr_fee_amount,
            mdr_fee_discrepancy_amount, settlement_variance_amount,
            settlement_status, source_system, source_record_id,
            ingestion_batch_id, record_hash, data_quality_status
        ) VALUES (
            :date_key, :store_key, :payment_method_key, :customer_key,
            :pos_invoice_number, :payment_line_number, :payment_transaction_id,
            :bank_utr_number, :gateway_batch_id, :tender_amount,
            :gateway_deducted_fee_amount, :expected_mdr_fee_amount,
            :mdr_fee_discrepancy_amount, :settlement_variance_amount,
            :settlement_status, :source_system, :source_record_id,
            :ingestion_batch_id, :record_hash, :data_quality_status
        )
        ON CONFLICT (pos_invoice_number, payment_line_number, date_key) DO NOTHING;
    """)

    INSERT_RETURNS_STMT = text("""
        INSERT INTO gold.fact_returns (
            date_key, original_sales_date_key, store_key, product_key, customer_key,
            return_reason_key, return_receipt_id, return_line_number,
            original_invoice_number, authorizing_manager_id, erp_quarantine_grn_id,
            returned_units, refund_amount, restocking_fee_amount,
            is_unreferenced_return_flag, is_quarantine_verified_flag,
            source_system, source_record_id, ingestion_batch_id,
            record_hash, data_quality_status
        ) VALUES (
            :date_key, :original_sales_date_key, :store_key, :product_key, :customer_key,
            :return_reason_key, :return_receipt_id, :return_line_number,
            :original_invoice_number, :authorizing_manager_id, :erp_quarantine_grn_id,
            :returned_units, :refund_amount, :restocking_fee_amount,
            :is_unreferenced_return_flag, :is_quarantine_verified_flag,
            :source_system, :source_record_id, :ingestion_batch_id,
            :record_hash, :data_quality_status
        )
        ON CONFLICT (return_receipt_id, return_line_number, date_key) DO NOTHING;
    """)

    INSERT_MOVEMENTS_STMT = text("""
        INSERT INTO gold.fact_inventory_movements (
            date_key, source_store_key, destination_store_key, product_key,
            movement_type_key, erp_material_document_id, material_doc_line_number,
            movement_units, unit_valuation_cost, movement_valuation_amount,
            source_system, source_record_id, ingestion_batch_id,
            record_hash, data_quality_status
        ) VALUES (
            :date_key, :source_store_key, :destination_store_key, :product_key,
            :movement_type_key, :erp_material_document_id, :material_doc_line_number,
            :movement_units, :unit_valuation_cost, :movement_valuation_amount,
            :source_system, :source_record_id, :ingestion_batch_id,
            :record_hash, :data_quality_status
        )
        ON CONFLICT (erp_material_document_id, material_doc_line_number, date_key) DO NOTHING;
    """)

    INSERT_SNAPSHOT_STMT = text("""
        INSERT INTO gold.fact_inventory_snapshot (
            date_key, store_key, product_key, stock_on_hand_units,
            blocked_damaged_units, in_transit_units, total_inventory_units,
            unit_cost_price, inventory_valuation_cost_amount,
            trailing_14d_sales_velocity_units, days_of_inventory_forward,
            stockout_flag, source_system, source_record_id,
            ingestion_batch_id, record_hash, data_quality_status
        ) VALUES (
            :date_key, :store_key, :product_key, :stock_on_hand_units,
            :blocked_damaged_units, :in_transit_units, :total_inventory_units,
            :unit_cost_price, :inventory_valuation_cost_amount,
            :trailing_14d_sales_velocity_units, :days_of_inventory_forward,
            :stockout_flag, :source_system, :source_record_id,
            :ingestion_batch_id, :record_hash, :data_quality_status
        )
        ON CONFLICT (date_key, store_key, product_key) DO NOTHING;
    """)

    def __init__(self, engine=None):
        self.engine = engine or get_db_engine()

    def fetch_master_context(self, config: GenerationProfileConfig) -> Dict[str, Any]:
        """Loads reference and dimension metadata."""
        with self.engine.connect() as conn:
            payment_methods = [
                dict(r._mapping) for r in conn.execute(text("""
                    SELECT payment_method_key, tender_type_code, tender_category,
                           acquirer_network, contracted_mdr_fee_pct
                    FROM gold.dim_payment_method
                    ORDER BY payment_method_key;
                """)).fetchall()
            ]

            return_reasons = [
                dict(r._mapping) for r in conn.execute(text("""
                    SELECT return_reason_key, reason_code, reason_description
                    FROM gold.ref_return_reason
                    ORDER BY return_reason_key;
                """)).fetchall()
            ]

            movement_types = [
                dict(r._mapping) for r in conn.execute(text("""
                    SELECT movement_type_key, provisional_movement_code AS movement_code, movement_name,
                           stock_impact_direction
                    FROM gold.ref_inventory_movement_type
                    ORDER BY movement_type_key;
                """)).fetchall()
            ]

            stores = [
                dict(r._mapping) for r in conn.execute(text("""
                    SELECT store_key, store_id, store_name, store_tier
                    FROM gold.dim_store
                    ORDER BY store_key
                    LIMIT :cnt;
                """), {"cnt": config.store_count}).fetchall()
            ]

            products = [
                dict(r._mapping) for r in conn.execute(text("""
                    SELECT product_key, sku_id, category_id, standard_cost_price, mrp
                    FROM gold.dim_product
                    ORDER BY product_key
                    LIMIT :cnt;
                """), {"cnt": config.product_count}).fetchall()
            ]

        return {
            "payment_methods": payment_methods,
            "return_reasons": return_reasons,
            "movement_types": movement_types,
            "stores": stores,
            "products": products,
        }

    def load_payments(
        self,
        config: GenerationProfileConfig,
        context: Dict[str, Any],
        chunk_size: int = 5000,
    ) -> Dict[str, Any]:
        """Loads gold.fact_payments reconciling with gold.fact_sales receipts."""
        t0 = time.time()
        print("\n--- SUBSTAGE A: PAYMENTS INGESTION (Target: 496,800 rows) ---")

        # 1. Fetch grouped receipts from gold.fact_sales
        with self.engine.connect() as conn:
            print("  Querying distinct sales receipts from gold.fact_sales...")
            receipt_rows = conn.execute(text("""
                SELECT pos_invoice_number, date_key, store_key, customer_key,
                       ROUND(SUM(net_sales_amount), 2) AS invoice_net_sales
                FROM gold.fact_sales
                GROUP BY pos_invoice_number, date_key, store_key, customer_key
                ORDER BY date_key, pos_invoice_number;
            """)).fetchall()
            receipts = [dict(r._mapping) for r in receipt_rows]

        total_receipts = len(receipts)
        print(f"  Fetched {total_receipts:,} sales receipts.")

        generator = PaymentGenerator(
            config=config,
            payment_methods=context["payment_methods"],
            seed=config.random_seed,
        )

        total_payments_inserted = 0

        # Ingest in chunks of 5,000 receipts (~5,400 payments)
        receipt_chunk_size = 5000
        for start_idx in range(0, total_receipts, receipt_chunk_size):
            r_chunk = receipts[start_idx : start_idx + receipt_chunk_size]
            payment_chunk = generator.generate_payments_for_receipts(
                receipts=r_chunk,
                start_receipt_index=start_idx,
            )

            with self.engine.begin() as conn:
                for p_sub_idx in range(0, len(payment_chunk), chunk_size):
                    sub_batch = payment_chunk[p_sub_idx : p_sub_idx + chunk_size]
                    conn.execute(self.INSERT_PAYMENTS_STMT, sub_batch)

            total_payments_inserted += len(payment_chunk)
            if (start_idx // receipt_chunk_size + 1) % 10 == 0 or start_idx + receipt_chunk_size >= total_receipts:
                elapsed = time.time() - t0
                pct = (total_payments_inserted / config.payment_tenders) * 100.0
                print(f"    Payments: {total_payments_inserted:,} / {config.payment_tenders:,} ({pct:5.1f}%) in {elapsed:.1f}s")

        duration = time.time() - t0
        return {
            "table": "gold.fact_payments",
            "rows_inserted": total_payments_inserted,
            "duration_seconds": round(duration, 2),
            "rows_per_second": round(total_payments_inserted / max(1.0, duration), 1),
        }

    def load_returns(
        self,
        config: GenerationProfileConfig,
        context: Dict[str, Any],
        chunk_size: int = 5000,
    ) -> Dict[str, Any]:
        """Loads gold.fact_returns referencing authentic historical sales lines."""
        t0 = time.time()
        print("\n--- SUBSTAGE B: RETURNS INGESTION (Target: 34,500 rows) ---")

        target_returns = config.return_lines  # Exactly 34,500

        # Category return quotas
        cat_quotas = {
            "APPR": 15534,
            "ELEC": 4143,
            "HOME": 6204,
            "FMCG": 8619,
        }
        assert sum(cat_quotas.values()) == target_returns

        sampled_sales_lines: List[Dict[str, Any]] = []

        with self.engine.connect() as conn:
            print("  Sampling authentic sales lines across categories...")
            for cat_id, quota in cat_quotas.items():
                rows = conn.execute(text("""
                    SELECT s.sales_fact_key, s.pos_invoice_number, s.pos_line_number, s.date_key,
                           s.store_key, s.product_key, s.customer_key,
                           s.quantity_sold, s.net_sales_amount, p.category_id
                    FROM gold.fact_sales s
                    JOIN gold.dim_product p ON s.product_key = p.product_key
                    WHERE p.category_id = :cat_id
                    ORDER BY ((s.sales_fact_key * 104729) % 1000000), s.sales_fact_key
                    LIMIT :quota;
                """), {"cat_id": cat_id, "quota": quota}).fetchall()
                sampled_sales_lines.extend([dict(r._mapping) for r in rows])

        print(f"  Total sampled sales lines for returns: {len(sampled_sales_lines):,}")

        generator = ReturnGenerator(
            config=config,
            return_reasons=context["return_reasons"],
            seed=config.random_seed,
        )

        return_records = generator.generate_returns_from_sales(sampled_sales_lines)
        total_returns = len(return_records)

        with self.engine.begin() as conn:
            for start_idx in range(0, total_returns, chunk_size):
                chunk = return_records[start_idx : start_idx + chunk_size]
                conn.execute(self.INSERT_RETURNS_STMT, chunk)

        duration = time.time() - t0
        print(f"    Returns loaded: {total_returns:,} in {duration:.1f}s")
        return {
            "table": "gold.fact_returns",
            "rows_inserted": total_returns,
            "duration_seconds": round(duration, 2),
            "rows_per_second": round(total_returns / max(1.0, duration), 1),
        }

    def load_inventory_movements(
        self,
        config: GenerationProfileConfig,
        context: Dict[str, Any],
        chunk_size: int = 5000,
    ) -> Dict[str, Any]:
        """Loads gold.fact_inventory_movements day-by-day (1,000 movements/day x 92 days)."""
        t0 = time.time()
        print("\n--- SUBSTAGE C: INVENTORY MOVEMENTS INGESTION (Target: 92,000 rows) ---")

        generator = InventoryGenerator(
            config=config,
            stores=context["stores"],
            products=context["products"],
            movement_types=context["movement_types"],
            seed=config.random_seed,
        )

        curr_date = config.start_date
        total_days = config.generation_days
        total_movements = 0

        while curr_date <= config.end_date:
            day_moves = generator.generate_day_movements(curr_date)
            with self.engine.begin() as conn:
                conn.execute(self.INSERT_MOVEMENTS_STMT, day_moves)
            total_movements += len(day_moves)
            curr_date += timedelta(days=1)

        duration = time.time() - t0
        print(f"    Movements loaded: {total_movements:,} in {duration:.1f}s")
        return {
            "table": "gold.fact_inventory_movements",
            "rows_inserted": total_movements,
            "duration_seconds": round(duration, 2),
            "rows_per_second": round(total_movements / max(1.0, duration), 1),
        }

    def load_inventory_snapshots(
        self,
        config: GenerationProfileConfig,
        context: Dict[str, Any],
        chunk_size: int = 5000,
        log_interval_days: int = 15,
    ) -> Dict[str, Any]:
        """Loads gold.fact_inventory_snapshot day-by-day (15,000 snapshots/day x 92 days)."""
        t0 = time.time()
        print("\n--- SUBSTAGE D: INVENTORY SNAPSHOTS INGESTION (Target: 1,380,000 rows) ---")

        generator = InventoryGenerator(
            config=config,
            stores=context["stores"],
            products=context["products"],
            movement_types=context["movement_types"],
            seed=config.random_seed,
        )

        curr_date = config.start_date
        total_days = config.generation_days
        day_idx = 0
        total_snapshots = 0

        while curr_date <= config.end_date:
            day_idx += 1
            day_snaps = generator.generate_day_snapshots(curr_date)

            with self.engine.begin() as conn:
                for start_idx in range(0, len(day_snaps), chunk_size):
                    chunk = day_snaps[start_idx : start_idx + chunk_size]
                    conn.execute(self.INSERT_SNAPSHOT_STMT, chunk)

            total_snapshots += len(day_snaps)

            if day_idx % log_interval_days == 0 or day_idx == total_days:
                elapsed = time.time() - t0
                pct = (day_idx / total_days) * 100.0
                rate = total_snapshots / max(1.0, elapsed)
                print(f"    Snapshots: {total_snapshots:,} / {config.inventory_snapshots:,} ({pct:5.1f}%) in {elapsed:.1f}s ({rate:,.0f} rows/s)")

            curr_date += timedelta(days=1)

        duration = time.time() - t0
        return {
            "table": "gold.fact_inventory_snapshot",
            "rows_inserted": total_snapshots,
            "duration_seconds": round(duration, 2),
            "rows_per_second": round(total_snapshots / max(1.0, duration), 1),
        }
