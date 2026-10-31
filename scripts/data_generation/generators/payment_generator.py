"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.4: Payment Fact Generator (gold.fact_payments)

Generates synthetic payment tender records reconciling 100% with sales checkout receipts.
Implements the approved 8% split-tender ratio (1.08 tenders/receipt), resulting in
exactly 496,800 payment records across 460,000 sales invoices for the INTEGRATION profile.
"""

import hashlib
import random
import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional

from scripts.data_generation.config import GenerationProfileConfig


class PaymentGenerator:
    """Generates synthetic payment tender transactions for gold.fact_payments."""

    def __init__(
        self,
        config: GenerationProfileConfig,
        payment_methods: List[Dict[str, Any]],
        seed: Optional[int] = None,
    ):
        self.config = config
        self.payment_methods = payment_methods
        self.seed = seed if seed is not None else config.random_seed
        self.rng = random.Random(self.seed)

        # Map methods by tender type / code for realistic customer choice
        self.methods_by_code: Dict[str, Dict[str, Any]] = {
            m["tender_type_code"]: m for m in self.payment_methods
        }

    def generate_payments_for_receipts(
        self,
        receipts: List[Dict[str, Any]],
        start_receipt_index: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Generates payment records for a batch of sales receipts.
        Every single-tender receipt gets 1 payment record.
        Receipts selected for split tender (exactly 8% overall) get 2 payment records.
        Guarantees that sum(tender_amount) per invoice == invoice_net_sales.
        """
        batch_uuid = uuid.uuid4()
        payment_records: List[Dict[str, Any]] = []

        # Available tender codes
        cash_method = self.methods_by_code.get("CASH", self.payment_methods[0])
        upi_qr = self.methods_by_code.get("UPI_QR", self.payment_methods[1])
        upi_auto = self.methods_by_code.get("UPI_AUTOPAY", upi_qr)
        cc_visa = self.methods_by_code.get("CC_VISA", self.payment_methods[2])
        cc_mc = self.methods_by_code.get("CC_MASTERCARD", cc_visa)
        dc_rupay = self.methods_by_code.get("DC_RUPAY", upi_qr)
        dc_visa = self.methods_by_code.get("DC_VISA", cc_visa)
        gift_voucher = self.methods_by_code.get("GIFT_VOUCHER", cash_method)

        for local_idx, receipt in enumerate(receipts):
            global_idx = start_receipt_index + local_idx
            invoice_num = receipt["pos_invoice_number"]
            date_key = receipt["date_key"]
            store_key = receipt["store_key"]
            customer_key = receipt["customer_key"]
            invoice_total = Decimal(str(receipt["invoice_net_sales"]))

            # Deterministic split-tender rule: exactly 2 out of every 25 receipts (8.00%)
            is_split_tender = (global_idx % 25) in (3, 17)

            if not is_split_tender:
                # Single Tender (92% of receipts)
                # Customer choice: Walk-in (-1) prefers cash/UPI; Loyalty prefers UPI/Cards
                if customer_key == -1:
                    roll = self.rng.random()
                    if roll < 0.58:
                        method = cash_method
                    elif roll < 0.90:
                        method = upi_qr
                    else:
                        method = dc_rupay
                else:
                    roll = self.rng.random()
                    if roll < 0.45:
                        method = upi_qr
                    elif roll < 0.58:
                        method = upi_auto
                    elif roll < 0.72:
                        method = cc_visa
                    elif roll < 0.84:
                        method = cc_mc
                    elif roll < 0.92:
                        method = dc_visa
                    elif roll < 0.97:
                        method = cash_method
                    else:
                        method = gift_voucher

                tender_amount = invoice_total
                mdr_rate = Decimal(str(method.get("contracted_mdr_fee_pct", method.get("merchant_discount_rate_pct", "0.0000"))))
                expected_mdr = (tender_amount * mdr_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                is_electronic = method["tender_type_code"] not in ("CASH", "GIFT_VOUCHER")
                bank_utr = f"UTR{date_key}{global_idx:08d}01" if is_electronic else None
                gateway_batch = f"GB-{method.get('acquirer_network', method.get('settlement_acquirer_channel', 'BANK'))}-{date_key}" if is_electronic else None
                txn_id = f"TXN-{invoice_num}-01"

                hash_str = f"{invoice_num}|1|{date_key}|{method['payment_method_key']}|{tender_amount}"
                rec_hash = hashlib.sha256(hash_str.encode("utf-8")).hexdigest()

                payment_records.append({
                    "date_key": date_key,
                    "store_key": store_key,
                    "payment_method_key": method["payment_method_key"],
                    "customer_key": customer_key,
                    "pos_invoice_number": invoice_num,
                    "payment_line_number": 1,
                    "payment_transaction_id": txn_id,
                    "bank_utr_number": bank_utr,
                    "gateway_batch_id": gateway_batch,
                    "tender_amount": tender_amount,
                    "gateway_deducted_fee_amount": expected_mdr,
                    "expected_mdr_fee_amount": expected_mdr,
                    "mdr_fee_discrepancy_amount": Decimal("0.00"),
                    "settlement_variance_amount": Decimal("0.00"),
                    "settlement_status": "CLEARED",
                    "source_system": "POS_ENGINE_OMNI",
                    "source_record_id": f"{invoice_num}-P01",
                    "ingestion_batch_id": batch_uuid,
                    "record_hash": rec_hash,
                    "data_quality_status": "VALIDATED",
                })
            else:
                # Split Tender (8% of receipts -> exactly 2 payment records)
                # Typically Cash + UPI, or Gift Voucher + Card/UPI
                split_roll = self.rng.random()
                if split_roll < 0.50:
                    method1 = cash_method
                    method2 = upi_qr
                elif split_roll < 0.80:
                    method1 = gift_voucher
                    method2 = cc_visa
                else:
                    method1 = dc_rupay
                    method2 = upi_qr

                # Primary tender takes ~40-60% of total
                ratio = Decimal("0.40") if self.rng.random() < 0.5 else Decimal("0.50")
                amount1 = (invoice_total * ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                amount2 = invoice_total - amount1  # Exact balance guarantee

                for line_no, (m, amt) in enumerate([(method1, amount1), (method2, amount2)], start=1):
                    mdr_rate = Decimal(str(m.get("contracted_mdr_fee_pct", m.get("merchant_discount_rate_pct", "0.0000"))))
                    expected_mdr = (amt * mdr_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                    is_elec = m["tender_type_code"] not in ("CASH", "GIFT_VOUCHER")
                    bank_utr = f"UTR{date_key}{global_idx:08d}{line_no:02d}" if is_elec else None
                    gateway_batch = f"GB-{m.get('acquirer_network', m.get('settlement_acquirer_channel', 'BANK'))}-{date_key}" if is_elec else None
                    txn_id = f"TXN-{invoice_num}-{line_no:02d}"

                    hash_str = f"{invoice_num}|{line_no}|{date_key}|{m['payment_method_key']}|{amt}"
                    rec_hash = hashlib.sha256(hash_str.encode("utf-8")).hexdigest()

                    payment_records.append({
                        "date_key": date_key,
                        "store_key": store_key,
                        "payment_method_key": m["payment_method_key"],
                        "customer_key": customer_key,
                        "pos_invoice_number": invoice_num,
                        "payment_line_number": line_no,
                        "payment_transaction_id": txn_id,
                        "bank_utr_number": bank_utr,
                        "gateway_batch_id": gateway_batch,
                        "tender_amount": amt,
                        "gateway_deducted_fee_amount": expected_mdr,
                        "expected_mdr_fee_amount": expected_mdr,
                        "mdr_fee_discrepancy_amount": Decimal("0.00"),
                        "settlement_variance_amount": Decimal("0.00"),
                        "settlement_status": "CLEARED",
                        "source_system": "POS_ENGINE_OMNI",
                        "source_record_id": f"{invoice_num}-P{line_no:02d}",
                        "ingestion_batch_id": batch_uuid,
                        "record_hash": rec_hash,
                        "data_quality_status": "VALIDATED",
                    })

        return payment_records
