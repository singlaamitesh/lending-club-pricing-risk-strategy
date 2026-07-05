"""Phase 7: export CSVs for Power BI + sensitivity check. See notes/13-Phase7-Dashboard-And-Sensitivity.md"""

import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path("data/loans.db")
OUT_DIR = Path("data/processed")


def load_all(conn):
    return pd.read_sql(
        """SELECT grade, loan_amount, interest_rate, annual_income, term_months,
                  is_completed, is_default, interest_received, principal_received, issue_year
           FROM loans_scored""",
        conn,
    )


def build_segments(df):
    df = df.copy()
    grade_default_rate = df.loc[df["is_completed"] == 1].groupby("grade")["is_default"].mean()
    df["risk_score"] = df["grade"].map(grade_default_rate)
    df["value_score"] = df["loan_amount"] * df["term_months"]
    df["risk_tier"] = pd.qcut(df["risk_score"], 3, labels=["Low Risk", "Medium Risk", "High Risk"])
    df["value_tier"] = pd.qcut(df["value_score"], 2, labels=["Low Value", "High Value"])
    df["segment"] = df["risk_tier"].astype(str) + " / " + df["value_tier"].astype(str)
    return df


def default_rate_by_grade(df):
    completed = df[df["is_completed"] == 1]
    result = completed.groupby("grade").agg(
        completed_loans=("is_default", "size"),
        defaulted_loans=("is_default", "sum"),
    )
    result["default_rate_pct"] = (result["defaulted_loans"] / result["completed_loans"] * 100).round(2)
    return result


def cohort_analysis(df):
    result = df.groupby("issue_year").agg(
        total_loans_in_cohort=("is_default", "size"),
        completed_loans=("is_completed", "sum"),
        defaults=("is_default", "sum"),
    )
    result["default_rate_pct_of_completed"] = (result["defaults"] / result["completed_loans"] * 100).round(2)
    result["pct_of_cohort_completed"] = (result["completed_loans"] / result["total_loans_in_cohort"] * 100).round(2)
    return result


def realized_margin_by_grade(df):
    completed = df[df["is_completed"] == 1].copy()
    completed["unrecovered_loss"] = completed["is_default"] * (
        completed["loan_amount"] - completed["principal_received"]
    )
    return completed.groupby("grade").agg(
        interest_actually_collected=("interest_received", "sum"),
        unrecovered_principal_loss=("unrecovered_loss", "sum"),
    ).assign(
        realized_margin=lambda d: d["interest_actually_collected"] - d["unrecovered_principal_loss"]
    ).round(0)


def segment_sensitivity(df):
    completed = df[df["is_completed"] == 1].copy()
    completed["unrecovered_loss"] = completed["is_default"] * (
        completed["loan_amount"] - completed["principal_received"]
    )
    grouped = completed.groupby("segment").agg(
        n_loans=("segment", "size"),
        interest_actually_collected=("interest_received", "sum"),
        unrecovered_principal_loss=("unrecovered_loss", "sum"),
    )
    grouped["realized_margin"] = grouped["interest_actually_collected"] - grouped["unrecovered_principal_loss"]
    grouped["margin_pessimistic_20pct_more_defaults"] = (
        grouped["interest_actually_collected"] - grouped["unrecovered_principal_loss"] * 1.2
    )
    grouped["margin_optimistic_20pct_fewer_defaults"] = (
        grouped["interest_actually_collected"] - grouped["unrecovered_principal_loss"] * 0.8
    )
    return grouped.round(0)


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    df = build_segments(load_all(conn))

    default_rate_by_grade(df).to_csv(OUT_DIR / "phase7_default_rate_by_grade.csv")
    cohort_analysis(df).to_csv(OUT_DIR / "phase7_cohort_analysis.csv")
    realized_margin_by_grade(df).to_csv(OUT_DIR / "phase7_realized_margin_by_grade.csv")

    sensitivity = segment_sensitivity(df)
    sensitivity.to_csv(OUT_DIR / "phase7_segment_sensitivity.csv")

    print(sensitivity)
    conn.close()
