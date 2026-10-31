"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.3: Historical Sales Fact Data Quality Validator (gold.fact_sales)

Performs comprehensive validation of generated historical sales records against
physical constraints, foreign key referential integrity, financial mathematical identities,
temporal partition coverage, zero-row boundaries for other facts, and distribution sanity.
"""

from decimal import Decimal
from typing import Dict, Any, List, Tuple
from sqlalchemy import text
from config.database import get_db_engine
from scripts.data_generation.config import GenerationProfileConfig, ProfileType, get_profile_config


class SalesValidator:
    """Automated validator for gold.fact_sales data quality and integrity."""

    def __init__(self, engine=None):
        self.engine = engine or get_db_engine()

    def validate_profile(
        self, profile: ProfileType = ProfileType.INTEGRATION
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Executes full validation suite against live PostgreSQL 16 database.
        Returns (is_valid: bool, errors: List[str], metrics: Dict[str, Any]).
        """
        config = get_profile_config(profile)
        errors: List[str] = []
        metrics: Dict[str, Any] = {}

        with self.engine.connect() as conn:
            # 1. Row Counts: fact_sales
            actual_sales_count = conn.execute(text("SELECT count(*) FROM gold.fact_sales;")).scalar()
            expected_sales_count = config.sales_line_items
            metrics["fact_sales_row_count"] = actual_sales_count
            metrics["expected_sales_count"] = expected_sales_count

            if actual_sales_count != expected_sales_count:
                errors.append(
                    f"Row count mismatch in gold.fact_sales: expected {expected_sales_count:,}, found {actual_sales_count:,}"
                )

            # 2. Strict Boundary for other facts + control_batch_audit
            authorized_counts = {
                "fact_payments": [0, config.payment_tenders],
                "fact_returns": [0, config.return_lines],
                "fact_inventory_movements": [0, config.inventory_movements],
                "fact_inventory_snapshot": [0, config.inventory_snapshots],
                "fact_marketing_performance": [0, config.marketing_performance_rows],
                "fact_campaign_exposure": [0, config.campaign_exposure_drops],
                "fact_reconciliation": [0, config.reconciliation_audits],
                "fact_demand_forecast": [0, config.demand_forecast_projections],
            }
            fact_counts = {}
            for f, allowed in authorized_counts.items():
                cnt = conn.execute(text(f"SELECT count(*) FROM gold.{f};")).scalar()
                fact_counts[f] = cnt
                if cnt not in allowed:
                    errors.append(f"Fact boundary violation: gold.{f} contains {cnt} rows (allowed: {allowed})")

            audit_count = conn.execute(text("SELECT count(*) FROM control.control_batch_audit;")).scalar()
            fact_counts["control_batch_audit"] = audit_count
            if audit_count != 0:
                errors.append(f"Control boundary violation: control.control_batch_audit contains {audit_count} rows (expected 0)")
            metrics["other_fact_counts"] = fact_counts

            # 3. Duplicate Business Key Check
            dup_keys = conn.execute(text("""
                SELECT count(*) - count(DISTINCT (pos_invoice_number, pos_line_number, date_key))
                FROM gold.fact_sales;
            """)).scalar()
            metrics["duplicate_business_keys"] = dup_keys
            if dup_keys != 0:
                errors.append(f"Duplicate receipt item business keys found in gold.fact_sales: {dup_keys}")

            # 4. Mandatory Field Null Checks
            null_checks = [
                "sales_fact_key", "date_key", "store_key", "product_key", "customer_key",
                "promotion_key", "pos_invoice_number", "pos_line_number", "pos_terminal_id",
                "cashier_employee_id", "transaction_timestamp", "quantity_sold", "unit_mrp",
                "unit_selling_price", "gross_sales_amount", "discount_amount", "net_taxable_amount",
                "tax_amount", "net_sales_amount", "unit_cost_price", "cost_amount",
                "gross_margin_amount", "source_system", "source_record_id", "ingestion_batch_id",
                "load_timestamp", "record_hash", "data_quality_status"
            ]
            null_counts = {}
            for col in null_checks:
                cnt = conn.execute(text(f"""
                    SELECT count(*) FROM gold.fact_sales WHERE {col} IS NULL;
                """)).scalar()
                if cnt != 0:
                    null_counts[col] = cnt
                    errors.append(f"Null values detected in mandatory column gold.fact_sales.{col}: {cnt}")
            metrics["null_counts"] = null_counts

            # 5. Referential Integrity Checks
            # Date Dimension
            orphaned_dates = conn.execute(text("""
                SELECT count(*)
                FROM gold.fact_sales s
                LEFT JOIN gold.dim_date d ON s.date_key = d.date_key
                WHERE d.date_key IS NULL;
            """)).scalar()
            if orphaned_dates != 0:
                errors.append(f"Orphaned date references in gold.fact_sales: {orphaned_dates}")

            # Date Range Conformance
            start_key = int(config.start_date.strftime("%Y%m%d"))
            end_key = int(config.end_date.strftime("%Y%m%d"))
            out_of_bounds_dates = conn.execute(text("""
                SELECT count(*)
                FROM gold.fact_sales
                WHERE date_key < :s_key OR date_key > :e_key;
            """), {"s_key": start_key, "e_key": end_key}).scalar()
            if out_of_bounds_dates != 0:
                errors.append(f"Sales dates out of profile bounds ({start_key} to {end_key}): {out_of_bounds_dates}")

            # Store Dimension
            orphaned_stores = conn.execute(text("""
                SELECT count(*)
                FROM gold.fact_sales s
                LEFT JOIN gold.dim_store st ON s.store_key = st.store_key
                WHERE st.store_key IS NULL;
            """)).scalar()
            if orphaned_stores != 0:
                errors.append(f"Orphaned store references in gold.fact_sales: {orphaned_stores}")

            # Product Dimension
            orphaned_products = conn.execute(text("""
                SELECT count(*)
                FROM gold.fact_sales s
                LEFT JOIN gold.dim_product p ON s.product_key = p.product_key
                WHERE p.product_key IS NULL;
            """)).scalar()
            if orphaned_products != 0:
                errors.append(f"Orphaned product references in gold.fact_sales: {orphaned_products}")

            # Customer Dimension
            orphaned_customers = conn.execute(text("""
                SELECT count(*)
                FROM gold.fact_sales s
                LEFT JOIN gold.dim_customer c ON s.customer_key = c.customer_key
                WHERE c.customer_key IS NULL;
            """)).scalar()
            if orphaned_customers != 0:
                errors.append(f"Orphaned customer references in gold.fact_sales: {orphaned_customers}")

            # Promotion Dimension
            orphaned_promos = conn.execute(text("""
                SELECT count(*)
                FROM gold.fact_sales s
                LEFT JOIN gold.dim_promotion pr ON s.promotion_key = pr.promotion_key
                WHERE pr.promotion_key IS NULL;
            """)).scalar()
            if orphaned_promos != 0:
                errors.append(f"Orphaned promotion references in gold.fact_sales: {orphaned_promos}")

            # 6. Financial Arithmetic & Accounting Identities
            # 6a. Net Taxable Amount Identity: gross_sales_amount - discount_amount == net_taxable_amount
            taxable_discrepancies = conn.execute(text("""
                SELECT count(*)
                FROM gold.fact_sales
                WHERE ABS((gross_sales_amount - discount_amount) - net_taxable_amount) > 0.001;
            """)).scalar()
            if taxable_discrepancies != 0:
                errors.append(f"Accounting discrepancy in Net Taxable Amount: {taxable_discrepancies} rows violate gross - discount = taxable")

            # 6b. Net Sales Amount Identity: net_taxable_amount + tax_amount == net_sales_amount
            net_sales_discrepancies = conn.execute(text("""
                SELECT count(*)
                FROM gold.fact_sales
                WHERE ABS((net_taxable_amount + tax_amount) - net_sales_amount) > 0.001;
            """)).scalar()
            if net_sales_discrepancies != 0:
                errors.append(f"Accounting discrepancy in Net Sales Amount: {net_sales_discrepancies} rows violate taxable + tax = net_sales")

            # 6c. Gross Margin Amount Identity: net_taxable_amount - cost_amount == gross_margin_amount
            margin_discrepancies = conn.execute(text("""
                SELECT count(*)
                FROM gold.fact_sales
                WHERE ABS((net_taxable_amount - cost_amount) - gross_margin_amount) > 0.001;
            """)).scalar()
            if margin_discrepancies != 0:
                errors.append(f"Accounting discrepancy in Gross Margin: {margin_discrepancies} rows violate taxable - cost = margin")

            # 6d. Quantity Sold Positive Check
            non_pos_qty = conn.execute(text("""
                SELECT count(*) FROM gold.fact_sales WHERE quantity_sold <= 0.000;
            """)).scalar()
            if non_pos_qty != 0:
                errors.append(f"Non-positive quantity sold detected: {non_pos_qty} rows")

            # 6e. Discount Ceiling Check: discount_amount <= gross_sales_amount
            discount_overages = conn.execute(text("""
                SELECT count(*) FROM gold.fact_sales WHERE discount_amount > gross_sales_amount;
            """)).scalar()
            if discount_overages != 0:
                errors.append(f"Discount exceeds gross sales amount in {discount_overages} rows")

            # 7. Distribution Metrics & Summaries
            totals = conn.execute(text("""
                SELECT 
                    SUM(gross_sales_amount) AS total_gross_sales,
                    SUM(discount_amount) AS total_discount,
                    SUM(net_taxable_amount) AS total_taxable,
                    SUM(tax_amount) AS total_tax,
                    SUM(net_sales_amount) AS total_net_sales,
                    SUM(cost_amount) AS total_cost,
                    SUM(gross_margin_amount) AS total_margin,
                    AVG(gross_margin_amount / NULLIF(net_taxable_amount, 0)) * 100 AS avg_margin_pct
                FROM gold.fact_sales;
            """)).fetchone()
            metrics["financial_totals"] = dict(totals._mapping) if totals else {}

            # Distinct coverage
            store_coverage = conn.execute(text("SELECT count(DISTINCT store_key) FROM gold.fact_sales;")).scalar()
            prod_coverage = conn.execute(text("SELECT count(DISTINCT product_key) FROM gold.fact_sales;")).scalar()
            date_coverage = conn.execute(text("SELECT count(DISTINCT date_key) FROM gold.fact_sales;")).scalar()
            metrics["distinct_stores_covered"] = store_coverage
            metrics["distinct_products_covered"] = prod_coverage
            metrics["distinct_dates_covered"] = date_coverage

            if store_coverage < config.store_count:
                errors.append(f"Store coverage incomplete: {store_coverage} of {config.store_count} stores active")
            if prod_coverage < config.product_count:
                errors.append(f"Product coverage incomplete: {prod_coverage} of {config.product_count} products active")
            if date_coverage < config.generation_days:
                errors.append(f"Date coverage incomplete: {date_coverage} of {config.generation_days} dates active")

            # Customer Loyalty vs Guest Walk-in Distribution
            cust_dist = conn.execute(text("""
                SELECT 
                    CASE WHEN customer_key = -1 THEN 'GUEST_WALKIN' ELSE 'REGISTERED_LOYALTY' END AS cust_type,
                    count(*) AS line_count,
                    count(DISTINCT pos_invoice_number) AS receipt_count
                FROM gold.fact_sales
                GROUP BY 1;
            """)).fetchall()
            metrics["customer_distribution"] = [dict(r._mapping) for r in cust_dist]

            # Monthly Sales Breakdown
            monthly_dist = conn.execute(text("""
                SELECT 
                    CONCAT(d.calendar_year, '-', LPAD(d.calendar_month_number::text, 2, '0')) AS calendar_year_month,
                    count(*) AS sales_lines,
                    count(DISTINCT s.pos_invoice_number) AS receipts,
                    ROUND(SUM(s.net_sales_amount), 2) AS total_net_sales,
                    ROUND(SUM(s.gross_margin_amount), 2) AS total_margin
                FROM gold.fact_sales s
                JOIN gold.dim_date d ON s.date_key = d.date_key
                GROUP BY d.calendar_year, d.calendar_month_number
                ORDER BY d.calendar_year, d.calendar_month_number;
            """)).fetchall()
            metrics["monthly_breakdown"] = [dict(r._mapping) for r in monthly_dist]

            # Category Breakdown
            cat_dist = conn.execute(text("""
                SELECT 
                    p.category_id,
                    p.category_name,
                    count(*) AS sales_lines,
                    ROUND(SUM(s.gross_sales_amount), 2) AS total_gross_sales,
                    ROUND(SUM(s.net_sales_amount), 2) AS total_net_sales,
                    ROUND(SUM(s.gross_margin_amount), 2) AS total_margin,
                    ROUND(AVG(s.gross_margin_amount / NULLIF(s.net_taxable_amount, 0)) * 100, 2) AS avg_margin_pct
                FROM gold.fact_sales s
                JOIN gold.dim_product p ON s.product_key = p.product_key
                GROUP BY p.category_id, p.category_name
                ORDER BY p.category_id;
            """)).fetchall()
            metrics["category_breakdown"] = [dict(r._mapping) for r in cat_dist]

            # Store Tier Breakdown
            tier_dist = conn.execute(text("""
                SELECT 
                    st.store_tier,
                    count(DISTINCT s.store_key) AS active_stores,
                    count(*) AS sales_lines,
                    count(DISTINCT s.pos_invoice_number) AS receipts,
                    ROUND(SUM(s.net_sales_amount), 2) AS total_net_sales
                FROM gold.fact_sales s
                JOIN gold.dim_store st ON s.store_key = st.store_key
                GROUP BY st.store_tier
                ORDER BY st.store_tier;
            """)).fetchall()
            metrics["store_tier_breakdown"] = [dict(r._mapping) for r in tier_dist]

        is_valid = len(errors) == 0
        return is_valid, errors, metrics

