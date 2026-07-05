"""Phase 2: 10 SQL queries. See notes/04-Phase2-Approach-And-Queries.md"""

import sqlite3
from pathlib import Path

DB_PATH = Path("data/loans.db")

CREATE_VIEW_SQL = """
DROP VIEW IF EXISTS loans_scored;
CREATE VIEW loans_scored AS
SELECT
    *,
    CASE WHEN loan_status IN ('Fully Paid','Charged Off','Default') THEN 1 ELSE 0 END AS is_completed,
    CASE WHEN loan_status IN ('Charged Off','Default') THEN 1 ELSE 0 END AS is_default,
    SUBSTR(issue_date, 1, 4) AS issue_year
FROM loans;
"""

QUERIES = {
    "1_default_rate_by_grade": """
        SELECT grade,
               COUNT(*)                                            AS completed_loans,
               SUM(is_default)                                     AS defaulted_loans,
               ROUND(100.0 * SUM(is_default) / COUNT(*), 2)        AS default_rate_pct
        FROM loans_scored
        WHERE is_completed = 1
        GROUP BY grade
        ORDER BY grade;
    """,

    "2_rate_and_default_by_grade_purpose": """
        SELECT grade, purpose,
               COUNT(*)                                                                   AS n_loans,
               ROUND(AVG(interest_rate), 2)                                                AS avg_interest_rate,
               ROUND(100.0 * SUM(is_default) / NULLIF(SUM(is_completed), 0), 2)            AS default_rate_pct,
               CASE WHEN COUNT(*) < 30 THEN 'low-confidence (n<30)' ELSE 'ok' END          AS sample_flag
        FROM loans_scored
        GROUP BY grade, purpose
        ORDER BY grade, purpose;
    """,

    "3_top10_riskiest_purposes_rank": """
        WITH purpose_risk AS (
            SELECT purpose,
                   COUNT(*)                                     AS completed_loans,
                   SUM(is_default)                              AS defaults,
                   ROUND(100.0 * SUM(is_default) / COUNT(*), 2)  AS default_rate_pct
            FROM loans_scored
            WHERE is_completed = 1
            GROUP BY purpose
        )
        SELECT purpose, completed_loans, defaults, default_rate_pct,
               RANK() OVER (ORDER BY default_rate_pct DESC) AS risk_rank
        FROM purpose_risk
        ORDER BY risk_rank
        LIMIT 10;
    """,

    "4_revenue_at_risk_by_grade": """
        SELECT grade,
               ROUND(SUM(loan_amount), 0)                                              AS total_originated,
               ROUND(SUM(CASE WHEN is_default = 1 THEN loan_amount ELSE 0 END), 0)      AS revenue_at_risk_principal,
               ROUND(SUM(CASE WHEN is_default = 1 THEN post_default_recoveries ELSE 0 END), 0) AS recovered_after_default,
               ROUND(100.0 * SUM(CASE WHEN is_default = 1 THEN loan_amount ELSE 0 END) / SUM(loan_amount), 2) AS pct_of_book_at_risk
        FROM loans_scored
        WHERE is_completed = 1
        GROUP BY grade
        ORDER BY grade;
    """,

    "5_underpriced_low_risk_customers": """
        WITH grade_quality AS (
            SELECT grade,
                   ROUND(100.0 * SUM(is_default) / SUM(is_completed), 2) AS grade_default_rate
            FROM loans_scored
            WHERE is_completed = 1
            GROUP BY grade
        ),
        median_grade_quality AS (
            SELECT grade_default_rate AS median_val
            FROM grade_quality
            ORDER BY grade_default_rate
            LIMIT 1 OFFSET (SELECT COUNT(*) / 2 FROM grade_quality)
        ),
        ranked AS (
            SELECT grade, purpose, loan_amount, interest_rate, annual_income,
                   PERCENT_RANK() OVER (PARTITION BY grade ORDER BY interest_rate) AS rate_percentile_in_grade,
                   PERCENT_RANK() OVER (ORDER BY annual_income)                    AS income_percentile_overall
            FROM loans_scored
        )
        SELECT r.grade, r.purpose, r.loan_amount, r.interest_rate, r.annual_income,
               ROUND(r.rate_percentile_in_grade, 3)   AS rate_percentile_in_grade,
               ROUND(r.income_percentile_overall, 3)  AS income_percentile_overall
        FROM ranked r
        JOIN grade_quality gq ON gq.grade = r.grade
        CROSS JOIN median_grade_quality m
        WHERE gq.grade_default_rate <= m.median_val
          AND r.income_percentile_overall >= 0.5
          AND r.rate_percentile_in_grade >= 0.5
        ORDER BY r.rate_percentile_in_grade DESC
        LIMIT 20;
    """,

    "6_cohort_analysis_by_issue_year": """
        SELECT issue_year,
               COUNT(*)                                                       AS total_loans_in_cohort,
               SUM(is_completed)                                              AS completed_loans,
               SUM(is_default)                                                AS defaults,
               ROUND(100.0 * SUM(is_default) / NULLIF(SUM(is_completed), 0), 2) AS default_rate_pct_of_completed,
               ROUND(100.0 * SUM(is_completed) / COUNT(*), 2)                  AS pct_of_cohort_completed
        FROM loans_scored
        GROUP BY issue_year
        ORDER BY issue_year;
    """,

    "7_rate_dispersion_by_grade": """
        SELECT grade,
               COUNT(*)                                                                          AS n_loans,
               ROUND(AVG(interest_rate), 2)                                                       AS avg_rate,
               ROUND(MIN(interest_rate), 2)                                                       AS min_rate,
               ROUND(MAX(interest_rate), 2)                                                       AS max_rate,
               ROUND(SQRT(AVG(interest_rate*interest_rate) - AVG(interest_rate)*AVG(interest_rate)), 2) AS stddev_rate
        FROM loans_scored
        GROUP BY grade
        ORDER BY grade;
    """,

    "8_default_rate_by_grade_and_income_quartile": """
        WITH income_quartiles AS (
            SELECT grade, annual_income, is_default,
                   NTILE(4) OVER (ORDER BY annual_income) AS income_quartile
            FROM loans_scored
            WHERE is_completed = 1
        )
        SELECT grade, income_quartile,
               COUNT(*)                                        AS n_loans,
               ROUND(AVG(annual_income), 0)                     AS avg_income_in_bucket,
               ROUND(100.0 * SUM(is_default) / COUNT(*), 2)     AS default_rate_pct
        FROM income_quartiles
        GROUP BY grade, income_quartile
        ORDER BY grade, income_quartile;
    """,

    "9_purpose_term_segments_lowest_risk": """
        SELECT purpose, term_months,
               COUNT(*)                                                                AS n_loans,
               ROUND(AVG(interest_rate), 2)                                            AS avg_rate,
               ROUND(100.0 * SUM(is_default) / NULLIF(SUM(is_completed), 0), 2)         AS default_rate_pct
        FROM loans_scored
        GROUP BY purpose, term_months
        HAVING SUM(is_completed) > 0
        ORDER BY default_rate_pct ASC
        LIMIT 15;
    """,

    "10_realized_margin_by_grade": """
        SELECT grade,
               ROUND(SUM(interest_received), 0)                                              AS interest_actually_collected,
               ROUND(SUM(CASE WHEN is_default = 1 THEN loan_amount - principal_received ELSE 0 END), 0) AS unrecovered_principal_loss,
               ROUND(SUM(interest_received) - SUM(CASE WHEN is_default = 1 THEN loan_amount - principal_received ELSE 0 END), 0) AS realized_margin
        FROM loans_scored
        WHERE is_completed = 1
        GROUP BY grade
        ORDER BY grade;
    """,
}


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(CREATE_VIEW_SQL)

    for name, sql in QUERIES.items():
        print(f"\n=== {name} ===")
        cur = conn.execute(sql)
        cols = [d[0] for d in cur.description]
        print("  " + " | ".join(cols))
        for row in cur.fetchall():
            print("  " + " | ".join(str(v) for v in row))

    conn.close()
