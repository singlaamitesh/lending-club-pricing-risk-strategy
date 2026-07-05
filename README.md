# Segment-Based Pricing & Risk Strategy for a Lending Portfolio

A data analyst portfolio project analyzing 2.26M Lending Club loans to
recommend segment-based pricing over blanket, grade-only pricing.

**Read first:** [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md) — the
one-page business summary with the key finding, recommendation, estimated
impact, and sensitivity check.

## Architecture

```
raw CSV (Kaggle) → SQLite (SQL analysis layer) → Python (pandas/scipy/sklearn)
→ Power BI dashboard → executive summary
```

## Repository Structure

```
data/
  raw/loan.csv          # not committed — download from Kaggle (see Setup)
  loans.db              # SQLite database (generated)
  processed/            # CSVs exported for Power BI + model artifacts
scripts/
  01_load_and_audit.py               # Phase 1: load raw CSV into SQLite
  02_data_quality_audit.py           # Phase 1: pre-cleaning data quality audit
  03_build_clean_loans.py            # Phase 1: build final clean `loans` table
  04_phase2_queries.py               # Phase 2: 10 SQL business-question queries
  05_phase3_hypothesis_tests.py      # Phase 3: chi-square, correlation, t-test
  06_phase4_segmentation.py          # Phase 4: 6 data-derived risk/value segments
  07_phase5_logistic_regression.py   # Phase 5: default-prediction model
  08_phase6_ab_test_simulation.py    # Phase 6: A/B test design + power analysis
  09_phase7_export_for_dashboard.py  # Phase 7: CSV exports + sensitivity check
notes/                   # Obsidian vault — every decision explained, beginner-level,
                          # including concepts considered but NOT used and why
EXECUTIVE_SUMMARY.md
README.md
```

## Setup

1. Download the Lending Club Loan Data dataset from Kaggle and place the
   CSV at `data/raw/loan.csv`.
2. `pip install pandas numpy scipy scikit-learn matplotlib`
3. Run the scripts in order (01 → 09) from the project root:
   ```
   python3 scripts/01_load_and_audit.py
   python3 scripts/02_data_quality_audit.py
   python3 scripts/03_build_clean_loans.py
   python3 scripts/04_phase2_queries.py
   python3 scripts/05_phase3_hypothesis_tests.py
   python3 scripts/06_phase4_segmentation.py
   python3 scripts/07_phase5_logistic_regression.py
   python3 scripts/08_phase6_ab_test_simulation.py
   python3 scripts/09_phase7_export_for_dashboard.py
   ```

## Methodology & Notes

Every technical decision (why this test, why this cutoff, why this model)
is explained in `notes/`, starting from `notes/00-Project-Overview.md`.
Notes are written to be understandable with zero prior coding/stats
background, and explicitly call out relevant approaches that were
considered but **not** used, and why — so the reasoning behind every
choice is defensible, not just the code that implements it.

## Key Finding

Good-grade (A-D), high-income borrowers pay only 0.86 points less than
low-income peers (11.77% vs 12.63%) despite income independently
predicting lower default risk at every grade — while the "High Risk /
High Value" segment runs a realized loss of $227.1M. See
`EXECUTIVE_SUMMARY.md` for the full recommendation and sensitivity check.

## Dashboard

Power BI visual specs (which chart, which fields) are in
`notes/13-Phase7-Dashboard-And-Sensitivity.md`. Source CSVs are in
`data/processed/`.
