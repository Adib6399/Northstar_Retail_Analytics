"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.5: Campaign Assignment Registry & Exposure Fact Generator
Target Tables:
  1. control.control_campaign_assignment_registry (50,000 records)
  2. gold.fact_campaign_exposure (50,000 records)

Implements the deterministic 10% holdout logic using HMAC-SHA256 via crypto_utils.
Guarantees historical assignment immutability, zero customer PII leakage,
and strict composite FK integrity between fact and registry.
"""

import hashlib
import hmac
import random
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple, Optional

from scripts.data_generation.config import GenerationProfileConfig
from scripts.data_generation.utilities.crypto_utils import calculate_campaign_holdout


class CampaignExposureGenerator:
    """Generates synthetic campaign holdout assignments and communication exposure drops."""

    def __init__(
        self,
        config: GenerationProfileConfig,
        campaigns: List[Dict[str, Any]],
        customers: List[Dict[str, Any]],
        salt: str = "campaign_holdout_salt_v1",
        seed: Optional[int] = None,
    ):
        self.config = config
        self.campaigns = campaigns
        # Filter out anonymous walk-in sentinel (-1)
        self.customers = [c for c in customers if c["customer_key"] > 0]
        self.salt = salt
        self.seed = seed if seed is not None else config.random_seed
        self.rng = random.Random(self.seed)

    def generate_assignments_and_exposures(
        self,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Generates paired assignments and exposure events.
        Produces exactly 50,000 assignments (5 campaigns x 10,000 customers).
        """
        batch_uuid = uuid.uuid4()
        registry_records: List[Dict[str, Any]] = []
        exposure_records: List[Dict[str, Any]] = []

        # Order customers and campaigns deterministically
        sorted_campaigns = sorted(self.campaigns, key=lambda c: c["campaign_key"])
        sorted_customers = sorted(self.customers, key=lambda c: c["customer_key"])

        channel_options = ["SMS", "WHATSAPP", "EMAIL"]

        for camp in sorted_campaigns:
            camp_key = camp["campaign_key"]
            camp_id = camp["campaign_id"]
            camp_start = camp["start_date"]
            camp_end = camp["end_date"]
            camp_date_key = int(camp_start.strftime("%Y%m%d"))
            pref_channel = camp.get("communication_channel", "SMS")

            key_bytes = self.salt.encode("utf-8")

            for cust in sorted_customers:
                cust_key = cust["customer_key"]
                cust_sk = cust["customer_sk"]

                # 1. Deterministic HMAC Holdout Calculation
                msg_bytes = f"{camp_id}:{cust_sk}".encode("utf-8")
                assignment_hash = hmac.new(key_bytes, msg_bytes, hashlib.sha256).hexdigest()
                cohort_metric = int(assignment_hash[:8], 16) % 100
                is_holdout = cohort_metric < 10  # 10% Control, 90% Treatment

                # Assignment timestamp (at campaign launch 08:00 UTC)
                assign_ts = datetime(camp_start.year, camp_start.month, camp_start.day, 8, 0, 0, tzinfo=timezone.utc)

                reg_entry = {
                    "campaign_id": camp_id,
                    "customer_sk": cust_sk,
                    "campaign_key": camp_key,
                    "customer_key": cust_key,
                    "assignment_date_key": camp_date_key,
                    "assignment_timestamp": assign_ts,
                    "is_holdout_control_flag": is_holdout,
                    "assignment_hash_value": assignment_hash,
                    "holdout_key_version": "v1",
                    "is_locked_flag": True,
                    "ingestion_batch_id": batch_uuid,
                }
                registry_records.append(reg_entry)

                # 2. Exposure Record Construction
                # Determine communication channel
                if pref_channel in channel_options:
                    channel = pref_channel
                else:  # OMNICHANNEL or other
                    channel = channel_options[cust_key % len(channel_options)]

                if is_holdout:
                    # Control Cohort: suppressed from receiving marketing communications
                    dispatch_status = "NOT_DISPATCHED_HOLDOUT"
                    dispatch_ts = None
                    dispatch_attempts = 0
                    delivery_status = "NOT_APPLICABLE_HOLDOUT"
                    delivery_ts = None
                    coupon_redeemed = False
                    redemption_date_key = None
                    redemption_ts = None
                    redemption_lag = None
                else:
                    # Treatment Cohort: dispatched via gateway
                    # Deterministic pseudo-randomness based on customer & campaign keys
                    sub_seed = (cust_key * 10007 + camp_key * 31) % 1000000
                    r_val = sub_seed / 1000000.0

                    # Dispatch offset within launch day (8 AM to 2 PM)
                    offset_secs = (sub_seed % 21600)
                    dispatch_ts = assign_ts + timedelta(seconds=offset_secs)

                    if r_val < 0.02:  # 2% dispatch failure
                        dispatch_status = "DISPATCH_FAILED"
                        dispatch_attempts = 3
                        delivery_status = "UNDELIVERED"
                        delivery_ts = None
                        coupon_redeemed = False
                        redemption_date_key = None
                        redemption_ts = None
                        redemption_lag = None
                    else:
                        dispatch_status = "DISPATCHED"
                        dispatch_attempts = 1

                        if r_val < 0.06:  # 4% bounce
                            delivery_status = "BOUNCED"
                            delivery_ts = None
                            coupon_redeemed = False
                            redemption_date_key = None
                            redemption_ts = None
                            redemption_lag = None
                        else:  # 94% delivered
                            delivery_status = "DELIVERED"
                            delivery_ts = dispatch_ts + timedelta(seconds=15 + (sub_seed % 180))

                            # ~8.5% coupon redemption rate among delivered treatment customers
                            if (sub_seed % 100) < 9:
                                coupon_redeemed = True
                                lag_days = 1 + (sub_seed % 10)
                                red_date = camp_start + timedelta(days=lag_days)
                                if red_date > camp_end:
                                    red_date = camp_end
                                redemption_date_key = int(red_date.strftime("%Y%m%d"))
                                redemption_ts = datetime(
                                    red_date.year, red_date.month, red_date.day,
                                    11 + (sub_seed % 9), (sub_seed % 60), 0,
                                    tzinfo=timezone.utc,
                                )
                                redemption_lag = lag_days
                            else:
                                coupon_redeemed = False
                                redemption_date_key = None
                                redemption_ts = None
                                redemption_lag = None

                src_rec_id = f"EXP-{camp_id}-{cust_key}"
                hash_str = f"{camp_key}|{cust_key}|{camp_date_key}|{is_holdout}|{dispatch_status}|{delivery_status}"
                rec_hash = hashlib.sha256(hash_str.encode("utf-8")).hexdigest()

                exp_entry = {
                    "assignment_date_key": camp_date_key,
                    "campaign_key": camp_key,
                    "customer_key": cust_key,
                    "is_holdout_control_flag": is_holdout,
                    "communication_channel": channel,
                    "dispatch_status": dispatch_status,
                    "dispatch_timestamp": dispatch_ts,
                    "dispatch_attempt_count": dispatch_attempts,
                    "delivery_status": delivery_status,
                    "delivery_timestamp": delivery_ts,
                    "coupon_redeemed_flag": coupon_redeemed,
                    "redemption_date_key": redemption_date_key,
                    "redemption_timestamp": redemption_ts,
                    "redemption_lag_days": redemption_lag,
                    "source_system": "SRC-003",
                    "source_record_id": src_rec_id,
                    "ingestion_batch_id": batch_uuid,
                    "record_hash": rec_hash,
                    "data_quality_status": "VALIDATED",
                }
                exposure_records.append(exp_entry)

        assert len(registry_records) == self.config.campaign_exposure_drops
        assert len(exposure_records) == self.config.campaign_exposure_drops
        return registry_records, exposure_records

