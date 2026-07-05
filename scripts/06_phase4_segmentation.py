"""Phase 4: segmentation. See notes/07-Phase4-Segmentation-Concepts.md and notes/08-Phase4-Segmentation-Results.md"""

import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path("data/loans.db")


def load_data(conn):
    return pd.read_sql(
        """SELECT grade, loan_amount, interest_rate, annual_income, term_months,
                  is_completed, is_default, interest_received, principal_received
           FROM loans_scored""",
        conn,
    )


def build_segments(df):
    df = df.copy()

    grade_default_rate = df.loc[df["is_completed"] == 1].groupby("grade")["is_default"].mean()
    df["risk_score"] = df["grade"].map(grade_default_rate)

    df["value_score"] = df["loan_amount"] * df["term_months"]
    df["rate_sensitivity_proxy"] = df["annual_income"] / df["loan_amount"]
    df["rate_percentile_in_grade"] = df.groupby("grade")["interest_rate"].rank(pct=True)

    df["risk_tier"] = pd.qcut(df["risk_score"], 3, labels=["Low Risk", "Medium Risk", "High Risk"])
    df["value_tier"] = pd.qcut(df["value_score"], 2, labels=["Low Value", "High Value"])
    df["segment"] = df["risk_tier"].astype(str) + " / " + df["value_tier"].astype(str)

    return df


def summarize_segments(df):
    completed = df[df["is_completed"] == 1].copy()
    completed["unrecovered_loss"] = completed["is_default"] * (
        completed["loan_amount"] - completed["principal_received"]
    )
    completed["margin"] = completed["interest_received"] - completed["unrecovered_loss"]

    completed_agg = completed.groupby("segment").agg(
        default_rate_pct=("is_default", lambda s: s.mean() * 100),
        realized_margin=("margin", "sum"),
    )

    summary = df.groupby("segment").agg(
        n_loans=("segment", "size"),
        total_loan_value=("loan_amount", "sum"),
        avg_interest_rate=("interest_rate", "mean"),
        avg_annual_income=("annual_income", "mean"),
        avg_rate_sensitivity_proxy=("rate_sensitivity_proxy", "mean"),
        avg_rate_percentile_in_grade=("rate_percentile_in_grade", "mean"),
    )
    summary = summary.join(completed_agg)
    return summary.round(2)


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    df = build_segments(load_data(conn))
    summary = summarize_segments(df)

    pd.set_option("display.width", 160)
    print(summary)

    summary.to_csv("data/processed/phase4_segment_summary.csv")
    conn.close()
