"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.5: 4-Way Operational Reconciliation Fact Generator (gold.fact_reconciliation)

Generates daily store-level audit reconciliation records across the four approved BDL-02 domains:
  1. LEG1_TILL: POS Sales Line vs Store Till Journal
  2. LEG2_PAYMENT: Payment Tender vs Bank Merchant Settlement
  3. LEG3_INVENTORY: POS Scanned Units vs ERP Inventory Decrement
  4. LEG4_RETURNS: Customer Returns vs Quarantine / Refund Ledgers

Produces exactly 11,040 records (30 stores x 92 days x 4 domains).
Preserves the Stage 5.3.4 audited operational variances and populates
realistic exception tickets for partial index idx_fact_recon_pending_discrepancy.
"""

import hashlib
import random
import uuid
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Tuple, Optional

from scripts.data_generation.config import GenerationProfileConfig


class ReconciliationGenerator:
    """Generates synthetic 4-way operational reconciliation audit records."""

    def __init__(
        self,
        config: GenerationProfileConfig,
        stores: List[Dict[str, Any]],
        recon_domains: List[Dict[str, Any]],
        sales_by_store_date: Dict[Tuple[int, int], Dict[str, Any]],
        payments_by_store_date: Dict[Tuple[int, int], Dict[str, Any]],
        returns_by_store_date: Dict[Tuple[int, int], Dict[str, Any]],
        movements_by_store_date: Dict[Tuple[int, int], Dict[str, Any]],
        seed: Optional[int] = None,
    ):
        self.config = config
        self.stores = stores
        self.recon_domains = recon_domains
        self.sales_by_store_date = sales_by_store_date
        self.payments_by_store_date = payments_by_store_date
        self.returns_by_store_date = returns_by_store_date
        self.movements_by_store_date = movements_by_store_date
        self.seed = seed if seed is not None else config.random_seed
        self.rng = random.Random(self.seed)

    def generate_all_reconciliations(self) -> List[Dict[str, Any]]:
        """
        Generates exactly 11,040 reconciliation audit records:
        30 stores x 92 days x 4 domains.
        """
        batch_uuid = uuid.uuid4()
        records: List[Dict[str, Any]] = []

        sorted_stores = sorted(self.stores, key=lambda s: s["store_key"])

        curr_date = self.config.start_date
        day_idx = 0

        while curr_date <= self.config.end_date:
            date_key = int(curr_date.strftime("%Y%m%d"))

            for st in sorted_stores:
                st_key = st["store_key"]
                sd_key = (st_key, date_key)

                # Fetch actual source measurements
                s_data = self.sales_by_store_date.get(sd_key, {"net_sales": Decimal("0.00"), "units": Decimal("0.000")})
                p_data = self.payments_by_store_date.get(sd_key, {"tender_amount": Decimal("0.00")})
                r_data = self.returns_by_store_date.get(sd_key, {"returned_units": Decimal("0.000")})
                m_data = self.movements_by_store_date.get(sd_key, {"mov_251_units": Decimal("0.000"), "mov_451_units": Decimal("0.000")})

                # Pseudo-random noise for ticket injection (1.5% target rate)
                sub_hash = (st_key * 104729 + date_key * 31) % 1000000
                is_ticket_day = (sub_hash % 67) == 0  # ~1.49% injection rate

                for d_key in [1, 2, 3, 4]:
                    audit_entity_id = f"AUD-STR{st_key:03d}-{date_key}-DOM{d_key}"

                    if d_key == 1:
                        # Domain 1: POS Sales vs Till Tape
                        sys_a = s_data["net_sales"]
                        threshold = Decimal("500.00")

                        if is_ticket_day:
                            # Injected drawer discrepancy > ₹500
                            discrepancy = Decimal(str((sub_hash % 600) + 550.00)).quantize(Decimal("0.01"))
                            sys_b = sys_a - discrepancy
                            variance = discrepancy
                            ticket_flag = True
                            ticket_id = f"TKT-LEG1-STR{st_key:03d}-{date_key}"
                            inv_status = "PENDING_REVIEW"
                            res_code = "CASH_DRAWER_OVER_SHORT"
                        else:
                            # Normal variance within ₹500 tolerance (e.g. minor penny rounding or coupon tape drift)
                            drift = Decimal(str((sub_hash % 30) * 1.5)).quantize(Decimal("0.01"))
                            sys_b = sys_a - drift
                            variance = drift
                            ticket_flag = False
                            ticket_id = None
                            inv_status = "RESOLVED_EXPLAINED"
                            res_code = "WITHIN_TOLERANCE"

                    elif d_key == 2:
                        # Domain 2: Payment Tender vs Bank Settlement
                        sys_a = p_data["tender_amount"]
                        threshold = Decimal("500.00")

                        if is_ticket_day:
                            # Gateway capture drop or bank chargeback hold > ₹500
                            discrepancy = Decimal(str((sub_hash % 800) + 520.00)).quantize(Decimal("0.01"))
                            sys_b = sys_a - discrepancy
                            variance = discrepancy
                            ticket_flag = True
                            ticket_id = f"TKT-LEG2-STR{st_key:03d}-{date_key}"
                            inv_status = "PENDING_REVIEW"
                            res_code = "GATEWAY_CAPTURE_VARIANCE"
                        else:
                            # Exact or within-penny settlement match
                            drift = Decimal(str((sub_hash % 20) * 0.5)).quantize(Decimal("0.01"))
                            sys_b = sys_a - drift
                            variance = drift
                            ticket_flag = False
                            ticket_id = None
                            inv_status = "RESOLVED_EXPLAINED"
                            res_code = "CLEARED_SETTLEMENT"

                    elif d_key == 3:
                        # Domain 3: POS Scanned Units vs ERP Inventory Decrement
                        # Preserves Stage 5.3.4 audited operational difference (1.77M POS sales vs 227K mov 251)
                        sys_a = s_data["units"]
                        sys_b = m_data["mov_251_units"]
                        variance = (sys_a - sys_b).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                        threshold = Decimal("50.00")

                        # Known architectural sampling variance
                        if is_ticket_day:
                            ticket_flag = True
                            ticket_id = f"TKT-LEG3-STR{st_key:03d}-{date_key}"
                            inv_status = "PENDING_REVIEW"
                            res_code = "ERP_BATCH_LATENCY_INVESTIGATION"
                        else:
                            ticket_flag = False
                            ticket_id = None
                            inv_status = "RESOLVED_EXPLAINED"
                            res_code = "ERP_BATCH_SAMPLING_VARIANCE"

                    else:  # d_key == 4
                        # Domain 4: Returns vs Quarantine Movements
                        # Preserves Stage 5.3.4 findings (quarantine vs direct saleable restock)
                        sys_a = r_data["returned_units"]
                        sys_b = m_data["mov_451_units"]
                        variance = (sys_a - sys_b).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                        threshold = Decimal("10.00")

                        if is_ticket_day:
                            ticket_flag = True
                            ticket_id = f"TKT-LEG4-STR{st_key:03d}-{date_key}"
                            inv_status = "PENDING_REVIEW"
                            res_code = "QUARANTINE_RECEIPT_VARIANCE"
                        else:
                            ticket_flag = False
                            ticket_id = None
                            inv_status = "RESOLVED_EXPLAINED"
                            res_code = "RESTOCKED_SALEABLE_AND_QUARANTINE_LAG"

                    abs_variance = abs(variance)
                    src_rec_id = f"RCN-{date_key}-S{st_key:03d}-D{d_key}"
                    hash_str = f"{date_key}|{st_key}|{d_key}|{sys_a}|{sys_b}|{variance}|{ticket_flag}"
                    rec_hash = hashlib.sha256(hash_str.encode("utf-8")).hexdigest()

                    records.append({
                        "date_key": date_key,
                        "store_key": st_key,
                        "recon_domain_key": d_key,
                        "discrepancy_ticket_id": ticket_id,
                        "audit_entity_identifier": audit_entity_id,
                        "source_system_a_amount": sys_a,
                        "source_system_b_amount": sys_b,
                        "variance_amount": variance,
                        "absolute_variance_amount": abs_variance,
                        "ticket_generated_flag": ticket_flag,
                        "discrepancy_threshold_applied": threshold,
                        "investigation_status": inv_status,
                        "resolution_reason_code": res_code,
                        "source_system": "RECON_ENGINE",
                        "source_record_id": src_rec_id,
                        "ingestion_batch_id": batch_uuid,
                        "record_hash": rec_hash,
                        "data_quality_status": "VALIDATED",
                    })

            curr_date += timedelta(days=1)
            day_idx += 1

        assert len(records) == self.config.reconciliation_audits
        return records

