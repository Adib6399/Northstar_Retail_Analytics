"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.2: Dimension Loader (Topological Master Data Ingestion)

Loads all 8 conformed dimension tables in strict foreign-key dependency order.
Enforces explicit database transactions, parameterized statements, batch execution,
and idempotent conflict resolution. Preserves customer sentinel member (key -1).
"""

from typing import Dict, Any, List
from sqlalchemy import text
from config.database import get_db_engine
from scripts.data_generation.config import GenerationProfileConfig, ProfileType, get_profile_config
from scripts.data_generation.generators.date_generator import generate_dim_date_records
from scripts.data_generation.generators.store_generator import generate_dim_store_records
from scripts.data_generation.generators.supplier_generator import generate_dim_supplier_records
from scripts.data_generation.generators.product_generator import generate_dim_product_records
from scripts.data_generation.generators.customer_generator import generate_dim_customer_records
from scripts.data_generation.generators.payment_method_generator import generate_dim_payment_method_records
from scripts.data_generation.generators.promotion_generator import generate_dim_promotion_records
from scripts.data_generation.generators.campaign_generator import generate_dim_campaign_records


class DimensionLoader:
    """Orchestrates topological ingestion of dimension tables into PostgreSQL 16."""

    def __init__(self):
        self.engine = get_db_engine()

    def load_profile(self, profile_config: GenerationProfileConfig) -> Dict[str, int]:
        """
        Executes topological master data loading for the specified profile.
        Returns a dictionary of resulting table row counts.
        """
        with self.engine.begin() as conn:
            # 1. Date Dimension (2,556 calendar records: 2021-01-01 to 2027-12-31)
            self._load_dim_date(conn)

            # 2. Supplier Dimension
            self._load_dim_supplier(conn, profile_config.supplier_count)

            # 3. Store Dimension
            self._load_dim_store(conn, profile_config.store_count)

            # 4. Payment Method Dimension (8 records)
            self._load_dim_payment_method(conn)

            # 5. Promotion Dimension
            self._load_dim_promotion(conn, profile_config.promotion_count)

            # 6. Campaign Dimension
            self._load_dim_campaign(conn, profile_config.campaign_count)

            # 7. Product Dimension (resolves supplier keys)
            self._load_dim_product(conn, profile_config.product_count)

            # 8. Customer Dimension (preserves sentinel, resolves store IDs)
            self._load_dim_customer(conn, profile_config.customer_count, profile_config.pseudonymization_pepper)

        return self.get_dimension_counts()

    def get_dimension_counts(self) -> Dict[str, int]:
        """Queries PostgreSQL directly to return exact row counts for all 8 dimensions."""
        dims = [
            "dim_date", "dim_store", "dim_supplier", "dim_product",
            "dim_customer", "dim_payment_method", "dim_promotion", "dim_campaign"
        ]
        counts = {}
        with self.engine.connect() as conn:
            for dim in dims:
                cnt = conn.execute(text(f"SELECT count(*) FROM gold.{dim};")).scalar()
                counts[dim] = cnt
        return counts

    def _load_dim_date(self, conn):
        """Idempotently loads 2,556 date records."""
        records = generate_dim_date_records()
        stmt = text("""
            INSERT INTO gold.dim_date (
                date_key, calendar_date, calendar_year, calendar_quarter,
                calendar_month_number, calendar_month_name, calendar_week_of_year,
                day_of_month, day_name, is_weekend_flag, fiscal_year, fiscal_quarter,
                is_indian_national_holiday_flag, festival_season_name, days_relative_to_festival_peak
            ) VALUES (
                :date_key, :calendar_date, :calendar_year, :calendar_quarter,
                :calendar_month_number, :calendar_month_name, :calendar_week_of_year,
                :day_of_month, :day_name, :is_weekend_flag, :fiscal_year, :fiscal_quarter,
                :is_indian_national_holiday_flag, :festival_season_name, :days_relative_to_festival_peak
            )
            ON CONFLICT (date_key) DO NOTHING;
        """)
        conn.execute(stmt, records)

    def _load_dim_supplier(self, conn, count: int):
        """Idempotently loads suppliers."""
        records = generate_dim_supplier_records(count)
        stmt = text("""
            INSERT INTO gold.dim_supplier (
                vendor_id, vendor_name, gstin_number,
                payment_terms_days, trailing_avg_lead_time_days, vendor_reliability_rating
            ) VALUES (
                :vendor_id, :vendor_name, :gstin_number,
                :payment_terms_days, :trailing_avg_lead_time_days, :vendor_reliability_rating
            )
            ON CONFLICT (vendor_id) DO NOTHING;
        """)
        conn.execute(stmt, records)

    def _load_dim_store(self, conn, count: int):
        """Idempotently loads stores."""
        records = generate_dim_store_records(count)
        stmt = text("""
            INSERT INTO gold.dim_store (
                store_id, store_name, store_tier, city, state, region,
                carpet_area_sqft, backroom_storage_sqft, monthly_lease_rent_inr,
                daily_allocated_rent_inr, store_manager_employee_id, operating_status,
                effective_from_timestamp, effective_to_timestamp, is_current_flag
            ) VALUES (
                :store_id, :store_name, :store_tier, :city, :state, :region,
                :carpet_area_sqft, :backroom_storage_sqft, :monthly_lease_rent_inr,
                :daily_allocated_rent_inr, :store_manager_employee_id, :operating_status,
                :effective_from_timestamp, :effective_to_timestamp, :is_current_flag
            )
            ON CONFLICT (store_id) WHERE (is_current_flag = true) DO NOTHING;
        """)
        conn.execute(stmt, records)

    def _load_dim_payment_method(self, conn):
        """Idempotently loads the 8 payment tender methods."""
        records = generate_dim_payment_method_records()
        stmt = text("""
            INSERT INTO gold.dim_payment_method (
                tender_type_code, tender_category, acquirer_network, contracted_mdr_fee_pct
            ) VALUES (
                :tender_type_code, :tender_category, :acquirer_network, :contracted_mdr_fee_pct
            )
            ON CONFLICT (tender_type_code, acquirer_network) DO NOTHING;
        """)
        conn.execute(stmt, records)

    def _load_dim_promotion(self, conn, count: int):
        """Idempotently loads promotional campaigns."""
        records = generate_dim_promotion_records(count)
        stmt = text("""
            INSERT INTO gold.dim_promotion (
                promo_code, promo_name, discount_type, discount_value,
                start_date, end_date, clearance_aging_tier, is_clearance_flag
            ) VALUES (
                :promo_code, :promo_name, :discount_type, :discount_value,
                :start_date, :end_date, :clearance_aging_tier, :is_clearance_flag
            )
            ON CONFLICT (promo_code) DO NOTHING;
        """)
        conn.execute(stmt, records)

    def _load_dim_campaign(self, conn, count: int):
        """Idempotently loads marketing campaigns."""
        records = generate_dim_campaign_records(count)
        stmt = text("""
            INSERT INTO gold.dim_campaign (
                campaign_id, campaign_name, communication_channel,
                start_date, end_date, total_budget_inr, target_category_name
            ) VALUES (
                :campaign_id, :campaign_name, :communication_channel,
                :start_date, :end_date, :total_budget_inr, :target_category_name
            )
            ON CONFLICT (campaign_id) DO NOTHING;
        """)
        conn.execute(stmt, records)

    def _load_dim_product(self, conn, count: int):
        """Resolves authentic supplier keys and idempotently loads products."""
        # Query authentic supplier keys from database
        sup_keys = [r[0] for r in conn.execute(text("SELECT supplier_key FROM gold.dim_supplier ORDER BY supplier_key;")).fetchall()]
        if not sup_keys:
            raise RuntimeError("Cannot load dim_product: zero suppliers exist in gold.dim_supplier.")

        records = generate_dim_product_records(count, sup_keys)
        stmt = text("""
            INSERT INTO gold.dim_product (
                sku_id, sku_name, category_id, category_name, subcategory_name,
                hsn_code, gst_rate_pct, standard_cost_price, mrp, pack_size,
                unit_of_measure, abc_velocity_class, primary_supplier_key,
                effective_from_timestamp, effective_to_timestamp, is_current_flag
            ) VALUES (
                :sku_id, :sku_name, :category_id, :category_name, :subcategory_name,
                :hsn_code, :gst_rate_pct, :standard_cost_price, :mrp, :pack_size,
                :unit_of_measure, :abc_velocity_class, :primary_supplier_key,
                :effective_from_timestamp, :effective_to_timestamp, :is_current_flag
            )
            ON CONFLICT (sku_id) WHERE (is_current_flag = true) DO NOTHING;
        """)
        conn.execute(stmt, records)

    def _load_dim_customer(self, conn, count: int, pepper: str):
        """Idempotently loads synthetic customer profiles, preserving sentinel customer."""
        store_ids = [r[0] for r in conn.execute(text("SELECT store_id FROM gold.dim_store ORDER BY store_id;")).fetchall()]
        if not store_ids:
            store_ids = ["STR-KA-001"]

        # Batch insert customers in chunks of 2,000 to manage memory and performance
        batch_size = 2000
        stmt = text("""
            INSERT INTO gold.dim_customer (
                customer_sk, registration_store_id, loyalty_tier,
                rfm_recency_score, rfm_frequency_score, rfm_monetary_score,
                rfm_segment_name, churn_risk_flag, lifetime_net_spend_inr
            ) VALUES (
                :customer_sk, :registration_store_id, :loyalty_tier,
                :rfm_recency_score, :rfm_frequency_score, :rfm_monetary_score,
                :rfm_segment_name, :churn_risk_flag, :lifetime_net_spend_inr
            )
            ON CONFLICT (customer_sk) DO NOTHING;
        """)

        for start_idx in range(1, count + 1, batch_size):
            chunk_size = min(batch_size, count - start_idx + 1)
            records = generate_dim_customer_records(
                customer_count=chunk_size,
                store_ids=store_ids,
                pepper=pepper,
                start_index=start_idx,
            )
            conn.execute(stmt, records)
