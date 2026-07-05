"""Phase 1a: load the raw CSV into SQLite. See notes/01-Phase1-Load-And-Clean.md"""

import sqlite3
from pathlib import Path

import pandas as pd

RAW_CSV = Path("data/raw/loan.csv")
DB_PATH = Path("data/loans.db")
RAW_TABLE = "loans_raw"
CHUNK_SIZE = 50_000


def load_csv_to_sqlite(csv_path: Path, db_path: Path, table: str, chunksize: int) -> int:
    if not csv_path.exists():
        raise FileNotFoundError(f"{csv_path} not found")

    conn = sqlite3.connect(db_path)
    total_rows = 0
    first_chunk = True

    for chunk in pd.read_csv(csv_path, chunksize=chunksize, low_memory=False):
        chunk.to_sql(
            table,
            conn,
            if_exists="replace" if first_chunk else "append",
            index=False,
        )
        total_rows += len(chunk)
        first_chunk = False
        print(f"  loaded {total_rows:,} rows so far...")

    conn.close()
    return total_rows


if __name__ == "__main__":
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    n = load_csv_to_sqlite(RAW_CSV, DB_PATH, RAW_TABLE, CHUNK_SIZE)
    print(f"\nDone. {n:,} rows loaded into {DB_PATH} -> table '{RAW_TABLE}'.")
