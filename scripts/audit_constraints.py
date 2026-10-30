#!/usr/bin/env python3
"""
Detailed constraint and index auditor for SQL migrations.
"""
import re
from pathlib import Path

MIGRATIONS_DIR = Path("sql/migrations")

pk_constraints = []
uq_constraints = []
fk_constraints = []
chk_constraints = []
excl_constraints = []
unique_indexes = []
supporting_indexes = []

for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
    content = sql_file.read_text(encoding="utf-8")
    
    # Strip comments
    lines = content.splitlines()
    clean_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("--") or stripped.startswith("/*"):
            continue
        # also remove inline comments
        if "--" in line:
            line = line.split("--")[0]
        clean_lines.append(line)
    clean_text = "\n".join(clean_lines)

    # 1. Primary keys:
    # Match: CONSTRAINT name PRIMARY KEY (...)
    pks = re.findall(r"CONSTRAINT\s+([a-zA-Z_0-9]+)\s+PRIMARY\s+KEY\s*\(([^\)]+)\)", clean_text, re.IGNORECASE)
    for name, cols in pks:
        pk_constraints.append((sql_file.name, name, cols.strip()))
    
    # Inline primary keys on column: colname ... PRIMARY KEY
    inline_pks = re.findall(r"^\s*([a-zA-Z_0-9]+)\s+[^,;]+?PRIMARY\s+KEY", clean_text, re.IGNORECASE | re.MULTILINE)
    for col in inline_pks:
        if not any(col.lower() in p[2].lower() for p in pk_constraints if p[0] == sql_file.name):
            pk_constraints.append((sql_file.name, f"pk_{col}_inline", col))

    # 2. Table-level Unique constraints:
    uqs = re.findall(r"CONSTRAINT\s+([a-zA-Z_0-9]+)\s+UNIQUE\s*\(([^\)]+)\)", clean_text, re.IGNORECASE)
    for name, cols in uqs:
        uq_constraints.append((sql_file.name, name, cols.strip()))

    # 3. Foreign key constraints:
    fks = re.findall(r"CONSTRAINT\s+([a-zA-Z_0-9]+)\s+FOREIGN\s+KEY\s*\(([^\)]+)\)\s*REFERENCES\s*([a-zA-Z_0-9\.]+)\s*\(([^\)]+)\)", clean_text, re.IGNORECASE)
    for name, cols, ref_table, ref_cols in fks:
        fk_constraints.append((sql_file.name, name, cols.strip(), ref_table.strip(), ref_cols.strip()))

    # 4. Check constraints:
    chks = re.findall(r"CONSTRAINT\s+([a-zA-Z_0-9]+)\s+CHECK\s*\(([^\;]+?)\)(?:\s*,|\s*\))", clean_text, re.IGNORECASE)
    for name, expr in chks:
        chk_constraints.append((sql_file.name, name, expr.strip()))

    # 5. Exclusion constraints:
    excls = re.findall(r"CONSTRAINT\s+([a-zA-Z_0-9]+)\s+EXCLUDE", clean_text, re.IGNORECASE)
    for name in excls:
        excl_constraints.append((sql_file.name, name))

    # 6. Standalone unique indexes:
    uis = re.findall(r"CREATE\s+UNIQUE\s+INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z_0-9]+)\s+ON\s+([a-zA-Z_0-9\.]+)\s*\(([^\)]+)\)(?:\s*WHERE\s*\(([^\)]+)\))?", clean_text, re.IGNORECASE)
    for name, tbl, cols, where in uis:
        unique_indexes.append((sql_file.name, name, tbl, cols.strip(), where.strip() if where else None))

    # 7. Supporting indexes:
    # Match CREATE INDEX (not UNIQUE)
    sis = re.finditer(r"CREATE\s+INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z_0-9]+)\s+ON\s+([a-zA-Z_0-9\.]+)(?:\s+USING\s+([a-zA-Z_0-9]+))?\s*\(([^\)]+)\)(?:\s*WITH\s*\(([^\)]+)\))?(?:\s*WHERE\s*\(([^\)]+)\))?", clean_text, re.IGNORECASE)
    for m in sis:
        name = m.group(1)
        tbl = m.group(2)
        idx_type = m.group(3) or "btree"
        cols = m.group(4).strip()
        params = m.group(5)
        where = m.group(6)
        supporting_indexes.append((sql_file.name, name, tbl, idx_type, cols, where))

print(f"Primary Key Constraints:   {len(pk_constraints)}")
for p in pk_constraints:
    print(f"  - {p[0]}: {p[1]} ({p[2]})")

print(f"\nUnique Constraints:        {len(uq_constraints)}")
for u in uq_constraints:
    print(f"  - {u[0]}: {u[1]} ({u[2]})")

print(f"\nForeign Key Constraints:   {len(fk_constraints)}")
for f in fk_constraints:
    print(f"  - {f[0]}: {f[1]} ({f[2]} -> {f[3]}({f[4]}))")

print(f"\nCheck Constraints:         {len(chk_constraints)}")
for c in chk_constraints:
    print(f"  - {c[0]}: {c[1]}")

print(f"\nExclusion Constraints:     {len(excl_constraints)}")

print(f"\nStandalone Unique Indexes: {len(unique_indexes)}")
for ui in unique_indexes:
    print(f"  - {ui[0]}: {ui[1]} ON {ui[2]} ({ui[3]})" + (f" WHERE {ui[4]}" if ui[4] else ""))

print(f"\nSupporting Indexes:        {len(supporting_indexes)}")
for si in supporting_indexes:
    print(f"  - {si[0]}: {si[1]} ON {si[2]} USING {si[3]} ({si[4]})" + (f" WHERE {si[5]}" if si[5] else ""))

