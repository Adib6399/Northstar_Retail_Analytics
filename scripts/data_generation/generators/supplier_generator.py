"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.2: Supplier Dimension Generator (gold.dim_supplier)

Generates fictional merchandise supplier records conforming to Domain D physical specifications.
All GSTINs are explicitly synthetic test values (prefixed with TESTV).
Supports DEV (10 suppliers) and INTEGRATION (50 suppliers).
"""

from decimal import Decimal
from typing import List, Dict, Any

SUPPLIER_CATALOG = [
    # Top 10 Suppliers for DEV Profile (Merchandise across all 4 divisions)
    {"id": "VND-001", "name": "Apex Electronics Components India Pvt Ltd", "terms": 30, "lead": Decimal("5.50"), "rating": Decimal("0.96"), "state_code": "29"},
    {"id": "VND-002", "name": "Bharat Audio & Vision Systems Ltd", "terms": 45, "lead": Decimal("7.00"), "rating": Decimal("0.92"), "state_code": "27"},
    {"id": "VND-003", "name": "Zenith Apparel & Cotton Mills Ltd", "terms": 30, "lead": Decimal("8.50"), "rating": Decimal("0.90"), "state_code": "33"},
    {"id": "VND-004", "name": "Kaveri Handlooms & Ethnic Wear Corp", "terms": 15, "lead": Decimal("6.00"), "rating": Decimal("0.94"), "state_code": "29"},
    {"id": "VND-005", "name": "Nilgiri Agro Food & Beverage Producers Ltd", "terms": 15, "lead": Decimal("3.00"), "rating": Decimal("0.98"), "state_code": "33"},
    {"id": "VND-006", "name": "Godavari Mills & Packaged Foods Pvt Ltd", "terms": 30, "lead": Decimal("4.50"), "rating": Decimal("0.95"), "state_code": "36"},
    {"id": "VND-007", "name": "Royal Kitchenware & Stainless Steel Industries", "terms": 45, "lead": Decimal("10.00"), "rating": Decimal("0.88"), "state_code": "24"},
    {"id": "VND-008", "name": "Prism Home Decor & Living Solutions Pvt Ltd", "terms": 30, "lead": Decimal("7.50"), "rating": Decimal("0.91"), "state_code": "27"},
    {"id": "VND-009", "name": "Omni Brand Personal Care & FMCG Distributors", "terms": 15, "lead": Decimal("3.50"), "rating": Decimal("0.97"), "state_code": "29"},
    {"id": "VND-010", "name": "Deccan Appliances & Electronics Manufacturing", "terms": 60, "lead": Decimal("12.00"), "rating": Decimal("0.85"), "state_code": "36"},
]

# Generate additional 40 suppliers for INTEGRATION (VND-011 to VND-050)
ADDITIONAL_SUPPLIERS = []
STATE_CODES = ["29", "27", "33", "36", "24"]
SECTORS = ["Electronics", "Textiles", "FMCG", "Home Care", "Beverages", "Appliances", "Apparel", "Kitchenware"]

for i in range(11, 51):
    v_id = f"VND-{i:03d}"
    state_code = STATE_CODES[(i - 1) % len(STATE_CODES)]
    sector = SECTORS[(i - 1) % len(SECTORS)]
    v_name = f"Northstar Allied {sector} Vendor {i} Pvt Ltd"
    terms = 15 if i % 3 == 0 else (45 if i % 4 == 0 else 30)
    lead = Decimal(str(3.0 + (i % 10) * 1.2)).quantize(Decimal("0.01"))
    rating = Decimal(str(0.80 + (i % 20) * 0.01)).quantize(Decimal("0.01"))

    ADDITIONAL_SUPPLIERS.append({
        "id": v_id,
        "name": v_name,
        "terms": terms,
        "lead": lead,
        "rating": rating,
        "state_code": state_code,
    })


def generate_dim_supplier_records(supplier_count: int = 10) -> List[Dict[str, Any]]:
    """
    Generates supplier dimension records.
    DEV: 10 suppliers.
    INTEGRATION: 50 suppliers.
    """
    full_pool = SUPPLIER_CATALOG + ADDITIONAL_SUPPLIERS
    selected = full_pool[:supplier_count]
    records = []

    for s in selected:
        idx_int = int(s["id"].split("-")[1])
        # Synthetic GSTIN format: 2-digit state (2) + TESTV (5) + 4-digit (4) + A (1) + 1Z5 (3) = 15 chars
        # Strictly synthetic and non-real test values
        synthetic_gstin = f"{s['state_code']}TESTV{idx_int:04d}A1Z5"

        records.append({
            "vendor_id": s["id"],
            "vendor_name": s["name"],
            "gstin_number": synthetic_gstin,
            "payment_terms_days": s["terms"],
            "trailing_avg_lead_time_days": s["lead"],
            "vendor_reliability_rating": s["rating"],
        })

    return records
