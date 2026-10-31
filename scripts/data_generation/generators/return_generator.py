"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.4: Returns Fact Generator (gold.fact_returns)

Generates synthetic merchandise returns strictly referencing authentic historical sales rows.
Applies the approved 2.50% return rate against 1,380,000 sales lines, resulting in exactly
34,500 return records with realistic category-specific return reasons and refund reconciliations.
"""

import hashlib
import random
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional

from scripts.data_generation.config import GenerationProfileConfig


class ReturnGenerator:
    """Generates synthetic customer returns referencing gold.fact_sales."""

    def __init__(
        self,
        config: GenerationProfileConfig,
        return_reasons: List[Dict[str, Any]],
        seed: Optional[int] = None,
    ):
        self.config = config
        self.return_reasons = return_reasons
        self.seed = seed if seed is not None else config.random_seed
        self.rng = random.Random(self.seed)

        # Reason code to key lookup
        self.reason_map: Dict[str, int] = {
            r["reason_code"]: r["return_reason_key"] for r in self.return_reasons
        }

    def generate_returns_from_sales(
        self,
        sales_lines: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Generates return records from selected historical sales lines.
        Ensures returned_units <= sold_units, return_date >= sales_date,
        and refund_amount reconciles to unit net sales amount.
        """
        batch_uuid = uuid.uuid4()
        returns: List[Dict[str, Any]] = []

        max_date = self.config.end_date

        for idx, sale in enumerate(sales_lines):
            store_key = sale["store_key"]
            product_key = sale["product_key"]
            customer_key = sale["customer_key"]
            orig_date_key = sale["date_key"]
            pos_invoice_number = sale["pos_invoice_number"]
            category_id = sale.get("category_id", "APPR")
            sales_fact_key = sale.get("sales_fact_key", idx + 1)

            # Parse original date
            s_year = orig_date_key // 10000
            s_month = (orig_date_key % 10000) // 100
            s_day = orig_date_key % 100
            orig_sale_date = date(s_year, s_month, s_day)

            # Return date: 1 to 14 days later, bounded by max_date
            lag_days = 1 + (sales_fact_key % 14)
            ret_date = orig_sale_date + timedelta(days=lag_days)
            if ret_date > max_date:
                ret_date = orig_sale_date  # Same-day return if near end of period
            ret_date_key = int(ret_date.strftime("%Y%m%d"))

            # Return Reason selection based on merchandise category
            if category_id == "APPR":
                choices = ["WRONG_SIZE", "WRONG_SIZE", "DEFECT", "BUYER_REMORSE"]
            elif category_id == "ELEC":
                choices = ["DEFECT", "DEFECT", "NOT_AS_DESCRIBED", "BUYER_REMORSE"]
            elif category_id == "FMCG":
                choices = ["EXPIRED", "DEFECT"]
            else:  # HOME
                choices = ["DEFECT", "BUYER_REMORSE", "NOT_AS_DESCRIBED"]

            r_code = choices[sales_fact_key % len(choices)]
            reason_key = self.reason_map.get(r_code, 1)

            # Returned units & refund amount
            sold_qty = Decimal(str(sale["quantity_sold"]))
            net_sales = Decimal(str(sale["net_sales_amount"]))
            returned_units = Decimal("1.000") if sold_qty >= Decimal("1.000") else sold_qty

            unit_refund = (net_sales / sold_qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            refund_amount = (returned_units * unit_refund).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # Restocking fee (nominal 5% only for BUYER_REMORSE on high-value items, else 0.00)
            restocking_fee = Decimal("0.00")
            if r_code == "BUYER_REMORSE" and refund_amount > Decimal("1000.00"):
                restocking_fee = (refund_amount * Decimal("0.05")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            return_receipt_id = f"RET-STR-{store_key:03d}-{ret_date_key}-{sales_fact_key:08d}"
            manager_id = f"MGR-STR-{store_key:03d}-01"
            quarantine_grn = f"QGRN-{ret_date_key}-{sales_fact_key:08d}"
            source_rec_id = f"{return_receipt_id}-L01"

            hash_str = f"{return_receipt_id}|1|{pos_invoice_number}|{refund_amount}"
            rec_hash = hashlib.sha256(hash_str.encode("utf-8")).hexdigest()

            returns.append({
                "date_key": ret_date_key,
                "original_sales_date_key": orig_date_key,
                "store_key": store_key,
                "product_key": product_key,
                "customer_key": customer_key,
                "return_reason_key": reason_key,
                "return_receipt_id": return_receipt_id,
                "return_line_number": 1,
                "original_invoice_number": pos_invoice_number,
                "authorizing_manager_id": manager_id,
                "erp_quarantine_grn_id": quarantine_grn,
                "returned_units": returned_units,
                "refund_amount": refund_amount,
                "restocking_fee_amount": restocking_fee,
                "is_unreferenced_return_flag": False,
                "is_quarantine_verified_flag": True,
                "source_system": "POS_ENGINE_OMNI",
                "source_record_id": source_rec_id,
                "ingestion_batch_id": batch_uuid,
                "record_hash": rec_hash,
                "data_quality_status": "VALIDATED",
            })

        return returns

