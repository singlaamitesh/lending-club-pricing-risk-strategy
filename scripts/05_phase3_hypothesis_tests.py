"""Phase 3: hypothesis tests. See notes/05-Phase3-Hypothesis-Testing-Concepts.md and notes/06-Phase3-Results-And-Findings.md"""

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

DB_PATH = Path("data/loans.db")


def load_completed(conn):
    return pd.read_sql(
        "SELECT grade, interest_rate, annual_income, is_default FROM loans_scored WHERE is_completed = 1",
        conn,
    )


def load_all(conn):
    return pd.read_sql("SELECT grade, interest_rate, annual_income FROM loans_scored", conn)


def chi_square_grade_default(df):
    table = pd.crosstab(df["grade"], df["is_default"])
    chi2, p, dof, expected = stats.chi2_contingency(table)
    n = table.values.sum()
    cramers_v = np.sqrt(chi2 / (n * (min(table.shape) - 1)))
    return table, chi2, p, dof, cramers_v


def correlation_analysis(df):
    pairs = [
        ("interest_rate", "annual_income"),
        ("interest_rate", "is_default"),
        ("annual_income", "is_default"),
    ]
    results = {}
    for a, b in pairs:
        r, p = stats.pearsonr(df[a], df[b])
        results[f"{a}_vs_{b}"] = (r, p)
    return results


def good_grades_by_median_default_rate(df_completed):
    grade_default_rate = df_completed.groupby("grade")["is_default"].mean() * 100
    median_rate = grade_default_rate.median()
    good = grade_default_rate[grade_default_rate <= median_rate].index.tolist()
    return good, grade_default_rate, median_rate


def underpriced_ttest(df_all, good_grades):
    subset = df_all[df_all["grade"].isin(good_grades)]
    income_median = subset["annual_income"].median()
    high_income = subset.loc[subset["annual_income"] >= income_median, "interest_rate"]
    low_income = subset.loc[subset["annual_income"] < income_median, "interest_rate"]

    t_stat, p_val = stats.ttest_ind(high_income, low_income, equal_var=False)

    n1, n2 = len(high_income), len(low_income)
    pooled_var = ((n1 - 1) * high_income.var() + (n2 - 1) * low_income.var()) / (n1 + n2 - 2)
    cohens_d = (high_income.mean() - low_income.mean()) / np.sqrt(pooled_var)

    return {
        "income_median": income_median,
        "high_income_n": len(high_income),
        "low_income_n": len(low_income),
        "high_income_mean_rate": high_income.mean(),
        "low_income_mean_rate": low_income.mean(),
        "t_stat": t_stat,
        "p_value": p_val,
        "cohens_d": cohens_d,
    }


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    completed = load_completed(conn)
    all_loans = load_all(conn)

    print("=== Test 1: Chi-square (grade vs default) ===")
    table, chi2, p, dof, cramers_v = chi_square_grade_default(completed)
    print(table)
    print(f"chi2={chi2:.2f}  dof={dof}  p={p:.4g}  cramers_v={cramers_v:.4f}")

    print("\n=== Test 2: Correlation analysis ===")
    for label, (r, p_val) in correlation_analysis(completed).items():
        print(f"{label}: r={r:.4f}  p={p_val:.4g}")

    print("\n=== Test 3: T-test (income within good grades) ===")
    good, grade_default_rate, median_rate = good_grades_by_median_default_rate(completed)
    print(f"grade default rates:\n{grade_default_rate.round(2)}")
    print(f"median default rate across grades: {median_rate:.2f}")
    print(f"good grades (<= median): {good}")

    result = underpriced_ttest(all_loans, good)
    for k, v in result.items():
        print(f"{k}: {v}")

    conn.close()
