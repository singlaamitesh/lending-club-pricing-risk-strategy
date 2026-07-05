"""Phase 1c: build the final clean `loans` table. See notes/02-Phase1-Audit-Findings.md"""

import sqlite3
from pathlib import Path

DB_PATH = Path("data/loans.db")

BUILD_LOANS_SQL = """
CREATE TABLE loans AS
WITH deduped AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY loan_amnt, term, int_rate, installment, grade,
                            annual_inc, purpose, issue_d, dti, addr_state, loan_status
               ORDER BY rowid
           ) AS rn
    FROM loans_raw
    WHERE annual_inc > 0
)
SELECT
    loan_amnt        AS loan_amount,
    int_rate         AS interest_rate,
    grade            AS grade,
    annual_inc       AS annual_income,
    purpose          AS purpose,
    CAST(TRIM(REPLACE(term, 'months', '')) AS INTEGER) AS term_months,
    REPLACE(loan_status, 'Does not meet the credit policy. Status:', '') AS loan_status,
    (SUBSTR(issue_d, INSTR(issue_d, '-') + 1) || '-' ||
     CASE SUBSTR(issue_d, 1, 3)
         WHEN 'Jan' THEN '01' WHEN 'Feb' THEN '02' WHEN 'Mar' THEN '03'
         WHEN 'Apr' THEN '04' WHEN 'May' THEN '05' WHEN 'Jun' THEN '06'
         WHEN 'Jul' THEN '07' WHEN 'Aug' THEN '08' WHEN 'Sep' THEN '09'
         WHEN 'Oct' THEN '10' WHEN 'Nov' THEN '11' WHEN 'Dec' THEN '12'
     END || '-01') AS issue_date,
    total_pymnt      AS total_payment_received,
    total_rec_prncp  AS principal_received,
    total_rec_int    AS interest_received,
    recoveries       AS post_default_recoveries
FROM deduped
WHERE rn = 1;
"""


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS loans")
    conn.executescript(BUILD_LOANS_SQL)
    conn.commit()

    raw_count = conn.execute("SELECT COUNT(*) FROM loans_raw").fetchone()[0]
    clean_count = conn.execute("SELECT COUNT(*) FROM loans").fetchone()[0]
    print(f"loans_raw: {raw_count:,} rows")
    print(f"loans:     {clean_count:,} rows  (dropped {raw_count - clean_count:,})")

    print("\nSample rows:")
    for row in conn.execute("SELECT * FROM loans LIMIT 5"):
        print(row)

    print("\nloan_status distribution in clean table:")
    for row in conn.execute("SELECT loan_status, COUNT(*) FROM loans GROUP BY loan_status ORDER BY 2 DESC"):
        print(" ", row)

    conn.close()
