"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.4: Inventory Generator (Snapshots & Material Movements)

Generates:
1. Daily periodic inventory snapshots (gold.fact_inventory_snapshot):
   30 stores x 500 SKUs x 92 days = exactly 1,380,000 snapshot records.
2. ERP material movements ledger (gold.fact_inventory_movements):
   1,000 movements/day x 92 days = exactly 92,000 movement records adhering strictly
   to approved reference types (101, 251, 252, 451, 301).
"""

import hashlib
import random
import uuid
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional

from scripts.data_generation.config import GenerationProfileConfig


class InventoryGenerator:
    """Generates inventory snapshots and ERP material movements."""

    def __init__(
        self,
        config: GenerationProfileConfig,
        stores: List[Dict[str, Any]],
        products: List[Dict[str, Any]],
        movement_types: List[Dict[str, Any]],
        seed: Optional[int] = None,
    ):
        self.config = config
        self.stores = stores[:config.store_count]
        self.products = products[:config.product_count]
        self.movement_types = movement_types
        self.seed = seed if seed is not None else config.random_seed
        self.rng = random.Random(self.seed)

        # Movement type key lookup by code
        # Approved codes: 101, 251, 252, 451, 301
        self.mtype_map: Dict[str, Dict[str, Any]] = {
            m["movement_code"]: m for m in self.movement_types
        }

    def generate_day_movements(self, target_date: date) -> List[Dict[str, Any]]:
        """
        Generates exactly 1,000 material movement records for target_date.
        Distribution:
          - 550 x 251 (POS sales decrement, -1)
          - 250 x 101 (Vendor goods receipt, +1)
          - 100 x 301 (Store transfer outflow, -1, with destination_store_key)
          -  75 x 451 (Returns quarantine receipt, +1)
          -  25 x 252 (Sales reversal / exchange, +1)
          Total: Exactly 1,000 movements / day.
        """
        date_key = int(target_date.strftime("%Y%m%d"))
        batch_uuid = uuid.uuid4()
        movements: List[Dict[str, Any]] = []

        # Breakdown matching exactly 1,000 records
        quotas = [
            ("251", 550),
            ("101", 250),
            ("301", 100),
            ("451", 75),
            ("252", 25),
        ]

        doc_counter = 0

        for m_code, count in quotas:
            m_info = self.mtype_map.get(m_code, self.movement_types[0])
            mtype_key = m_info["movement_type_key"]
            impact_direction = m_info.get("stock_impact_direction", 1)

            for _ in range(count):
                doc_counter += 1
                store = self.rng.choice(self.stores)
                src_store_key = store["store_key"]

                # Destination store for transfers (code 301)
                dst_store_key = None
                if m_code == "301":
                    other_stores = [s for s in self.stores if s["store_key"] != src_store_key]
                    dst_store = self.rng.choice(other_stores)
                    dst_store_key = dst_store["store_key"]

                product = self.rng.choice(self.products)
                prod_key = product["product_key"]
                unit_cost = Decimal(str(product["standard_cost_price"]))

                # Plausible quantities by movement type
                if m_code == "251":
                    raw_units = Decimal(str(self.rng.randint(1, 8)))
                elif m_code == "101":
                    raw_units = Decimal(str(self.rng.randint(20, 100)))
                elif m_code == "301":
                    raw_units = Decimal(str(self.rng.randint(5, 25)))
                elif m_code == "451":
                    raw_units = Decimal(str(self.rng.randint(1, 3)))
                else:  # 252
                    raw_units = Decimal(str(self.rng.randint(1, 2)))

                # Apply sign based on stock impact direction (-1 for outflow, +1 for inflow)
                units = raw_units if impact_direction == 1 else -raw_units
                valuation_amt = (units * unit_cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                erp_doc_id = f"MATDOC-{date_key}-{doc_counter:06d}"
                source_rec_id = f"{erp_doc_id}-L01"

                hash_str = f"{erp_doc_id}|1|{date_key}|{src_store_key}|{prod_key}|{units}|{valuation_amt}"
                rec_hash = hashlib.sha256(hash_str.encode("utf-8")).hexdigest()

                movements.append({
                    "date_key": date_key,
                    "source_store_key": src_store_key,
                    "destination_store_key": dst_store_key,
                    "product_key": prod_key,
                    "movement_type_key": mtype_key,
                    "erp_material_document_id": erp_doc_id,
                    "material_doc_line_number": 1,
                    "movement_units": units,
                    "unit_valuation_cost": unit_cost,
                    "movement_valuation_amount": valuation_amt,
                    "source_system": "SAP_S4HANA_ERP",
                    "source_record_id": source_rec_id,
                    "ingestion_batch_id": batch_uuid,
                    "record_hash": rec_hash,
                    "data_quality_status": "VALIDATED",
                })

        assert len(movements) == 1000
        return movements

    def generate_day_snapshots(self, target_date: date) -> List[Dict[str, Any]]:
        """
        Generates daily inventory snapshots for target_date.
        Coverage: Exactly 30 stores x 500 SKUs = 15,000 records.
        Preserves saleable, blocked, in-transit stock distinctions and valuation math.
        """
        date_key = int(target_date.strftime("%Y%m%d"))
        batch_uuid = uuid.uuid4()
        snapshots: List[Dict[str, Any]] = []

        for store in self.stores:
            s_key = store["store_key"]
            s_id = store["store_id"]

            for prod in self.products:
                p_key = prod["product_key"]
                sku_id = prod["sku_id"]
                cat_id = prod.get("category_id", "FMCG")
                unit_cost = Decimal(str(prod["standard_cost_price"]))

                # Stockout chance (~2%)
                is_stockout = self.rng.random() < 0.02

                if is_stockout:
                    stock_on_hand = Decimal("0.000")
                else:
                    # Category-appropriate stock levels
                    if cat_id == "FMCG":
                        stock_on_hand = Decimal(str(self.rng.randint(40, 200)))
                    elif cat_id == "APPR":
                        stock_on_hand = Decimal(str(self.rng.randint(15, 60)))
                    elif cat_id == "HOME":
                        stock_on_hand = Decimal(str(self.rng.randint(10, 40)))
                    else:  # ELEC
                        stock_on_hand = Decimal(str(self.rng.randint(5, 25)))

                # Blocked quarantine units (occasional customer return, 0-4 units)
                blocked_units = Decimal(str(self.rng.randint(0, 4))) if self.rng.random() < 0.25 else Decimal("0.000")

                # In-transit replenishment units (0-15 units)
                in_transit = Decimal(str(self.rng.randint(5, 25))) if self.rng.random() < 0.20 else Decimal("0.000")

                total_units = stock_on_hand + blocked_units + in_transit
                valuation_amt = (total_units * unit_cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                # Trailing 14-day velocity & days of forward inventory
                velocity = Decimal(str(self.rng.randint(5, 50)))
                daily_burn = velocity / Decimal("14.0")
                if daily_burn > Decimal("0.0") and stock_on_hand > Decimal("0.0"):
                    doi = (stock_on_hand / daily_burn).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
                else:
                    doi = Decimal("0.0") if stock_on_hand == Decimal("0.0") else Decimal("99.0")

                source_rec_id = f"SNAP-{s_id}-{date_key}-{sku_id}"
                hash_str = f"{s_key}|{p_key}|{date_key}|{stock_on_hand}|{blocked_units}|{in_transit}|{valuation_amt}"
                rec_hash = hashlib.sha256(hash_str.encode("utf-8")).hexdigest()

                snapshots.append({
                    "date_key": date_key,
                    "store_key": s_key,
                    "product_key": p_key,
                    "stock_on_hand_units": stock_on_hand,
                    "blocked_damaged_units": blocked_units,
                    "in_transit_units": in_transit,
                    "total_inventory_units": total_units,
                    "unit_cost_price": unit_cost,
                    "inventory_valuation_cost_amount": valuation_amt,
                    "trailing_14d_sales_velocity_units": velocity,
                    "days_of_inventory_forward": doi,
                    "stockout_flag": is_stockout,
                    "source_system": "SAP_S4HANA_ERP",
                    "source_record_id": source_rec_id,
                    "ingestion_batch_id": batch_uuid,
                    "record_hash": rec_hash,
                    "data_quality_status": "VALIDATED",
                })

        expected_day_snapshots = len(self.stores) * len(self.products)
        assert len(snapshots) == expected_day_snapshots
        return snapshots

