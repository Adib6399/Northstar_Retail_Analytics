"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.2: Promotion Dimension Generator (gold.dim_promotion)

Generates fictional promotional offers and discounts conforming to physical specifications.
Satisfies discount type check constraints, date range constraints (start_date <= end_date),
and unique promo_code. Supports DEV (5 promotions) and INTEGRATION (25 promotions).
"""

from datetime import date
from decimal import Decimal
from typing import List, Dict, Any

DEV_PROMOTIONS = [
    {
        "promo_code": "PROMO-DIWALI-2026",
        "promo_name": "Diwali Grand Festive Discount 2026",
        "discount_type": "PERCENTAGE",
        "discount_value": Decimal("15.00"),
        "start_date": date(2026, 10, 15),
        "end_date": date(2026, 11, 15),
        "clearance_aging_tier": "NONE",
        "is_clearance_flag": False,
    },
    {
        "promo_code": "PROMO-FLAT500-2026",
        "promo_name": "Flat 500 Off on Premium Electronics",
        "discount_type": "FLAT_AMOUNT",
        "discount_value": Decimal("500.00"),
        "start_date": date(2026, 10, 1),
        "end_date": date(2026, 10, 31),
        "clearance_aging_tier": "NONE",
        "is_clearance_flag": False,
    },
    {
        "promo_code": "PROMO-BOGO-SHIRTS",
        "promo_name": "Buy 1 Get 1 Free on Mens Casual Shirts",
        "discount_type": "BOGO",
        "discount_value": Decimal("100.00"),
        "start_date": date(2026, 9, 1),
        "end_date": date(2026, 10, 31),
        "clearance_aging_tier": "NONE",
        "is_clearance_flag": False,
    },
    {
        "promo_code": "PROMO-CLEAR-TIER1",
        "promo_name": "End of Season Clearance 90+ Days Aging",
        "discount_type": "CLEARANCE_MARKDOWN",
        "discount_value": Decimal("35.00"),
        "start_date": date(2026, 8, 1),
        "end_date": date(2026, 10, 31),
        "clearance_aging_tier": "TIER_1_90D",
        "is_clearance_flag": True,
    },
    {
        "promo_code": "PROMO-FMCG-COMBO",
        "promo_name": "Grocery Super Saver 10% Off",
        "discount_type": "PERCENTAGE",
        "discount_value": Decimal("10.00"),
        "start_date": date(2026, 10, 20),
        "end_date": date(2026, 10, 31),
        "clearance_aging_tier": "NONE",
        "is_clearance_flag": False,
    },
]

# Additional 20 promotions for INTEGRATION
ADDITIONAL_PROMOTIONS = []
DISCOUNT_TYPES = ["PERCENTAGE", "FLAT_AMOUNT", "BOGO", "CLEARANCE_MARKDOWN"]

for i in range(6, 26):
    dtype = DISCOUNT_TYPES[(i - 1) % len(DISCOUNT_TYPES)]
    dval = Decimal("20.00") if dtype == "PERCENTAGE" else (Decimal("250.00") if dtype == "FLAT_AMOUNT" else (Decimal("50.00") if dtype == "CLEARANCE_MARKDOWN" else Decimal("100.00")))
    is_clear = (dtype == "CLEARANCE_MARKDOWN")
    tier = "TIER_2_180D" if is_clear else "NONE"

    # Start date in 2026
    start_m = 1 + (i % 10)
    start_d = date(2026, start_m, 1)
    end_d = date(2026, min(start_m + 1, 12), 28)

    ADDITIONAL_PROMOTIONS.append({
        "promo_code": f"PROMO-INT-{i:03d}",
        "promo_name": f"Northstar Seasonal Promotion {i:03d}",
        "discount_type": dtype,
        "discount_value": dval,
        "start_date": start_d,
        "end_date": end_d,
        "clearance_aging_tier": tier,
        "is_clearance_flag": is_clear,
    })


def generate_dim_promotion_records(promotion_count: int = 5) -> List[Dict[str, Any]]:
    """
    Generates promotional dimension records.
    DEV: 5 promotions.
    INTEGRATION: 25 promotions.
    """
    pool = DEV_PROMOTIONS + ADDITIONAL_PROMOTIONS
    return [dict(p) for p in pool[:promotion_count]]
