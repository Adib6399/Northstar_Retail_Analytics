-- ============================================================================
-- Migration: 006_create_partitions.sql
-- Description: Creates active child partitions supporting NFR-006 (5-yr historical + future)
-- Platform: PostgreSQL 16
-- Stage: Stage 5.2B.1 Physical DDL Implementation
-- Author: Senior PostgreSQL 16 Database Engineer
-- ============================================================================

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

-- ============================================================================
-- 1. Control Schema: control.control_batch_audit (Annual Partitions 2021-2027)
-- ============================================================================
CREATE TABLE IF NOT EXISTS control.control_batch_audit_y2021 PARTITION OF control.control_batch_audit
    FOR VALUES FROM ('2021-01-01 00:00:00+00') TO ('2022-01-01 00:00:00+00');
CREATE TABLE IF NOT EXISTS control.control_batch_audit_y2022 PARTITION OF control.control_batch_audit
    FOR VALUES FROM ('2022-01-01 00:00:00+00') TO ('2023-01-01 00:00:00+00');
CREATE TABLE IF NOT EXISTS control.control_batch_audit_y2023 PARTITION OF control.control_batch_audit
    FOR VALUES FROM ('2023-01-01 00:00:00+00') TO ('2024-01-01 00:00:00+00');
CREATE TABLE IF NOT EXISTS control.control_batch_audit_y2024 PARTITION OF control.control_batch_audit
    FOR VALUES FROM ('2024-01-01 00:00:00+00') TO ('2025-01-01 00:00:00+00');
CREATE TABLE IF NOT EXISTS control.control_batch_audit_y2025 PARTITION OF control.control_batch_audit
    FOR VALUES FROM ('2025-01-01 00:00:00+00') TO ('2026-01-01 00:00:00+00');
CREATE TABLE IF NOT EXISTS control.control_batch_audit_y2026 PARTITION OF control.control_batch_audit
    FOR VALUES FROM ('2026-01-01 00:00:00+00') TO ('2027-01-01 00:00:00+00');
CREATE TABLE IF NOT EXISTS control.control_batch_audit_y2027 PARTITION OF control.control_batch_audit
    FOR VALUES FROM ('2027-01-01 00:00:00+00') TO ('2028-01-01 00:00:00+00');

-- ============================================================================
-- 2. Gold Schema: Monthly Partitioned Tables
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 2.1 gold.fact_sales (Monthly Partitions 2021 to 2027: 84 partitions)
-- ----------------------------------------------------------------------------
-- Calendar Year 2021
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2021m01 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20210101) TO (20210201);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2021m02 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20210201) TO (20210301);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2021m03 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20210301) TO (20210401);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2021m04 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20210401) TO (20210501);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2021m05 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20210501) TO (20210601);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2021m06 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20210601) TO (20210701);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2021m07 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20210701) TO (20210801);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2021m08 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20210801) TO (20210901);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2021m09 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20210901) TO (20211001);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2021m10 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20211001) TO (20211101);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2021m11 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20211101) TO (20211201);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2021m12 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20211201) TO (20220101);
-- Calendar Year 2022
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2022m01 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20220101) TO (20220201);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2022m02 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20220201) TO (20220301);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2022m03 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20220301) TO (20220401);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2022m04 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20220401) TO (20220501);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2022m05 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20220501) TO (20220601);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2022m06 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20220601) TO (20220701);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2022m07 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20220701) TO (20220801);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2022m08 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20220801) TO (20220901);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2022m09 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20220901) TO (20221001);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2022m10 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20221001) TO (20221101);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2022m11 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20221101) TO (20221201);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2022m12 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20221201) TO (20230101);
-- Calendar Year 2023
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2023m01 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20230101) TO (20230201);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2023m02 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20230201) TO (20230301);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2023m03 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20230301) TO (20230401);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2023m04 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20230401) TO (20230501);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2023m05 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20230501) TO (20230601);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2023m06 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20230601) TO (20230701);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2023m07 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20230701) TO (20230801);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2023m08 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20230801) TO (20230901);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2023m09 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20230901) TO (20231001);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2023m10 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20231001) TO (20231101);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2023m11 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20231101) TO (20231201);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2023m12 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20231201) TO (20240101);
-- Calendar Year 2024
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2024m01 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20240101) TO (20240201);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2024m02 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20240201) TO (20240301);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2024m03 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20240301) TO (20240401);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2024m04 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20240401) TO (20240501);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2024m05 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20240501) TO (20240601);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2024m06 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20240601) TO (20240701);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2024m07 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20240701) TO (20240801);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2024m08 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20240801) TO (20240901);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2024m09 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20240901) TO (20241001);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2024m10 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20241001) TO (20241101);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2024m11 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20241101) TO (20241201);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2024m12 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20241201) TO (20250101);
-- Calendar Year 2025
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2025m01 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20250101) TO (20250201);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2025m02 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20250201) TO (20250301);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2025m03 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20250301) TO (20250401);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2025m04 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20250401) TO (20250501);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2025m05 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20250501) TO (20250601);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2025m06 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20250601) TO (20250701);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2025m07 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20250701) TO (20250801);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2025m08 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20250801) TO (20250901);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2025m09 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20250901) TO (20251001);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2025m10 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20251001) TO (20251101);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2025m11 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20251101) TO (20251201);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2025m12 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20251201) TO (20260101);
-- Calendar Year 2026
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2026m01 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20260101) TO (20260201);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2026m02 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20260201) TO (20260301);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2026m03 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20260301) TO (20260401);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2026m04 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20260401) TO (20260501);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2026m05 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20260501) TO (20260601);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2026m06 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20260601) TO (20260701);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2026m07 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20260701) TO (20260801);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2026m08 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20260801) TO (20260901);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2026m09 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20260901) TO (20261001);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2026m10 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20261001) TO (20261101);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2026m11 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20261101) TO (20261201);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2026m12 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20261201) TO (20270101);
-- Calendar Year 2027
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2027m01 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20270101) TO (20270201);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2027m02 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20270201) TO (20270301);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2027m03 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20270301) TO (20270401);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2027m04 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20270401) TO (20270501);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2027m05 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20270501) TO (20270601);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2027m06 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20270601) TO (20270701);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2027m07 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20270701) TO (20270801);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2027m08 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20270801) TO (20270901);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2027m09 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20270901) TO (20271001);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2027m10 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20271001) TO (20271101);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2027m11 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20271101) TO (20271201);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2027m12 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20271201) TO (20280101);

-- ----------------------------------------------------------------------------
-- 2.2 gold.fact_inventory_snapshot (Monthly Partitions 2021 to 2027: 84 partitions)
-- ----------------------------------------------------------------------------
-- Calendar Year 2021
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2021m01 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20210101) TO (20210201);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2021m02 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20210201) TO (20210301);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2021m03 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20210301) TO (20210401);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2021m04 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20210401) TO (20210501);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2021m05 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20210501) TO (20210601);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2021m06 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20210601) TO (20210701);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2021m07 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20210701) TO (20210801);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2021m08 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20210801) TO (20210901);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2021m09 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20210901) TO (20211001);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2021m10 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20211001) TO (20211101);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2021m11 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20211101) TO (20211201);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2021m12 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20211201) TO (20220101);
-- Calendar Year 2022
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2022m01 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20220101) TO (20220201);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2022m02 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20220201) TO (20220301);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2022m03 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20220301) TO (20220401);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2022m04 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20220401) TO (20220501);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2022m05 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20220501) TO (20220601);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2022m06 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20220601) TO (20220701);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2022m07 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20220701) TO (20220801);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2022m08 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20220801) TO (20220901);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2022m09 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20220901) TO (20221001);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2022m10 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20221001) TO (20221101);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2022m11 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20221101) TO (20221201);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2022m12 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20221201) TO (20230101);
-- Calendar Year 2023
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2023m01 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20230101) TO (20230201);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2023m02 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20230201) TO (20230301);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2023m03 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20230301) TO (20230401);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2023m04 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20230401) TO (20230501);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2023m05 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20230501) TO (20230601);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2023m06 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20230601) TO (20230701);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2023m07 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20230701) TO (20230801);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2023m08 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20230801) TO (20230901);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2023m09 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20230901) TO (20231001);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2023m10 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20231001) TO (20231101);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2023m11 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20231101) TO (20231201);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2023m12 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20231201) TO (20240101);
-- Calendar Year 2024
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2024m01 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20240101) TO (20240201);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2024m02 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20240201) TO (20240301);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2024m03 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20240301) TO (20240401);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2024m04 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20240401) TO (20240501);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2024m05 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20240501) TO (20240601);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2024m06 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20240601) TO (20240701);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2024m07 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20240701) TO (20240801);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2024m08 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20240801) TO (20240901);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2024m09 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20240901) TO (20241001);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2024m10 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20241001) TO (20241101);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2024m11 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20241101) TO (20241201);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2024m12 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20241201) TO (20250101);
-- Calendar Year 2025
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2025m01 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20250101) TO (20250201);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2025m02 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20250201) TO (20250301);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2025m03 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20250301) TO (20250401);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2025m04 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20250401) TO (20250501);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2025m05 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20250501) TO (20250601);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2025m06 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20250601) TO (20250701);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2025m07 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20250701) TO (20250801);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2025m08 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20250801) TO (20250901);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2025m09 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20250901) TO (20251001);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2025m10 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20251001) TO (20251101);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2025m11 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20251101) TO (20251201);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2025m12 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20251201) TO (20260101);
-- Calendar Year 2026
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2026m01 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20260101) TO (20260201);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2026m02 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20260201) TO (20260301);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2026m03 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20260301) TO (20260401);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2026m04 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20260401) TO (20260501);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2026m05 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20260501) TO (20260601);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2026m06 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20260601) TO (20260701);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2026m07 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20260701) TO (20260801);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2026m08 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20260801) TO (20260901);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2026m09 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20260901) TO (20261001);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2026m10 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20261001) TO (20261101);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2026m11 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20261101) TO (20261201);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2026m12 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20261201) TO (20270101);
-- Calendar Year 2027
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2027m01 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20270101) TO (20270201);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2027m02 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20270201) TO (20270301);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2027m03 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20270301) TO (20270401);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2027m04 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20270401) TO (20270501);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2027m05 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20270501) TO (20270601);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2027m06 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20270601) TO (20270701);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2027m07 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20270701) TO (20270801);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2027m08 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20270801) TO (20270901);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2027m09 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20270901) TO (20271001);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2027m10 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20271001) TO (20271101);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2027m11 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20271101) TO (20271201);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2027m12 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20271201) TO (20280101);

-- ----------------------------------------------------------------------------
-- 2.3 gold.fact_demand_forecast (Forward-Looking Monthly Horizon: 6 partitions)
-- Note: Forward-looking T+1 to T+14 operational forecast window per FR-024.
-- Historical forecasts are intentionally omitted (no artificial back-fill).
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_demand_forecast_y2026m10 PARTITION OF gold.fact_demand_forecast
    FOR VALUES FROM (20261001) TO (20261101);
CREATE TABLE IF NOT EXISTS gold.fact_demand_forecast_y2026m11 PARTITION OF gold.fact_demand_forecast
    FOR VALUES FROM (20261101) TO (20261201);
CREATE TABLE IF NOT EXISTS gold.fact_demand_forecast_y2026m12 PARTITION OF gold.fact_demand_forecast
    FOR VALUES FROM (20261201) TO (20270101);
CREATE TABLE IF NOT EXISTS gold.fact_demand_forecast_y2027m01 PARTITION OF gold.fact_demand_forecast
    FOR VALUES FROM (20270101) TO (20270201);
CREATE TABLE IF NOT EXISTS gold.fact_demand_forecast_y2027m02 PARTITION OF gold.fact_demand_forecast
    FOR VALUES FROM (20270201) TO (20270301);
CREATE TABLE IF NOT EXISTS gold.fact_demand_forecast_y2027m03 PARTITION OF gold.fact_demand_forecast
    FOR VALUES FROM (20270301) TO (20270401);

-- ============================================================================
-- 3. Gold Schema: Annual Partitioned Tables (2021 to 2027: 7 partitions each)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 3.1 gold.fact_payments
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_payments_y2021 PARTITION OF gold.fact_payments
    FOR VALUES FROM (20210101) TO (20220101);
CREATE TABLE IF NOT EXISTS gold.fact_payments_y2022 PARTITION OF gold.fact_payments
    FOR VALUES FROM (20220101) TO (20230101);
CREATE TABLE IF NOT EXISTS gold.fact_payments_y2023 PARTITION OF gold.fact_payments
    FOR VALUES FROM (20230101) TO (20240101);
CREATE TABLE IF NOT EXISTS gold.fact_payments_y2024 PARTITION OF gold.fact_payments
    FOR VALUES FROM (20240101) TO (20250101);
CREATE TABLE IF NOT EXISTS gold.fact_payments_y2025 PARTITION OF gold.fact_payments
    FOR VALUES FROM (20250101) TO (20260101);
CREATE TABLE IF NOT EXISTS gold.fact_payments_y2026 PARTITION OF gold.fact_payments
    FOR VALUES FROM (20260101) TO (20270101);
CREATE TABLE IF NOT EXISTS gold.fact_payments_y2027 PARTITION OF gold.fact_payments
    FOR VALUES FROM (20270101) TO (20280101);

-- ----------------------------------------------------------------------------
-- 3.2 gold.fact_returns
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_returns_y2021 PARTITION OF gold.fact_returns
    FOR VALUES FROM (20210101) TO (20220101);
CREATE TABLE IF NOT EXISTS gold.fact_returns_y2022 PARTITION OF gold.fact_returns
    FOR VALUES FROM (20220101) TO (20230101);
CREATE TABLE IF NOT EXISTS gold.fact_returns_y2023 PARTITION OF gold.fact_returns
    FOR VALUES FROM (20230101) TO (20240101);
CREATE TABLE IF NOT EXISTS gold.fact_returns_y2024 PARTITION OF gold.fact_returns
    FOR VALUES FROM (20240101) TO (20250101);
CREATE TABLE IF NOT EXISTS gold.fact_returns_y2025 PARTITION OF gold.fact_returns
    FOR VALUES FROM (20250101) TO (20260101);
CREATE TABLE IF NOT EXISTS gold.fact_returns_y2026 PARTITION OF gold.fact_returns
    FOR VALUES FROM (20260101) TO (20270101);
CREATE TABLE IF NOT EXISTS gold.fact_returns_y2027 PARTITION OF gold.fact_returns
    FOR VALUES FROM (20270101) TO (20280101);

-- ----------------------------------------------------------------------------
-- 3.3 gold.fact_inventory_movements
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_inventory_movements_y2021 PARTITION OF gold.fact_inventory_movements
    FOR VALUES FROM (20210101) TO (20220101);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_movements_y2022 PARTITION OF gold.fact_inventory_movements
    FOR VALUES FROM (20220101) TO (20230101);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_movements_y2023 PARTITION OF gold.fact_inventory_movements
    FOR VALUES FROM (20230101) TO (20240101);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_movements_y2024 PARTITION OF gold.fact_inventory_movements
    FOR VALUES FROM (20240101) TO (20250101);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_movements_y2025 PARTITION OF gold.fact_inventory_movements
    FOR VALUES FROM (20250101) TO (20260101);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_movements_y2026 PARTITION OF gold.fact_inventory_movements
    FOR VALUES FROM (20260101) TO (20270101);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_movements_y2027 PARTITION OF gold.fact_inventory_movements
    FOR VALUES FROM (20270101) TO (20280101);

-- ----------------------------------------------------------------------------
-- 3.4 gold.fact_reconciliation
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_reconciliation_y2021 PARTITION OF gold.fact_reconciliation
    FOR VALUES FROM (20210101) TO (20220101);
CREATE TABLE IF NOT EXISTS gold.fact_reconciliation_y2022 PARTITION OF gold.fact_reconciliation
    FOR VALUES FROM (20220101) TO (20230101);
CREATE TABLE IF NOT EXISTS gold.fact_reconciliation_y2023 PARTITION OF gold.fact_reconciliation
    FOR VALUES FROM (20230101) TO (20240101);
CREATE TABLE IF NOT EXISTS gold.fact_reconciliation_y2024 PARTITION OF gold.fact_reconciliation
    FOR VALUES FROM (20240101) TO (20250101);
CREATE TABLE IF NOT EXISTS gold.fact_reconciliation_y2025 PARTITION OF gold.fact_reconciliation
    FOR VALUES FROM (20250101) TO (20260101);
CREATE TABLE IF NOT EXISTS gold.fact_reconciliation_y2026 PARTITION OF gold.fact_reconciliation
    FOR VALUES FROM (20260101) TO (20270101);
CREATE TABLE IF NOT EXISTS gold.fact_reconciliation_y2027 PARTITION OF gold.fact_reconciliation
    FOR VALUES FROM (20270101) TO (20280101);

-- ----------------------------------------------------------------------------
-- 3.5 gold.fact_marketing_performance
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_marketing_performance_y2021 PARTITION OF gold.fact_marketing_performance
    FOR VALUES FROM (20210101) TO (20220101);
CREATE TABLE IF NOT EXISTS gold.fact_marketing_performance_y2022 PARTITION OF gold.fact_marketing_performance
    FOR VALUES FROM (20220101) TO (20230101);
CREATE TABLE IF NOT EXISTS gold.fact_marketing_performance_y2023 PARTITION OF gold.fact_marketing_performance
    FOR VALUES FROM (20230101) TO (20240101);
CREATE TABLE IF NOT EXISTS gold.fact_marketing_performance_y2024 PARTITION OF gold.fact_marketing_performance
    FOR VALUES FROM (20240101) TO (20250101);
CREATE TABLE IF NOT EXISTS gold.fact_marketing_performance_y2025 PARTITION OF gold.fact_marketing_performance
    FOR VALUES FROM (20250101) TO (20260101);
CREATE TABLE IF NOT EXISTS gold.fact_marketing_performance_y2026 PARTITION OF gold.fact_marketing_performance
    FOR VALUES FROM (20260101) TO (20270101);
CREATE TABLE IF NOT EXISTS gold.fact_marketing_performance_y2027 PARTITION OF gold.fact_marketing_performance
    FOR VALUES FROM (20270101) TO (20280101);

-- ----------------------------------------------------------------------------
-- 3.6 gold.fact_campaign_exposure
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_campaign_exposure_y2021 PARTITION OF gold.fact_campaign_exposure
    FOR VALUES FROM (20210101) TO (20220101);
CREATE TABLE IF NOT EXISTS gold.fact_campaign_exposure_y2022 PARTITION OF gold.fact_campaign_exposure
    FOR VALUES FROM (20220101) TO (20230101);
CREATE TABLE IF NOT EXISTS gold.fact_campaign_exposure_y2023 PARTITION OF gold.fact_campaign_exposure
    FOR VALUES FROM (20230101) TO (20240101);
CREATE TABLE IF NOT EXISTS gold.fact_campaign_exposure_y2024 PARTITION OF gold.fact_campaign_exposure
    FOR VALUES FROM (20240101) TO (20250101);
CREATE TABLE IF NOT EXISTS gold.fact_campaign_exposure_y2025 PARTITION OF gold.fact_campaign_exposure
    FOR VALUES FROM (20250101) TO (20260101);
CREATE TABLE IF NOT EXISTS gold.fact_campaign_exposure_y2026 PARTITION OF gold.fact_campaign_exposure
    FOR VALUES FROM (20260101) TO (20270101);
CREATE TABLE IF NOT EXISTS gold.fact_campaign_exposure_y2027 PARTITION OF gold.fact_campaign_exposure
    FOR VALUES FROM (20270101) TO (20280101);

-- ============================================================================
-- 4. Future Partition Maintenance Automation Strategy
-- ============================================================================
-- In production, a scheduled cron task or Airflow maintenance DAG will execute 
-- automated partition pre-creation 30 days prior to the beginning of each 
-- calendar month / year, guaranteeing continuous partition availability 
-- without manual administrative intervention.
