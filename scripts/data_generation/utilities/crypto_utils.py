"""
Northstar Retail Group — Cryptographic Utilities
Provides HMAC-SHA256 pseudonymization and deterministic campaign holdout hashing.
"""

import hashlib
import hmac


def generate_customer_sk(natural_id: str, pepper: str) -> str:
    """
    Generates a deterministic 64-character HMAC-SHA256 hexadecimal digest
    from a synthetic customer identifier and a secret pepper.
    Conforms to FR-014 and gold.dim_customer.customer_sk.
    """
    key_bytes = pepper.encode("utf-8")
    msg_bytes = natural_id.strip().encode("utf-8")
    return hmac.new(key_bytes, msg_bytes, hashlib.sha256).hexdigest()


def calculate_campaign_holdout(campaign_id: str, customer_sk: str, salt: str = "campaign_holdout_salt_v1") -> bool:
    """
    Deterministically assigns a customer to either Treatment (90%) or Control (10%)
    using an HMAC-SHA256 hash modulo 100.
    Returns:
        True: Assigned to Control Group (Metric < 10)
        False: Assigned to Treatment Group (Metric >= 10)
    """
    key_bytes = salt.encode("utf-8")
    msg_bytes = f"{campaign_id}:{customer_sk}".encode("utf-8")
    digest = hmac.new(key_bytes, msg_bytes, hashlib.sha256).hexdigest()
    # Use first 8 hex characters (32 bits) modulo 100
    cohort_metric = int(digest[:8], 16) % 100
    return cohort_metric < 10
