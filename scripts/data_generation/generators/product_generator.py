"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.2: Product Dimension Generator (gold.dim_product)

Generates fictional merchandise SKU records conforming to Domain B physical specifications.
Covers 4 categories: Electronics, Clothing & Apparel, Groceries & FMCG, Home & Kitchen.
Supports DEV (50 SKUs) and INTEGRATION (500 SKUs).
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Any

CATEGORIES = [
    {
        "id": "ELEC",
        "name": "Electronics",
        "subcategories": [
            ("Mobile & Tablets", "8517", Decimal("0.1800"), "A", "EACH"),
            ("Audio & Wearables", "8518", Decimal("0.1800"), "B", "EACH"),
            ("Home Entertainment", "8528", Decimal("0.2800"), "A", "EACH"),
            ("IT Accessories & Cables", "8544", Decimal("0.1800"), "C", "EACH"),
        ],
        "mrp_range": (1500, 45000),
        "margin_range": (Decimal("0.10"), Decimal("0.18")),
    },
    {
        "id": "APPR",
        "name": "Clothing & Apparel",
        "subcategories": [
            ("Mens Casual Wear", "6109", Decimal("0.0500"), "A", "EACH"),
            ("Womens Ethnic Wear", "6204", Decimal("0.1200"), "A", "EACH"),
            ("Kids & Infant Fashion", "6111", Decimal("0.0500"), "B", "EACH"),
            ("Athleisure & Sportswear", "6115", Decimal("0.1200"), "B", "EACH"),
        ],
        "mrp_range": (499, 4999),
        "margin_range": (Decimal("0.40"), Decimal("0.55")),
    },
    {
        "id": "FMCG",
        "name": "Groceries & FMCG",
        "subcategories": [
            ("Staples & Grains", "1006", Decimal("0.0000"), "A", "KG"),
            ("Packaged Foods & Snacks", "1905", Decimal("0.1200"), "A", "PACK"),
            ("Beverages & Juices", "2202", Decimal("0.1200"), "B", "LTR"),
            ("Personal Care & Hygiene", "3401", Decimal("0.1800"), "B", "EACH"),
        ],
        "mrp_range": (40, 850),
        "margin_range": (Decimal("0.08"), Decimal("0.18")),
    },
    {
        "id": "HOME",
        "name": "Home & Kitchen",
        "subcategories": [
            ("Cookware & Stainless Steel", "7323", Decimal("0.1800"), "B", "EACH"),
            ("Small Kitchen Appliances", "8509", Decimal("0.1800"), "A", "EACH"),
            ("Storage & Plastic Containers", "3924", Decimal("0.1800"), "C", "PACK"),
            ("Home Linen & Bedding", "6302", Decimal("0.1200"), "B", "EACH"),
        ],
        "mrp_range": (299, 5999),
        "margin_range": (Decimal("0.28"), Decimal("0.45")),
    },
]


def generate_dim_product_records(
    product_count: int = 50,
    supplier_keys: List[int] = None,
) -> List[Dict[str, Any]]:
    """
    Generates product dimension records.
    product_count: 50 for DEV, 500 for INTEGRATION.
    supplier_keys: List of valid primary_supplier_key IDs from dim_supplier.
    """
    if not supplier_keys:
        supplier_keys = [1]

    records = []
    eff_from = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    eff_to = datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

    for i in range(1, product_count + 1):
        cat_idx = (i - 1) % len(CATEGORIES)
        cat = CATEGORIES[cat_idx]
        subcats = cat["subcategories"]
        subcat_idx = ((i - 1) // len(CATEGORIES)) % len(subcats)
        subcat_name, hsn, gst_rate, abc_class, uom = subcats[subcat_idx]

        sku_id = f"SKU-{cat['id']}-{i:04d}"
        sku_name = f"Northstar {cat['name']} {subcat_name} Item {i:04d}"

        # Deterministic pricing
        min_mrp, max_mrp = cat["mrp_range"]
        mrp_span = max_mrp - min_mrp
        mrp_val = Decimal(str(min_mrp + ((i * 137) % mrp_span))).quantize(Decimal("0.01"))
        if mrp_val <= 0:
            mrp_val = Decimal(str(min_mrp))

        # Margin and standard cost
        min_margin, max_margin = cat["margin_range"]
        margin_pct = min_margin + ((i % 10) / Decimal("100.0"))
        if margin_pct > max_margin:
            margin_pct = max_margin

        cost_val = (mrp_val * (Decimal("1.0000") - margin_pct)).quantize(Decimal("0.0001"))
        if cost_val <= 0:
            cost_val = Decimal("10.0000")

        # Associate to an authentic primary supplier key
        primary_sup_key = supplier_keys[(i - 1) % len(supplier_keys)]

        pack_size = Decimal("1.00") if uom == "EACH" else (Decimal("5.00") if uom == "KG" else Decimal("1.00"))

        records.append({
            "sku_id": sku_id,
            "sku_name": sku_name,
            "category_id": cat["id"],
            "category_name": cat["name"],
            "subcategory_name": subcat_name,
            "hsn_code": hsn,
            "gst_rate_pct": gst_rate,
            "standard_cost_price": cost_val,
            "mrp": mrp_val.quantize(Decimal("0.0001")),
            "pack_size": pack_size,
            "unit_of_measure": uom,
            "abc_velocity_class": abc_class,
            "primary_supplier_key": primary_sup_key,
            "effective_from_timestamp": eff_from,
            "effective_to_timestamp": eff_to,
            "is_current_flag": True,
        })

    return records
