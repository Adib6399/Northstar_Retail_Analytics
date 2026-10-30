"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.2: Customer Dimension Generator (gold.dim_customer)

Generates synthetic, privacy-safe customer loyalty profiles conforming to Domain C specifications.
Uses HMAC-SHA256 pseudonymization with pepper for customer_sk. Zero real PII.
Preserves sentinel customer_key = -1.
Supports DEV (200 profiles) and INTEGRATION (10,000 profiles).
"""

from decimal import Decimal
from typing import List, Dict, Any
from scripts.data_generation.utilities.crypto_utils import generate_customer_sk


def generate_dim_customer_records(
    customer_count: int = 200,
    store_ids: List[str] = None,
    pepper: str = "northstar_retail_hmac_pepper_seed_2026",
    start_index: int = 1,
) -> List[Dict[str, Any]]:
    """
    Generates synthetic customer dimension records.
    start_index allows deterministic delta generation (e.g. 1 to 200 for DEV, 201 to 10000 for INT).
    """
    if not store_ids:
        store_ids = ["STR-KA-001"]

    records = []

    for i in range(start_index, start_index + customer_count):
        natural_id = f"CUST-{i:06d}"
        customer_sk = generate_customer_sk(natural_id, pepper)

        # Registration store
        reg_store_id = store_ids[(i - 1) % len(store_ids)]

        # Loyalty Tier distribution: 60% Bronze, 25% Silver, 12% Gold, 3% Platinum
        tier_mod = i % 100
        if tier_mod < 60:
            tier = "BRONZE"
            recency = (i % 3) + 1
            freq = (i % 3) + 1
            mon = (i % 3) + 1
            lifetime_spend = Decimal(str(500.0 + (i % 50) * 120.0)).quantize(Decimal("0.01"))
        elif tier_mod < 85:
            tier = "SILVER"
            recency = ((i + 1) % 4) + 2
            freq = ((i + 2) % 4) + 2
            mon = ((i + 3) % 4) + 2
            lifetime_spend = Decimal(str(5000.0 + (i % 50) * 350.0)).quantize(Decimal("0.01"))
        elif tier_mod < 97:
            tier = "GOLD"
            recency = ((i + 2) % 3) + 3
            freq = ((i + 3) % 3) + 3
            mon = ((i + 1) % 3) + 3
            lifetime_spend = Decimal(str(25000.0 + (i % 50) * 800.0)).quantize(Decimal("0.01"))
        else:
            tier = "PLATINUM"
            recency = 5 if i % 2 == 0 else 4
            freq = 5
            mon = 5
            lifetime_spend = Decimal(str(75000.0 + (i % 50) * 2500.0)).quantize(Decimal("0.01"))

        # Segment and Churn logic
        if recency >= 4 and freq >= 4 and mon >= 4:
            segment = "CHAMPIONS"
            churn = False
        elif freq >= 3 and mon >= 3:
            segment = "LOYAL"
            churn = False
        elif recency >= 3 and mon >= 2:
            segment = "POTENTIAL_LOYALIST"
            churn = False
        elif recency <= 2 and freq <= 2:
            segment = "AT_RISK"
            churn = True
        else:
            segment = "HIBERNATING"
            churn = True if recency == 1 else False

        records.append({
            "customer_sk": customer_sk,
            "registration_store_id": reg_store_id,
            "loyalty_tier": tier,
            "rfm_recency_score": recency,
            "rfm_frequency_score": freq,
            "rfm_monetary_score": mon,
            "rfm_segment_name": segment,
            "churn_risk_flag": churn,
            "lifetime_net_spend_inr": lifetime_spend,
        })

    return records
