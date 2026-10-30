"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.2: Campaign Dimension Generator (gold.dim_campaign)

Generates fictional marketing campaign records conforming to physical specifications.
Satisfies communication channel check constraints, date range constraints, and unique campaign_id.
Supports DEV (2 campaigns) and INTEGRATION (5 campaigns).
"""

from datetime import date
from decimal import Decimal
from typing import List, Dict, Any

CANONICAL_CAMPAIGNS = [
    # DEV Campaigns (2)
    {
        "campaign_id": "CMP-2026-DIWALI",
        "campaign_name": "Diwali Festive Megasale Omnichannel Campaign",
        "communication_channel": "OMNICHANNEL",
        "start_date": date(2026, 10, 15),
        "end_date": date(2026, 11, 15),
        "total_budget_inr": Decimal("5000000.00"),
        "target_category_name": "Clothing & Apparel",
    },
    {
        "campaign_id": "CMP-2026-LOYALTY",
        "campaign_name": "Q4 Loyalty Tier Retention WhatsApp Blast",
        "communication_channel": "WHATSAPP",
        "start_date": date(2026, 10, 1),
        "end_date": date(2026, 10, 31),
        "total_budget_inr": Decimal("1500000.00"),
        "target_category_name": "Electronics",
    },
    # INTEGRATION Campaigns (3 more)
    {
        "campaign_id": "CMP-2026-FRESH",
        "campaign_name": "Weekend Grocery FMCG Flash SMS Campaign",
        "communication_channel": "SMS",
        "start_date": date(2026, 8, 1),
        "end_date": date(2026, 9, 30),
        "total_budget_inr": Decimal("850000.00"),
        "target_category_name": "Groceries & FMCG",
    },
    {
        "campaign_id": "CMP-2026-HOMEFEST",
        "campaign_name": "Monsoon Home & Kitchen Clearance Email Outreach",
        "communication_channel": "EMAIL",
        "start_date": date(2026, 8, 15),
        "end_date": date(2026, 9, 15),
        "total_budget_inr": Decimal("650000.00"),
        "target_category_name": "Home & Kitchen",
    },
    {
        "campaign_id": "CMP-2026-PREMIUM",
        "campaign_name": "Platinum Members Private Showcase Preview",
        "communication_channel": "OMNICHANNEL",
        "start_date": date(2026, 10, 20),
        "end_date": date(2026, 10, 31),
        "total_budget_inr": Decimal("2200000.00"),
        "target_category_name": "Electronics",
    },
]


def generate_dim_campaign_records(campaign_count: int = 2) -> List[Dict[str, Any]]:
    """
    Generates campaign dimension records.
    DEV: 2 campaigns.
    INTEGRATION: 5 campaigns.
    """
    return [dict(c) for c in CANONICAL_CAMPAIGNS[:campaign_count]]
