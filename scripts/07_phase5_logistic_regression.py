"""Phase 5: logistic regression default model. See notes/09-Phase5-Model-Concepts.md and notes/10-Phase5-Model-Results.md"""

import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

DB_PATH = Path("data/loans.db")


def load_completed(conn):
    return pd.read_sql(
        """SELECT grade, purpose, annual_income, loan_amount, term_months, is_default
           FROM loans_scored WHERE is_completed = 1""",
        conn,
    )


def build_features(df):
    X = pd.get_dummies(df[["grade", "purpose", "annual_income", "loan_amount", "term_months"]],
                        columns=["grade", "purpose"], drop_first=True)
    y = df["is_default"]
    return X, y


def train_and_evaluate(X, y):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    numeric_cols = ["annual_income", "loan_amount", "term_months"]
    scaler = StandardScaler()
    X_train_scaled = X_train.copy()
    X_test_scaled = X_test.copy()
    X_train_scaled[numeric_cols] = scaler.fit_transform(X_train[numeric_cols])
    X_test_scaled[numeric_cols] = scaler.transform(X_test[numeric_cols])

    model = LogisticRegression(class_weight="balanced", max_iter=1000)
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    y_proba = model.predict_proba(X_test_scaled)[:, 1]

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "auc": roc_auc_score(y_test, y_proba),
    }
    return model, X_train_scaled.columns, metrics


def feature_importance(model, feature_names):
    importance = pd.Series(model.coef_[0], index=feature_names).sort_values()
    return importance


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    df = load_completed(conn)
    X, y = build_features(df)
    model, feature_names, metrics = train_and_evaluate(X, y)

    print("Overall default rate:", y.mean())
    print("Metrics:", metrics)

    importance = feature_importance(model, feature_names)
    importance.to_csv("data/processed/phase5_feature_importance.csv", header=["coefficient"])
    print("\nTop 10 features by |coefficient|:")
    print(importance.reindex(importance.abs().sort_values(ascending=False).index).head(10))

    fig, ax = plt.subplots(figsize=(8, 10))
    importance.plot(kind="barh", ax=ax)
    ax.set_xlabel("Standardized logistic regression coefficient")
    ax.set_title("Feature importance — default prediction")
    fig.tight_layout()
    fig.savefig("data/processed/phase5_feature_importance.png", dpi=120)

    conn.close()
