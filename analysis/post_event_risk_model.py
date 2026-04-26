#!/usr/bin/env python3
"""Train a post-event L2M bad-call risk model."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
import sys

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from referee_fatigue.db import connect, create_referee_tables


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train post-event L2M risk model")
    parser.add_argument("--db-path", default="data/nba_stats.db")
    parser.add_argument("--output", default="results/post_event_risk_model_report.md")
    parser.add_argument("--predictions", default="results/post_event_high_risk_events.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    conn = connect(PROJECT_ROOT / args.db_path)
    create_referee_tables(conn)
    df = prepare_dataset(load_event_data(conn))
    train_df, test_df = split_by_game(df)
    pipeline = build_pipeline()
    pipeline.fit(train_df[FEATURE_COLUMNS], train_df["incorrect"])

    test_pred = pipeline.predict_proba(test_df[FEATURE_COLUMNS])[:, 1]
    full_pred = pipeline.predict_proba(df[FEATURE_COLUMNS])[:, 1]
    report = build_report(df, train_df, test_df, test_pred, pipeline)

    output_path = PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    scored = df.copy()
    scored["predicted_error_probability"] = full_pred
    scored.sort_values("predicted_error_probability", ascending=False).head(200).to_csv(
        PROJECT_ROOT / args.predictions, index=False
    )
    print(f"Wrote {output_path}")
    print(f"Wrote {PROJECT_ROOT / args.predictions}")


CATEGORICAL_FEATURES = [
    "call_family",
    "call_type_grouped",
    "decision_kind",
    "monitoring_type",
    "period_bucket",
    "clock_bucket",
]

NUMERIC_FEATURES = [
    "clock_seconds",
    "estimated_pace",
    "q4_pre_l2m_actions_per_minute",
    "l2m_actions_per_minute",
    "days_rest_capped",
    "games_last_7",
    "travel_miles_last_7k",
    "back_to_back",
]

FEATURE_COLUMNS = CATEGORICAL_FEATURES + NUMERIC_FEATURES


def load_event_data(conn) -> pd.DataFrame:
    return pd.read_sql_query(
        """
        SELECT
            e.game_id,
            e.event_index,
            e.period,
            e.game_clock,
            e.call_type,
            e.review_decision,
            e.incorrect,
            e.committing_player,
            e.disadvantaged_player,
            e.comment,
            ra.official_id AS crew_chief_id,
            l.days_rest,
            l.back_to_back,
            l.games_last_7,
            l.travel_miles_last_7_days,
            p.estimated_pace,
            p.q4_pre_l2m_actions_per_minute,
            p.l2m_actions_per_minute
        FROM l2m_events e
        JOIN l2m_reports r
            ON e.game_id = r.game_id
        LEFT JOIN referee_assignments ra
            ON e.game_id = ra.game_id AND ra.role = 'crew_chief'
        LEFT JOIN referee_load_features l
            ON e.game_id = l.game_id AND ra.official_id = l.official_id
        LEFT JOIN game_pace_features p
            ON e.game_id = p.game_id
        WHERE e.review_decision IN ('CC', 'CNC', 'IC', 'INC')
        """,
        conn,
    )


def prepare_dataset(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["call_family"] = out["call_type"].map(call_family)
    out["decision_kind"] = out["review_decision"].map(
        {"CC": "call", "IC": "call", "CNC": "non_call", "INC": "non_call"}
    )
    out["clock_seconds"] = out["game_clock"].map(clock_seconds)
    out["clock_bucket"] = out["clock_seconds"].map(clock_bucket)
    out["period_bucket"] = out["period"].map(lambda value: "OT" if str(value).upper() != "Q4" else "Q4")
    out["monitoring_type"] = out["call_type"].map(monitoring_type)
    out["call_type_grouped"] = group_rare_values(out["call_type"], min_count=20)
    out["days_rest_capped"] = out["days_rest"].clip(0, 7)
    out["travel_miles_last_7k"] = out["travel_miles_last_7_days"] / 1000
    out["back_to_back"] = out["back_to_back"].fillna(0).astype(int)
    out = out.dropna(subset=FEATURE_COLUMNS + ["incorrect", "game_id"]).copy()
    out["incorrect"] = out["incorrect"].astype(int)
    return out


def build_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", min_frequency=10, sparse_output=False),
                CATEGORICAL_FEATURES,
            ),
            ("numeric", StandardScaler(), NUMERIC_FEATURES),
        ],
        verbose_feature_names_out=False,
    )
    model = LogisticRegression(max_iter=2000, C=0.5)
    return Pipeline([("preprocess", preprocessor), ("model", model)])


def split_by_game(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
    train_index, test_index = next(
        splitter.split(df, df["incorrect"], groups=df["game_id"])
    )
    return df.iloc[train_index].copy(), df.iloc[test_index].copy()


def build_report(
    df: pd.DataFrame,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    test_pred: pd.Series,
    pipeline: Pipeline,
) -> str:
    baseline = float(test_df["incorrect"].mean())
    metrics = {
        "roc_auc": roc_auc_score(test_df["incorrect"], test_pred),
        "avg_precision": average_precision_score(test_df["incorrect"], test_pred),
        "brier": brier_score_loss(test_df["incorrect"], test_pred),
        "log_loss": log_loss(test_df["incorrect"], test_pred),
    }
    lift_table = risk_lift_table(test_df, test_pred)
    calibration_table = calibration_by_decile(test_df, test_pred)
    coefficient_table = top_positive_coefficients(pipeline)

    lines = [
        "# Post-Event L2M Bad-Call Risk Model",
        "",
        "## Headline",
        "",
        f"- Events available: **{len(df):,}**",
        f"- Train events: **{len(train_df):,}**",
        f"- Test events: **{len(test_df):,}**",
        f"- Test baseline error rate: **{baseline:.1%}**",
        f"- ROC AUC: **{metrics['roc_auc']:.3f}**",
        f"- Average precision: **{metrics['avg_precision']:.3f}**",
        f"- Brier score: **{metrics['brier']:.4f}**",
        f"- Log loss: **{metrics['log_loss']:.4f}**",
        f"- Decision: **{decision(metrics, lift_table, baseline)}**",
        "",
        "## Risk Lift",
        "",
        dataframe_to_markdown(lift_table),
        "",
        "## Calibration By Risk Decile",
        "",
        dataframe_to_markdown(calibration_table),
        "",
        "## Strongest Positive Risk Features",
        "",
        dataframe_to_markdown(coefficient_table.head(25)),
        "",
        "## Interpretation",
        "",
        interpretation(metrics, lift_table, baseline),
        "",
    ]
    return "\n".join(lines)


def risk_lift_table(test_df: pd.DataFrame, predictions) -> pd.DataFrame:
    scored = test_df.copy()
    scored["predicted_error_probability"] = predictions
    scored = scored.sort_values("predicted_error_probability", ascending=False)
    total_incorrect = scored["incorrect"].sum()
    rows = []
    for share in [0.05, 0.10, 0.20, 0.33]:
        top = scored.head(max(1, int(len(scored) * share)))
        rows.append(
            {
                "risk_bucket": f"top_{int(share * 100)}pct",
                "events": len(top),
                "incorrect": int(top["incorrect"].sum()),
                "observed_error_rate": top["incorrect"].mean(),
                "lift_vs_baseline": top["incorrect"].mean() / scored["incorrect"].mean(),
                "share_of_all_errors_captured": top["incorrect"].sum() / total_incorrect,
                "avg_predicted_probability": top["predicted_error_probability"].mean(),
            }
        )
    return pd.DataFrame(rows)


def calibration_by_decile(test_df: pd.DataFrame, predictions) -> pd.DataFrame:
    scored = test_df.copy()
    scored["predicted_error_probability"] = predictions
    scored["risk_decile"] = pd.qcut(
        scored["predicted_error_probability"].rank(method="first"),
        10,
        labels=[f"D{i}" for i in range(1, 11)],
    )
    return (
        scored.groupby("risk_decile", observed=False)
        .agg(
            events=("incorrect", "size"),
            incorrect=("incorrect", "sum"),
            observed_error_rate=("incorrect", "mean"),
            avg_predicted_probability=("predicted_error_probability", "mean"),
        )
        .reset_index()
        .sort_values("risk_decile", ascending=False)
    )


def top_positive_coefficients(pipeline: Pipeline) -> pd.DataFrame:
    preprocessor = pipeline.named_steps["preprocess"]
    model = pipeline.named_steps["model"]
    feature_names = preprocessor.get_feature_names_out()
    coefficients = pd.DataFrame(
        {
            "feature": feature_names,
            "coefficient": model.coef_[0],
        }
    )
    coefficients["odds_ratio"] = coefficients["coefficient"].map(lambda value: __import__("math").exp(value))
    return coefficients.sort_values("coefficient", ascending=False)


def decision(metrics: dict, lift_table: pd.DataFrame, baseline: float) -> str:
    top_10_rate = float(
        lift_table.loc[lift_table["risk_bucket"] == "top_10pct", "observed_error_rate"].iloc[0]
    )
    if metrics["roc_auc"] >= 0.70 and top_10_rate >= baseline * 2:
        return "usable post-event risk ranking"
    if metrics["roc_auc"] >= 0.62 and top_10_rate >= baseline * 1.5:
        return "directionally useful, needs more seasons"
    return "weak ranking; context taxonomy helps more than prediction"


def interpretation(metrics: dict, lift_table: pd.DataFrame, baseline: float) -> str:
    top_10 = lift_table.loc[lift_table["risk_bucket"] == "top_10pct"].iloc[0]
    return (
        "This model is designed to rank reviewed L2M events by structural error risk, "
        "not to predict every bad call perfectly. The key question is whether the "
        f"top-risk bucket beats the held-out baseline of {baseline:.1%}. In the top "
        f"10% of scored events, the observed error rate was {top_10['observed_error_rate']:.1%}, "
        f"a {top_10['lift_vs_baseline']:.1f}x lift."
    )


def call_family(value: str | None) -> str:
    if not value:
        return "Unknown"
    return value.split(":", 1)[0].strip()


def monitoring_type(value: str | None) -> str:
    text = str(value or "").lower()
    if any(token in text for token in ["3 second", "5 second", "8 second", "24 second", "lane"]):
        return "timing_count"
    if any(token in text for token in ["out-of-bounds", "out of bounds", "stepped", "traveling", "backcourt"]):
        return "possession_boundary"
    if any(token in text for token in ["defense 3 second", "away from play", "loose ball", "offensive"]):
        return "continuous_off_ball"
    if "foul" in text:
        return "contact_foul"
    return "other"


def clock_seconds(value: str | None) -> float | None:
    if not value:
        return None
    match = re.match(r"(\d+):(\d+(?:\.\d+)?)", str(value))
    if not match:
        return None
    return float(match.group(1)) * 60 + float(match.group(2))


def clock_bucket(value: float | None) -> str:
    if value is None:
        return "unknown"
    if value <= 30:
        return "00-30s"
    if value <= 60:
        return "31-60s"
    if value <= 90:
        return "61-90s"
    return "91-120s"


def group_rare_values(series: pd.Series, min_count: int) -> pd.Series:
    counts = series.value_counts(dropna=False)
    return series.where(series.map(counts).fillna(0) >= min_count, "Other")


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    formatted = df.copy()
    for column in formatted.columns:
        if column.endswith("rate") or column in {
            "share_of_all_errors_captured",
            "avg_predicted_probability",
            "observed_error_rate",
        }:
            formatted[column] = formatted[column].map(lambda value: f"{value:.1%}")
        elif column in {"lift_vs_baseline", "coefficient", "odds_ratio"}:
            formatted[column] = formatted[column].map(lambda value: f"{value:.3f}")
    headers = list(formatted.columns)
    rows = formatted.astype(str).values.tolist()
    widths = [
        max(len(str(header)), *(len(row[index]) for row in rows))
        for index, header in enumerate(headers)
    ]
    lines = [
        "| " + " | ".join(str(header).ljust(widths[index]) for index, header in enumerate(headers)) + " |",
        "| " + " | ".join("-" * width for width in widths) + " |",
    ]
    for row in rows:
        lines.append(
            "| " + " | ".join(row[index].ljust(widths[index]) for index in range(len(headers))) + " |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    main()

