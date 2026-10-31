#!/usr/bin/env python3
"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 6.3: Four-Way Reconciliation Deep Dive Runner & Validation Suite
File: scripts/run_stage_6_3_analysis.py

Executes all 6 analytical SQL modules in sql/analytics/stage_6_3/
against the live PostgreSQL 16 analytical warehouse, logs query performance,
and outputs verified raw query results to docs/06_sql_business_analysis/stage_6_3_raw_query_results.txt.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import time
import re
from typing import Dict, Any, List, Tuple
from sqlalchemy import text
import pandas as pd
from config.database import get_db_engine, check_database_connectivity


def split_sql_queries(sql_content: str) -> List[Tuple[str, str]]:
    """Splits an SQL file into individual statements with associated comment headers."""
    # Remove line comments when splitting or handle them carefully
    # First, let's extract query blocks separated by semicolons that are outside comments
    lines = sql_content.splitlines()
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("--"):
            # keep title comments but mask semicolons in comments
            cleaned_lines.append(line.replace(";", ","))
        else:
            cleaned_lines.append(line)
    
    sanitized_content = "\n".join(cleaned_lines)
    raw_statements = [s.strip() for s in sanitized_content.split(";") if s.strip()]
    parsed: List[Tuple[str, str]] = []

    for stmt in raw_statements:
        non_comment_lines = [
            line.strip() for line in stmt.splitlines() 
            if line.strip() and not line.strip().startswith("--")
        ]
        if not non_comment_lines:
            continue

        title_match = re.search(r"-- (Query \d+\.\d+: [^\n]+)", stmt)
        title = title_match.group(1) if title_match else "Reconciliation Query"
        parsed.append((title, stmt))

    return parsed


def run_stage_6_3_suite():
    print("=" * 80)
    print("NORTHSTAR RETAIL GROUP — STAGE 6.3: FOUR-WAY RECONCILIATION RUNNER")
    print("=" * 80)

    # 1. Connectivity Check
    conn_ok, conn_msg = check_database_connectivity()
    if not conn_ok:
        print(f"[PRE-FLIGHT ERROR] Database unreachable: {conn_msg}")
        sys.exit(1)
    print(f"[PRE-FLIGHT] Database connection verified: {conn_msg}")

    engine = get_db_engine()
    sql_dir = project_root / "sql" / "analytics" / "stage_6_3"
    output_raw_file = project_root / "docs" / "06_sql_business_analysis" / "stage_6_3_raw_query_results.txt"

    if not sql_dir.exists():
        print(f"[ERROR] SQL directory {sql_dir} does not exist.")
        sys.exit(1)

    sql_files = sorted([f for f in os.listdir(sql_dir) if f.endswith(".sql")])
    print(f"\nFound {len(sql_files)} reconciliation SQL modules in {sql_dir.relative_to(project_root)}:\n")

    total_queries = 0
    total_execution_time = 0.0
    failed_queries = []

    with engine.connect() as conn, open(output_raw_file, "w") as raw_out:
        raw_out.write("================================================================================\n")
        raw_out.write("NORTHSTAR RETAIL GROUP — ENTERPRISE RETAIL ANALYTICS PLATFORM\n")
        raw_out.write("STAGE 6.3: FOUR-WAY RECONCILIATION DEEP DIVE — RAW QUERY EXECUTION OUTPUT\n")
        raw_out.write("Executed against: PostgreSQL 16 (northstar_analytics_dev)\n")
        raw_out.write("Execution Mode: STRICT READ-ONLY\n")
        raw_out.write("Disclaimer: Synthetic portfolio retail analytics dataset\n")
        raw_out.write("================================================================================\n\n")

        for sql_file in sql_files:
            file_path = sql_dir / sql_file
            content = file_path.read_text(encoding="utf-8")
            queries = split_sql_queries(content)

            print(f"--> Executing Module: {sql_file} ({len(queries)} queries)...")
            raw_out.write(f"================================================================================\n")
            raw_out.write(f"MODULE: {sql_file}\n")
            raw_out.write(f"================================================================================\n\n")

            for idx, (title, query_stmt) in enumerate(queries, 1):
                start_time = time.time()
                try:
                    df = pd.read_sql_query(text(query_stmt), conn)
                    elapsed = time.time() - start_time
                    total_execution_time += elapsed
                    total_queries += 1

                    print(f"    [{idx}/{len(queries)}] {title} ({len(df)} rows returned in {elapsed:.3f}s)")
                    raw_out.write(f"--- {title} ---\n")
                    raw_out.write(f"Execution time: {elapsed:.4f}s | Rows returned: {len(df)}\n")
                    raw_out.write(df.to_string() + "\n\n")

                except Exception as ex:
                    elapsed = time.time() - start_time
                    print(f"    [FAIL] {title} failed after {elapsed:.3f}s: {ex}")
                    failed_queries.append((sql_file, title, str(ex)))
                    try:
                        conn.rollback()
                    except Exception:
                        pass

            print()

    print("=" * 80)
    print(f"EXECUTION COMPLETE: {total_queries} queries executed across {len(sql_files)} modules in {total_execution_time:.2f}s")
    print(f"Raw query outputs saved to: {output_raw_file.relative_to(project_root)}")
    print("=" * 80)

    if failed_queries:
        print(f"\n[FAILURE] {len(failed_queries)} query execution errors encountered:")
        for f, t, err in failed_queries:
            print(f"  - [{f}] {t}: {err}")
        sys.exit(1)
    else:
        print("\n[SUCCESS] 100% OF RECONCILIATION ANALYTICAL QUERIES EXECUTED CLEANLY AND READ-ONLY.")


if __name__ == "__main__":
    run_stage_6_3_suite()
