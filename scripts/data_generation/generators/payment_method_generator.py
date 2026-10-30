"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.2: Payment Method Dimension Generator (gold.dim_payment_method)

Generates the 8 canonical retail tender payment channels conforming to physical specifications.
Satisfies unique constraint (tender_type_code, acquirer_network), VARCHAR(20) limit on tender_type_code,
and MDR fee ranges.
"""

from decimal import Decimal
from typing import List, Dict, Any

PAYMENT_METHODS_CATALOG = [
    {
        "tender_type_code": "CASH",
        "tender_category": "Cash",
        "acquirer_network": "IN_STORE_TILL",
        "contracted_mdr_fee_pct": Decimal("0.0000"),
    },
    {
        "tender_type_code": "UPI_QR",
        "tender_category": "UPI",
        "acquirer_network": "NPCI_BHIM",
        "contracted_mdr_fee_pct": Decimal("0.0000"),
    },
    {
        "tender_type_code": "UPI_AUTOPAY",
        "tender_category": "UPI",
        "acquirer_network": "PAYTM_GATEWAY",
        "contracted_mdr_fee_pct": Decimal("0.0010"),
    },
    {
        "tender_type_code": "CC_VISA",
        "tender_category": "Credit Card",
        "acquirer_network": "HDFC_BANK",
        "contracted_mdr_fee_pct": Decimal("0.0165"),
    },
    {
        "tender_type_code": "CC_MASTERCARD",
        "tender_category": "Credit Card",
        "acquirer_network": "ICICI_BANK",
        "contracted_mdr_fee_pct": Decimal("0.0175"),
    },
    {
        "tender_type_code": "DC_RUPAY",
        "tender_category": "Debit Card",
        "acquirer_network": "SBI_PAYMENTS",
        "contracted_mdr_fee_pct": Decimal("0.0000"),
    },
    {
        "tender_type_code": "DC_VISA",
        "tender_category": "Debit Card",
        "acquirer_network": "AXIS_BANK",
        "contracted_mdr_fee_pct": Decimal("0.0085"),
    },
    {
        "tender_type_code": "GIFT_VOUCHER",
        "tender_category": "Gift Voucher",
        "acquirer_network": "NORTHSTAR_INTERNAL",
        "contracted_mdr_fee_pct": Decimal("0.0000"),
    },
]


def generate_dim_payment_method_records() -> List[Dict[str, Any]]:
    """Generates the 8 canonical payment method records."""
    return [dict(pm) for pm in PAYMENT_METHODS_CATALOG]
