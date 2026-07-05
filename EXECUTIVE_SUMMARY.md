# Segment-Based Pricing & Risk Strategy — Executive Summary

## Problem
The lender currently prices loans almost entirely off credit grade (A-G),
with minimal differentiation for income or purpose within a grade. This
project analyzes 2.26M historical loans to test whether this "blanket"
approach is leaving money on the table — both by underpricing safe
customers and by underpricing risk in the riskiest segments.

## Approach
Raw loan-level data was cleaned and loaded into SQL (2,258,991 loans after
removing 1,677 impossible/duplicate records), analyzed through 10
business-question SQL queries, validated with 5 statistical hypothesis
tests, split into 6 data-derived risk/value segments, used to train a
logistic regression default model, and stress-tested with a simulated
A/B test and a ±20% sensitivity check. Full methodology and every
statistical choice is documented and defensible (see `notes/` vault).

## Key Finding
Within "good" grades (A-D, the below-median-risk grades), high-income
borrowers pay only **0.86 percentage points less** than low-income peers
on average (11.77% vs 12.63%, t-test p≈0) — despite income independently
predicting a **lower default rate at every grade level** (Phase 2 Query
8). At the very top of a grade's rate band, this gap disappears entirely:
Grade-A borrowers earning $65K and $300K pay the **exact same 9.63%
rate**. Meanwhile, at the other end of the risk spectrum, the "High
Risk / High Value" segment (333,923 loans, $7.15B originated) is running
a **realized loss of $227.1M** — actual interest collected minus actual
unrecovered principal after default.

## Recommendation
1. **Re-price or cap loan size** for the High Risk / High Value segment —
   current pricing does not cover its risk.
2. **Close the income-based pricing gap** for good-grade, high-income
   borrowers via a phased pilot (not a full-segment rollout — see
   Adverse Selection risk below).
3. **Monitor the Medium Risk segments closely** — their margins are
   thin and sensitive to small changes in default assumptions (see
   Sensitivity Check).

## Estimated Impact
Simulating the income-gap pricing correction across the eligible
1,085,138-loan population suggests a **directional revenue lift of
~$629M** (lifetime, across loan terms) if borrower behavior is unchanged.
This is an upper-bound estimate — see caveats below.

## Sensitivity Check (±20% on default-rate assumptions)

| Segment | Base margin | +20% defaults | −20% defaults | Robust? |
|---|---|---|---|---|
| Low Risk / Low Value | +$163.3M | +$121.2M | +$205.3M | Yes |
| Low Risk / High Value | +$208.3M | +$139.7M | +$276.8M | Yes |
| Medium Risk / Low Value | +$35.4M | −$7.5M | +$78.2M | **No — flips** |
| Medium Risk / High Value | +$10.3M | −$118.4M | +$139.0M | **No — flips** |
| High Risk / Low Value | −$1.9M | −$39.7M | +$35.8M | **No — flips** |
| High Risk / High Value | −$227.1M | −$493.1M | +$39.0M | **No — flips** |

The Low Risk segments' conclusions hold under any reasonable estimation
error — confident to act on. The Medium/High Risk segments' conclusions
are directionally right but **not robust to a ±20% miss on default
estimates**, so any pricing action there should ship with monitoring, not
a one-time blanket change.

## Key Caveats
- The $629M estimate assumes default behavior is unchanged after the
  price increase. In reality, raising rates for a segment risks
  **adverse selection** — better-risk borrowers may shop elsewhere,
  leaving a relatively riskier mix behind. Recommendation 2 should be
  piloted on a small sample first, not rolled out portfolio-wide.
- The logistic regression default model (AUC 0.69) intentionally uses
  only 5 simple, explainable features; a production model would likely
  add credit-history fields (`dti`, `revol_util`, etc.) for better
  discrimination at the cost of some interpretability.
- Revenue figures use actual collected amounts (`total_rec_int`,
  `recoveries`) where available, but the simulated A/B test revenue uses
  a simplified `loan_amount × rate × term` formula, not a full
  amortization schedule.

---
Full methodology, every statistical test, and all concepts (including
what was considered and *not* used, and why) are documented phase-by-phase
in `notes/00-Project-Overview.md` and linked notes.
