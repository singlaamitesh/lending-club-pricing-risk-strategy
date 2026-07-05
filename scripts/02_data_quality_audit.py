"""Phase 1b: data quality audit on the raw table. See notes/01-Data-Quality-Audit-Concepts.md"""

import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path("data/loans.db")
RAW_TABLE = "loans_raw"


def missing_report(conn: sqlite3.Connection, table: str) -> pd.DataFrame:
    total = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    cols = [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]

    rows = []
    for col in cols:
        missing = conn.execute(
            f'SELECT COUNT(*) FROM {table} WHERE "{col}" IS NULL OR TRIM("{col}") = \'\''
        ).fetchone()[0]
        rows.append({"column": col, "missing_pct": round(100 * missing / total, 2)})

    return pd.DataFrame(rows).sort_values("missing_pct", ascending=False)


def duplicate_report(conn: sqlite3.Connection, table: str) -> int:
    return conn.execute(
        f"SELECT COUNT(*) FROM (SELECT id FROM {table} GROUP BY id HAVING COUNT(*) > 1)"
    ).fetchone()[0]


def outlier_report(conn: sqlite3.Connection, table: str) -> dict:
    checks = {
        "loan_amnt <= 0": f"SELECT COUNT(*) FROM {table} WHERE loan_amnt <= 0",
        "int_rate <= 0 or int_rate > 40 (%)": (
            f"SELECT COUNT(*) FROM {table} "
            f"WHERE CAST(REPLACE(int_rate, '%', '') AS REAL) <= 0 "
            f"OR CAST(REPLACE(int_rate, '%', '') AS REAL) > 40"
        ),
        "annual_inc <= 0": f"SELECT COUNT(*) FROM {table} WHERE annual_inc <= 0",
        "annual_inc > 5,000,000 (extreme, review not auto-drop)": (
            f"SELECT COUNT(*) FROM {table} WHERE annual_inc > 5000000"
        ),
    }
    return {label: conn.execute(sql).fetchone()[0] for label, sql in checks.items()}


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)

    print("=== Missing % per column (top 20) ===")
    print(missing_report(conn, RAW_TABLE).head(20).to_string(index=False))

    print(f"\n=== Duplicate `id` groups ===\n{duplicate_report(conn, RAW_TABLE)}")

    print("\n=== Outlier / impossible-value checks (columns we plan to keep) ===")
    for label, count in outlier_report(conn, RAW_TABLE).items():
        print(f"  {label}: {count:,} rows")

    conn.close()
