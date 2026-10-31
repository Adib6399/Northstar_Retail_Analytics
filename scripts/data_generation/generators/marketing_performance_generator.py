"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.5: Marketing Performance Fact Generator (gold.fact_marketing_performance)

Generates daily campaign rollups across stores and active campaigns.
Produces exactly 1,840 records for the INTEGRATION profile (20 store-campaign combinations
per day across 92 days), matching the canonical volume configuration and physical grain.
"""

import hashlib
import random
import uuid
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional

from scripts.data_generation.config import GenerationProfileConfig


class MarketingPerformanceGenerator:
    """Generates synthetic marketing campaign performance rollups."""

    def __init__(
        self,
        config: GenerationProfileConfig,
        stores: List[Dict[str, Any]],
        campaigns: List[Dict[str, Any]],
        promotions: List[Dict[str, Any]],
        seed: Optional[int] = None,
    ):
        self.config = config
        self.stores = stores
        self.campaigns = campaigns
        self.promotions = promotions
        self.seed = seed if seed is not None else config.random_seed
        self.rng = random.Random(self.seed)

        # Map campaign key to associated promotion key if applicable
        self.campaign_promo_map: Dict[int, int] = {
            1: 1,   # Diwali Campaign -> Diwali Grand Festive Promo
            2: 2,   # Loyalty Campaign -> Flat 500 Off Promo
            7: 5,   # Grocery Fresh Campaign -> Grocery Super Saver Promo
            8: 4,   # Monsoon Homefest -> End of Season Clearance Promo
            9: 19,  # Premium Showcase -> Seasonal Promo 019
        }

    def generate_all_performance(self) -> List[Dict[str, Any]]:
        """
        Generates exactly config.marketing_performance_rows (1,840 records).
        Allocates 20 store-campaign combinations per day across the 92 calendar days.
        """
        batch_uuid = uuid.uuid4()
        records: List[Dict[str, Any]] = []

        total_days = self.config.generation_days
        target_rows = self.config.marketing_performance_rows
        rows_per_day = target_rows // total_days  # Exactly 20 rows/day (20 * 92 = 1840)

        # Store tier multipliers for spend and sales scaling
        tier_multipliers = {"TIER_1": 1.5, "TIER_2": 1.0, "TIER_3": 0.7}

        curr_date = self.config.start_date
        day_index = 0

        while curr_date <= self.config.end_date:
            date_key = int(curr_date.strftime("%Y%m%d"))

            # Determine active campaigns on this date
            active_campaigns = [
                c for c in self.campaigns
                if c["start_date"] <= curr_date <= c["end_date"]
            ]
            if not active_campaigns:
                # Fallback to closest campaign if gap exists
                active_campaigns = [self.campaigns[0]]

            # Distribute rows_per_day (20) across active campaigns
            num_active = len(active_campaigns)
            stores_per_camp = rows_per_day // num_active
            remainder = rows_per_day % num_active

            # Deterministic store selection per campaign for this day
            store_offset = (day_index * 7) % len(self.stores)
            rotated_stores = self.stores[store_offset:] + self.stores[:store_offset]

            store_alloc_idx = 0
            for c_idx, camp in enumerate(active_campaigns):
                count_for_camp = stores_per_camp + (1 if c_idx < remainder else 0)
                selected_stores = rotated_stores[store_alloc_idx : store_alloc_idx + count_for_camp]
                store_alloc_idx += count_for_camp

                camp_key = camp["campaign_key"]
                promo_key = self.campaign_promo_map.get(camp_key, -1)

                for st in selected_stores:
                    st_key = st["store_key"]
                    st_tier = st.get("store_tier", "TIER_2")
                    mult = Decimal(str(tier_multipliers.get(st_tier, 1.0)))

                    # 1. Customer Counts
                    test_cust_cnt = int(self.rng.randint(60, 220) * float(mult))
                    ctrl_cust_cnt = max(5, int(test_cust_cnt * 0.108))  # ~10% holdout

                    # 2. Spend allocation (₹800 to ₹3,500 scaled by store tier)
                    base_spend = Decimal(str(self.rng.randint(800, 3200))) * mult
                    spend_amount = base_spend.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                    # 3. Control cohort sales (scaled to test cohort size for true incremental comparison)
                    avg_spend_per_cust = Decimal(str(self.rng.uniform(180.0, 420.0)))
                    ctrl_sales_raw = (Decimal(ctrl_cust_cnt) * avg_spend_per_cust).quantize(Decimal("0.01"))
                    # Scale control sales to test cohort size
                    scaled_ctrl_sales = (ctrl_sales_raw * Decimal(test_cust_cnt) / Decimal(ctrl_cust_cnt)).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )

                    # 4. Lift generation (positive lift in 92% of cases, slight noise in 8%)
                    lift_factor = Decimal(str(self.rng.uniform(1.08, 1.28))) if self.rng.random() > 0.08 else Decimal(str(self.rng.uniform(0.96, 1.02)))
                    test_sales = (scaled_ctrl_sales * lift_factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    lift_amount = test_sales - scaled_ctrl_sales

                    # 5. Incremental margin and ROMI
                    margin_pct = Decimal("0.32")  # Average gross margin 32%
                    inc_margin = (lift_amount * margin_pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                    romi_ratio = (inc_margin / spend_amount).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

                    # Attribution Status
                    if lift_amount > Decimal("500.00"):
                        attr_status = "CONFIRMED"
                    elif lift_amount >= Decimal("0.00"):
                        attr_status = "STATISTICALLY_INSIGNIFICANT"
                    else:
                        attr_status = "UNATTRIBUTED_MISSING_CONTROL"

                    src_rec_id = f"MKTG-D{date_key}-S{st_key:03d}-C{camp_key}"
                    hash_str = f"{date_key}|{st_key}|{camp_key}|{test_sales}|{spend_amount}"
                    rec_hash = hashlib.sha256(hash_str.encode("utf-8")).hexdigest()

                    records.append({
                        "date_key": date_key,
                        "store_key": st_key,
                        "campaign_key": camp_key,
                        "promotion_key": promo_key,
                        "test_cohort_sales_amount": test_sales,
                        "control_cohort_sales_amount": scaled_ctrl_sales,
                        "incremental_sales_lift_amount": lift_amount,
                        "incremental_gross_margin_amount": inc_margin,
                        "attributed_marketing_spend_amount": spend_amount,
                        "test_customer_count": test_cust_cnt,
                        "control_customer_count": ctrl_cust_cnt,
                        "incremental_romi_ratio": romi_ratio,
                        "attribution_status": attr_status,
                        "source_system": "ATTRIBUTION",
                        "source_record_id": src_rec_id,
                        "ingestion_batch_id": batch_uuid,
                        "record_hash": rec_hash,
                        "data_quality_status": "VALIDATED",
                    })

            curr_date += timedelta(days=1)
            day_index += 1

        assert len(records) == target_rows, f"Marketing performance generated {len(records)}, expected {target_rows}"
        return records

