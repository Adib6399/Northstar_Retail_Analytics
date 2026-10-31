"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.3: Historical Sales Fact Generator (gold.fact_sales)

Generates synthetic transactional sales line items adhering to physical schema specifications,
financial accounting identities, deterministic footfall curves, and exact profile volume counts.
Supports DEV (10,500 lines) and INTEGRATION (1,380,000 lines) profiles.
"""

import hashlib
import random
import uuid
from datetime import date, datetime, time, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional

from scripts.data_generation.config import GenerationProfileConfig, ProfileType


class SalesGenerator:
    """Generates synthetic POS retail sales lines conforming to gold.fact_sales schema."""

    def __init__(
        self,
        config: GenerationProfileConfig,
        stores: List[Dict[str, Any]],
        products: List[Dict[str, Any]],
        promotions: List[Dict[str, Any]],
        customers: List[int],
        seed: Optional[int] = None,
    ):
        self.config = config
        self.stores = stores[:config.store_count]
        self.products = products[:config.product_count]
        self.promotions = promotions[:config.promotion_count]
        self.registered_customers = customers[:config.customer_count]
        self.seed = seed if seed is not None else config.random_seed
        self.rng = random.Random(self.seed)

        # Categorize products by category and velocity class for realistic basket selection
        self.products_by_category: Dict[str, List[Dict[str, Any]]] = {}
        for p in self.products:
            cat = p.get("category_id", "FMCG")
            self.products_by_category.setdefault(cat, []).append(p)

        # Category selection weights in basket items
        self.category_weights = {
            "FMCG": 0.45,
            "APPR": 0.25,
            "HOME": 0.18,
            "ELEC": 0.12,
        }

        # Store tier multipliers for daily footfall distribution
        self.store_tier_weights = {
            "TIER_1": 1.25,
            "TIER_2": 1.00,
            "TIER_3": 0.75,
        }

        # Precompute day-by-day receipt quotas
        self.daily_receipt_quotas = self._calculate_daily_receipt_quotas()

    def _calculate_daily_receipt_quotas(self) -> Dict[date, int]:
        """
        Calculates exact integer receipt quotas per calendar day.
        Applies intra-week footfall weights and Indian festive multipliers (Diwali),
        then adjusts residual rounding differences so sum(receipts) == total_receipts.
        """
        days = []
        curr = self.config.start_date
        while curr <= self.config.end_date:
            days.append(curr)
            curr += timedelta(days=1)

        total_days = len(days)
        target_receipts = self.config.total_receipts

        # Day-of-week multipliers (0=Mon, 6=Sun)
        dow_weights = {
            0: 0.85, 1: 0.85, 2: 0.85, 3: 0.85,  # Mon-Thu
            4: 1.10,                              # Fri
            5: 1.35, 6: 1.35                      # Sat-Sun peak
        }

        raw_weights = []
        for d in days:
            w = dow_weights[d.weekday()]
            # Festive season adjustments in October 2026
            if d >= date(2026, 10, 15):
                w *= 1.40  # Diwali peak surge
            elif d >= date(2026, 10, 1):
                w *= 1.15  # Dussehra / Pre-festive buildup
            raw_weights.append(w)

        total_weight = sum(raw_weights)
        quotas = [int(round(w / total_weight * target_receipts)) for w in raw_weights]
        diff = target_receipts - sum(quotas)

        # Distribute residual difference (+/- 1) across the largest volume days
        sorted_indices = sorted(range(total_days), key=lambda i: raw_weights[i], reverse=True)
        for i in range(abs(diff)):
            idx = sorted_indices[i % total_days]
            quotas[idx] += 1 if diff > 0 else -1

        assert sum(quotas) == target_receipts, (
            f"Receipt allocation mismatch: sum={sum(quotas)} vs target={target_receipts}"
        )
        return dict(zip(days, quotas))

    def _calculate_store_receipt_quotas(self, total_day_receipts: int) -> List[int]:
        """
        Distributes a single day's total receipts across the active stores based on tier.
        Guarantees that sum(store_receipts) == total_day_receipts.
        """
        store_weights = [self.store_tier_weights.get(s.get("store_tier", "TIER_2"), 1.0) for s in self.stores]
        total_weight = sum(store_weights)

        quotas = [int(round(w / total_weight * total_day_receipts)) for w in store_weights]
        diff = total_day_receipts - sum(quotas)

        sorted_indices = sorted(range(len(self.stores)), key=lambda i: store_weights[i], reverse=True)
        for i in range(abs(diff)):
            idx = sorted_indices[i % len(self.stores)]
            quotas[idx] += 1 if diff > 0 else -1

        assert sum(quotas) == total_day_receipts
        return quotas

    def generate_day_sales(self, target_date: date) -> List[Dict[str, Any]]:
        """
        Generates all itemized sales lines for all stores on a specific calendar date.
        Guarantees that total lines generated on this day == 3.0 * total_day_receipts.
        """
        total_day_receipts = self.daily_receipt_quotas[target_date]
        target_day_lines = round(total_day_receipts * self.config.avg_lines_per_receipt)

        # Basket size integer distribution ensuring EXACT 3.0 average:
        # C1 (1 line) = k1, C2 (2 lines) = k2, C3 (3 lines) = R - 2*k1 - 2*k2, C4 = k2, C5 = k1
        k1 = int(round(0.10 * total_day_receipts))
        k2 = int(round(0.20 * total_day_receipts))
        c3 = total_day_receipts - 2 * k1 - 2 * k2
        basket_counts = [k1, k2, c3, k2, k1]  # for sizes 1, 2, 3, 4, 5
        assert sum(basket_counts) == total_day_receipts

        # Build basket sizes pool and shuffle deterministically
        basket_sizes_pool = []
        for sz, cnt in zip([1, 2, 3, 4, 5], basket_counts):
            basket_sizes_pool.extend([sz] * cnt)
        self.rng.shuffle(basket_sizes_pool)

        # Store-level receipt distribution
        store_quotas = self._calculate_store_receipt_quotas(total_day_receipts)

        # Active promotions on this date
        active_promotions = [
            p for p in self.promotions
            if p["start_date"] <= target_date <= p["end_date"]
        ]
        if not active_promotions:
            # Fallback to any promotion with minimum key to satisfy NOT NULL FK constraint
            active_promotions = [min(self.promotions, key=lambda x: x["promotion_key"])]

        # Find general active promotion for fallback lines
        general_promo = active_promotions[0]

        date_key = int(target_date.strftime("%Y%m%d"))
        batch_uuid = uuid.uuid4()
        lines: List[Dict[str, Any]] = []

        pool_idx = 0
        receipt_counter = 0

        for s_idx, store in enumerate(self.stores):
            store_key = store["store_key"]
            store_id = store["store_id"]
            num_receipts = store_quotas[s_idx]

            for r_idx in range(num_receipts):
                receipt_counter += 1
                basket_size = basket_sizes_pool[pool_idx]
                pool_idx += 1

                pos_invoice_number = f"INV-{store_id}-{date_key}-{r_idx + 1:05d}"

                # Customer assignment: 30% guest walk-in (-1), 70% registered loyalty member
                if self.rng.random() < 0.30:
                    customer_key = -1
                else:
                    customer_key = self.rng.choice(self.registered_customers)

                # Terminal and Cashier assignment
                terminal_num = ((store_key * 7 + r_idx) % 4) + 1
                pos_terminal_id = f"POS-{terminal_num:02d}"
                cashier_num = ((store_key * 11 + r_idx) % 8) + 1
                cashier_employee_id = f"EMP-{store_id[4:]}-{cashier_num:02d}"

                # Transaction timestamp (between 09:30 and 21:30 IST)
                sec_offset = int((r_idx / max(1, num_receipts)) * 43200) + self.rng.randint(-30, 30)
                sec_offset = max(0, min(43200, sec_offset))
                base_time = datetime(
                    target_date.year, target_date.month, target_date.day,
                    9, 30, 0, tzinfo=timezone.utc
                ) + timedelta(seconds=sec_offset)

                for line_num in range(1, basket_size + 1):
                    # Category and product selection
                    cat_roll = self.rng.random()
                    if cat_roll < 0.45:
                        selected_cat = "FMCG"
                    elif cat_roll < 0.70:
                        selected_cat = "APPR"
                    elif cat_roll < 0.88:
                        selected_cat = "HOME"
                    else:
                        selected_cat = "ELEC"

                    cat_prods = self.products_by_category.get(selected_cat, self.products)
                    product = self.rng.choice(cat_prods)

                    # Quantity sold
                    if selected_cat == "FMCG":
                        qty_roll = self.rng.random()
                        qty = Decimal("1.000") if qty_roll < 0.60 else (Decimal("2.000") if qty_roll < 0.85 else Decimal("3.000"))
                    elif selected_cat == "APPR":
                        qty = Decimal("2.000") if self.rng.random() < 0.15 else Decimal("1.000")
                    else:
                        qty = Decimal("1.000")

                    unit_mrp = Decimal(str(product["mrp"]))
                    unit_cost_price = Decimal(str(product["standard_cost_price"]))
                    unit_selling_price = unit_mrp  # Base catalog selling price

                    gross_sales_amount = (qty * unit_selling_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                    # Promotion and discount calculation
                    promo_applied = False
                    discount_amount = Decimal("0.00")
                    selected_promo = general_promo

                    # Higher promo likelihood during festive period (35%) vs normal (20%)
                    promo_prob = 0.35 if target_date >= date(2026, 10, 15) else 0.20
                    if self.rng.random() < promo_prob and active_promotions:
                        candidate_promo = self.rng.choice(active_promotions)
                        selected_promo = candidate_promo
                        promo_applied = True

                        ptype = candidate_promo["discount_type"]
                        pval = Decimal(str(candidate_promo["discount_value"]))

                        if ptype == "PERCENTAGE":
                            discount_amount = (gross_sales_amount * (pval / Decimal("100.00"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                        elif ptype == "FLAT_AMOUNT":
                            discount_amount = min(pval.quantize(Decimal("0.01")), gross_sales_amount)
                        elif ptype == "BOGO":
                            if qty >= Decimal("2.000"):
                                discount_amount = (gross_sales_amount / Decimal("2.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                            else:
                                discount_amount = Decimal("0.00")
                        elif ptype == "CLEARANCE_MARKDOWN":
                            discount_amount = (gross_sales_amount * (pval / Decimal("100.00"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                    discount_amount = min(discount_amount, gross_sales_amount)
                    net_taxable_amount = gross_sales_amount - discount_amount

                    gst_rate_pct = Decimal(str(product["gst_rate_pct"]))
                    tax_amount = (net_taxable_amount * gst_rate_pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    net_sales_amount = net_taxable_amount + tax_amount

                    cost_amount = (qty * unit_cost_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    gross_margin_amount = net_taxable_amount - cost_amount

                    source_record_id = f"{pos_invoice_number}-L{line_num:02d}"

                    # Cryptographic record hash for tamper-evident data engineering lineage
                    hash_str = f"{pos_invoice_number}|{line_num}|{date_key}|{store_key}|{product['product_key']}|{net_sales_amount}"
                    record_hash = hashlib.sha256(hash_str.encode("utf-8")).hexdigest()

                    lines.append({
                        "date_key": date_key,
                        "store_key": store_key,
                        "product_key": product["product_key"],
                        "customer_key": customer_key,
                        "promotion_key": selected_promo["promotion_key"],
                        "pos_invoice_number": pos_invoice_number,
                        "pos_line_number": line_num,
                        "pos_terminal_id": pos_terminal_id,
                        "cashier_employee_id": cashier_employee_id,
                        "transaction_timestamp": base_time,
                        "quantity_sold": qty,
                        "unit_mrp": unit_mrp,
                        "unit_selling_price": unit_selling_price,
                        "gross_sales_amount": gross_sales_amount,
                        "discount_amount": discount_amount,
                        "net_taxable_amount": net_taxable_amount,
                        "tax_amount": tax_amount,
                        "net_sales_amount": net_sales_amount,
                        "unit_cost_price": unit_cost_price,
                        "cost_amount": cost_amount,
                        "gross_margin_amount": gross_margin_amount,
                        "source_system": "POS_ENGINE_OMNI",
                        "source_record_id": source_record_id,
                        "ingestion_batch_id": batch_uuid,
                        "record_hash": record_hash,
                        "data_quality_status": "VALIDATED",
                    })

        assert len(lines) == target_day_lines, (
            f"Daily lines mismatch for {target_date}: generated {len(lines)} vs target {target_day_lines}"
        )
        return lines

