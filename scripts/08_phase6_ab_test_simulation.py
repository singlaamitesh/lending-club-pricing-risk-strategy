"""Phase 6: A/B test design, power analysis, simulation. See notes/11-Phase6-AB-Test-Concepts.md and notes/12-Phase6-AB-Test-Results.md"""

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

DB_PATH = Path("data/loans.db")
RANDOM_SEED = 42


def load_all(conn):
    return pd.read_sql(
        "SELECT grade, loan_amount, interest_rate, annual_income, term_months, is_completed, is_default, issue_year FROM loans_scored",
        conn,
    )


def good_grades_by_median_default_rate(df):
    completed = df[df["is_completed"] == 1]
    grade_default_rate = completed.groupby("grade")["is_default"].mean() * 100
    median_rate = grade_default_rate.median()
    return grade_default_rate[grade_default_rate <= median_rate].index.tolist()


def measure_rate_gap(df, good_grades):
    subset = df[df["grade"].isin(good_grades)]
    income_median = subset["annual_income"].median()
    high = subset.loc[subset["annual_income"] >= income_median, "interest_rate"]
    low = subset.loc[subset["annual_income"] < income_median, "interest_rate"]
    return low.mean() - high.mean(), income_median


def simulate_ab_test(df, good_grades, income_median, rate_uplift_pts, seed=RANDOM_SEED):
    target = df[(df["grade"].isin(good_grades)) & (df["annual_income"] >= income_median)].copy()

    rng = np.random.default_rng(seed)
    target["arm"] = rng.choice(["control", "treatment"], size=len(target), p=[0.5, 0.5])

    target["applied_rate"] = np.where(
        target["arm"] == "treatment", target["interest_rate"] + rate_uplift_pts, target["interest_rate"]
    )
    target["simulated_interest_revenue"] = (
        target["loan_amount"] * (target["applied_rate"] / 100) * (target["term_months"] / 12)
    )
    return target


def required_sample_size(effect_size_d, alpha=0.05, power=0.80):
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_power = stats.norm.ppf(power)
    return 2 * ((z_alpha + z_power) / effect_size_d) ** 2


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    df = load_all(conn)

    good_grades = good_grades_by_median_default_rate(df)
    rate_gap, income_median = measure_rate_gap(df, good_grades)
    print(f"good grades: {good_grades}")
    print(f"income median: {income_median}")
    print(f"measured rate gap (low-income minus high-income): {rate_gap:.4f} points")

    target = simulate_ab_test(df, good_grades, income_median, rate_gap)
    control = target.loc[target["arm"] == "control", "simulated_interest_revenue"]
    treatment = target.loc[target["arm"] == "treatment", "simulated_interest_revenue"]

    t_stat, p_val = stats.ttest_ind(treatment, control, equal_var=False)
    n1, n2 = len(treatment), len(control)
    pooled_var = ((n1 - 1) * treatment.var() + (n2 - 1) * control.var()) / (n1 + n2 - 2)
    cohens_d = (treatment.mean() - control.mean()) / np.sqrt(pooled_var)

    print(f"\ntarget population size: {len(target)}")
    print(f"control (n={n1}) mean simulated revenue: {control.mean():.2f}")
    print(f"treatment (n={n2}) mean simulated revenue: {treatment.mean():.2f}")
    print(f"lift per loan: {treatment.mean() - control.mean():.2f}")
    print(f"t={t_stat:.2f}  p={p_val:.4g}  cohens_d={cohens_d:.4f}")

    n_needed = required_sample_size(cohens_d)
    print(f"\nrequired sample size per arm (alpha=.05, power=.80): {n_needed:.1f}")
    print(f"available per arm in this simulation: {min(n1, n2)}")

    total_loans = len(df)
    fraction_target = len(target) / total_loans
    recent_year_volume = df.loc[df["issue_year"] == "2017"].shape[0]
    monthly_total_volume = recent_year_volume / 12
    monthly_target_volume = monthly_total_volume * fraction_target
    months_needed = (2 * n_needed) / monthly_target_volume

    print(f"\ntarget segment share of all originations: {fraction_target:.4f}")
    print(f"2017 originations (proxy for current run-rate): {recent_year_volume}")
    print(f"estimated monthly target-segment volume: {monthly_target_volume:.1f}")
    print(f"estimated months needed for a live test: {months_needed:.2f}")

    conn.close()
