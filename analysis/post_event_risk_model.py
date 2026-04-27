#!/usr/bin/env python3
"""Train a post-event L2M bad-call risk model."""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path
import sys

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from referee_fatigue.db import connect, create_referee_tables
from referee_fatigue.taxonomy import call_family, classify


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train post-event L2M risk model")
    parser.add_argument("--db-path", default="data/nba_stats.db")
    parser.add_argument("--output", default="results/post_event_risk_model_report.md")
    parser.add_argument("--predictions", default="results/post_event_high_risk_events.csv")
    parser.add_argument(
        "--mode",
        choices=["random", "season-holdout", "rolling"],
        default="random",
        help="Validation split strategy.",
    )
    parser.add_argument("--holdout-season")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    conn = connect(PROJECT_ROOT / args.db_path)
    create_referee_tables(conn)
    df = prepare_dataset(load_event_data(conn))
    if args.mode == "rolling":
        rolling_table = rolling_season_evaluation(df)
        pipeline = build_pipeline()
        pipeline.fit(df[FEATURE_COLUMNS], df["incorrect"])
        full_pred = pipeline.predict_proba(df[FEATURE_COLUMNS])[:, 1]
        if rolling_table.empty:
            train_df, test_df = split_dataset(df, "random")
            fallback_pipeline = build_pipeline()
            fallback_pipeline.fit(train_df[FEATURE_COLUMNS], train_df["incorrect"])
            test_pred = fallback_pipeline.predict_proba(test_df[FEATURE_COLUMNS])[:, 1]
            report = build_report(
                df,
                train_df,
                test_df,
                test_pred,
                fallback_pipeline,
                "rolling unavailable; random split fallback",
            )
            report += "\n\n## Rolling Season Holdout\n\n"
            report += rolling_interpretation(rolling_table) + "\n"
            write_season_holdout_table(rolling_table)
        else:
            report = build_rolling_report(df, rolling_table)
    else:
        train_df, test_df = split_dataset(df, args.mode, args.holdout_season)
        pipeline = build_pipeline()
        pipeline.fit(train_df[FEATURE_COLUMNS], train_df["incorrect"])

        test_pred = pipeline.predict_proba(test_df[FEATURE_COLUMNS])[:, 1]
        full_pred = pipeline.predict_proba(df[FEATURE_COLUMNS])[:, 1]
        report = build_report(df, train_df, test_df, test_pred, pipeline, args.mode)

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
    "score_state",
    "possession_context",
    "scramble_context",
    "sequence_context_grouped",
]

NUMERIC_FEATURES = [
    "clock_seconds",
    "score_margin_abs",
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
            e.season,
            e.period,
            e.game_clock,
            e.call_type,
            e.review_decision,
            e.incorrect,
            e.committing_player,
            e.disadvantaged_player,
            e.comment,
            c.score_margin,
            c.score_margin_abs,
            c.tied_game,
            c.one_possession,
            c.trailing_team_possession,
            c.rebound_scramble_indicator,
            c.sequence_context,
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
        LEFT JOIN l2m_event_context c
            ON e.game_id = c.game_id AND e.event_index = c.event_index
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
    out["monitoring_type"] = out.apply(
        lambda row: classify(row["call_type"], row["review_decision"]),
        axis=1,
    )
    out["call_type_grouped"] = group_rare_values(out["call_type"].fillna("Unknown"), min_count=20)
    out["days_rest_capped"] = pd.to_numeric(out.get("days_rest"), errors="coerce").clip(0, 7)
    out["travel_miles_last_7k"] = pd.to_numeric(
        out.get("travel_miles_last_7_days"), errors="coerce"
    ) / 1000
    out["back_to_back"] = pd.to_numeric(out.get("back_to_back"), errors="coerce").fillna(0).astype(int)
    out["score_margin_abs"] = pd.to_numeric(out.get("score_margin_abs"), errors="coerce")
    if out["score_margin_abs"].isna().all() and "score_margin" in out:
        out["score_margin_abs"] = pd.to_numeric(out["score_margin"], errors="coerce").abs()
    out["score_state"] = out["score_margin_abs"].map(score_state)
    out["possession_context"] = out.get("trailing_team_possession", pd.Series(index=out.index)).map(
        boolean_context("trailing_team_possession")
    )
    out["scramble_context"] = out.get("rebound_scramble_indicator", pd.Series(index=out.index)).map(
        boolean_context("rebound_scramble")
    )
    out["sequence_context_grouped"] = group_rare_values(
        out.get("sequence_context", pd.Series(index=out.index)).fillna("unknown"),
        min_count=20,
    )
    for column in CATEGORICAL_FEATURES:
        out[column] = out[column].fillna("unknown").astype(str)
    for column in NUMERIC_FEATURES:
        out[column] = pd.to_numeric(out[column], errors="coerce")
    out = out.dropna(subset=["incorrect", "game_id", "season"]).copy()
    out["incorrect"] = out["incorrect"].astype(int)
    return out


def build_pipeline(
    categorical_features: list[str] | None = None,
    numeric_features: list[str] | None = None,
) -> Pipeline:
    categorical_features = categorical_features if categorical_features is not None else CATEGORICAL_FEATURES
    numeric_features = numeric_features if numeric_features is not None else NUMERIC_FEATURES
    transformers = []
    if categorical_features:
        transformers.append(
            (
                "categorical",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="constant", fill_value="unknown")),
                        ("onehot", make_one_hot_encoder()),
                    ]
                ),
                categorical_features,
            )
        )
    if numeric_features:
        transformers.append(
            (
                "numeric",
                Pipeline(
                    [
                        ("impute", make_numeric_imputer()),
                        ("scale", StandardScaler()),
                    ]
                ),
                numeric_features,
            )
        )
    preprocessor = ColumnTransformer(transformers=transformers, verbose_feature_names_out=False)
    model = LogisticRegression(max_iter=2000, C=0.5)
    return Pipeline([("preprocess", preprocessor), ("model", model)])


def make_one_hot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", min_frequency=10, sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", min_frequency=10, sparse=False)


def make_numeric_imputer() -> SimpleImputer:
    try:
        return SimpleImputer(strategy="constant", fill_value=0, keep_empty_features=True)
    except TypeError:
        return SimpleImputer(strategy="constant", fill_value=0)


def split_dataset(
    df: pd.DataFrame,
    mode: str,
    holdout_season: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if mode == "season-holdout":
        if holdout_season is None:
            seasons = sorted(df["season"].dropna().unique(), key=season_sort_key)
            if len(seasons) < 2:
                raise ValueError("season-holdout mode needs at least two seasons or --holdout-season")
            holdout_season = seasons[-1]
        train_df = df[df["season"].map(season_sort_key) < season_sort_key(holdout_season)].copy()
        test_df = df[df["season"] == holdout_season].copy()
        if train_df.empty or test_df.empty:
            raise ValueError(f"No train/test rows available for holdout season {holdout_season}")
        return train_df, test_df

    splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
    train_index, test_index = next(
        splitter.split(df, df["incorrect"], groups=df["game_id"])
    )
    return df.iloc[train_index].copy(), df.iloc[test_index].copy()


def rolling_season_evaluation(
    df: pd.DataFrame,
    categorical_features: list[str] | None = None,
    numeric_features: list[str] | None = None,
) -> pd.DataFrame:
    categorical_features = categorical_features if categorical_features is not None else CATEGORICAL_FEATURES
    numeric_features = numeric_features if numeric_features is not None else NUMERIC_FEATURES
    rows = []
    seasons = sorted(df["season"].dropna().unique(), key=season_sort_key)
    for holdout_season in seasons[1:]:
        train_df = df[df["season"].map(season_sort_key) < season_sort_key(holdout_season)].copy()
        test_df = df[df["season"] == holdout_season].copy()
        if train_df.empty or test_df.empty or train_df["incorrect"].nunique() < 2:
            continue
        pipeline = build_pipeline(categorical_features, numeric_features)
        feature_columns = categorical_features + numeric_features
        pipeline.fit(train_df[feature_columns], train_df["incorrect"])
        predictions = pipeline.predict_proba(test_df[feature_columns])[:, 1]
        metrics = model_metrics(test_df["incorrect"], predictions)
        lift_table = risk_lift_table(test_df, predictions)
        top_10 = lift_table.loc[lift_table["risk_bucket"] == "top_10pct"].iloc[0]
        rows.append(
            {
                "holdout_season": holdout_season,
                "train_seasons": season_range(train_df),
                "train_events": len(train_df),
                "test_events": len(test_df),
                "test_incorrect": int(test_df["incorrect"].sum()),
                "baseline_error_rate": test_df["incorrect"].mean(),
                "roc_auc": metrics["roc_auc"],
                "avg_precision": metrics["avg_precision"],
                "top_10_error_rate": top_10["observed_error_rate"],
                "top_10_lift": top_10["lift_vs_baseline"],
                "top_10_error_capture": top_10["share_of_all_errors_captured"],
            }
        )
    return pd.DataFrame(rows)


def build_rolling_report(df: pd.DataFrame, rolling_table: pd.DataFrame) -> str:
    write_season_holdout_table(rolling_table)
    table_markdown = dataframe_to_markdown(rolling_table)
    lines = [
        "# Post-Event L2M Bad-Call Risk Model",
        "",
        "## Rolling Season Holdout",
        "",
        f"- Events available: **{len(df):,}**",
        f"- Seasons available: **{season_range(df)}**",
        f"- Holdout seasons evaluated: **{len(rolling_table):,}**",
        "",
        table_markdown,
        "",
        "## Interpretation",
        "",
        rolling_interpretation(rolling_table),
        "",
    ]
    return "\n".join(lines)


def write_season_holdout_table(rolling_table: pd.DataFrame) -> None:
    output_path = PROJECT_ROOT / "results" / "season_holdout_lift_table.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(["# Season Holdout Lift Table", "", dataframe_to_markdown(rolling_table), ""]),
        encoding="utf-8",
    )


def build_report(
    df: pd.DataFrame,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    test_pred: pd.Series,
    pipeline: Pipeline,
    mode: str,
) -> str:
    baseline = float(test_df["incorrect"].mean())
    metrics = model_metrics(test_df["incorrect"], test_pred)
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
        f"- Validation mode: **{mode}**",
        f"- Train seasons: **{season_range(train_df)}**",
        f"- Test seasons: **{season_range(test_df)}**",
        f"- Test baseline error rate: **{baseline:.1%}**",
        f"- ROC AUC: **{format_metric(metrics['roc_auc'], 3)}**",
        f"- Average precision: **{format_metric(metrics['avg_precision'], 3)}**",
        f"- Brier score: **{format_metric(metrics['brier'], 4)}**",
        f"- Log loss: **{format_metric(metrics['log_loss'], 4)}**",
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
                "lift_vs_baseline": safe_divide(top["incorrect"].mean(), scored["incorrect"].mean()),
                "share_of_all_errors_captured": safe_divide(top["incorrect"].sum(), total_incorrect),
                "avg_predicted_probability": top["predicted_error_probability"].mean(),
            }
        )
    return pd.DataFrame(rows)


def model_metrics(y_true: pd.Series, predictions) -> dict[str, float | None]:
    has_both_classes = pd.Series(y_true).nunique() == 2
    return {
        "roc_auc": roc_auc_score(y_true, predictions) if has_both_classes else None,
        "avg_precision": average_precision_score(y_true, predictions) if has_both_classes else None,
        "brier": brier_score_loss(y_true, predictions),
        "log_loss": log_loss(y_true, predictions, labels=[0, 1]) if has_both_classes else None,
    }


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
    coefficients["odds_ratio"] = coefficients["coefficient"].map(lambda value: math.exp(value))
    return coefficients.sort_values("coefficient", ascending=False)


def decision(metrics: dict, lift_table: pd.DataFrame, baseline: float) -> str:
    top_10_rate = float(
        lift_table.loc[lift_table["risk_bucket"] == "top_10pct", "observed_error_rate"].iloc[0]
    )
    roc_auc = metrics.get("roc_auc")
    if roc_auc is not None and roc_auc >= 0.70 and top_10_rate >= baseline * 2:
        return "usable post-event risk ranking"
    if roc_auc is not None and roc_auc >= 0.62 and top_10_rate >= baseline * 1.5:
        return "directionally useful, needs more seasons"
    return "weak ranking; context taxonomy helps more than prediction"


def interpretation(metrics: dict, lift_table: pd.DataFrame, baseline: float) -> str:
    top_10 = lift_table.loc[lift_table["risk_bucket"] == "top_10pct"].iloc[0]
    lift = top_10["lift_vs_baseline"]
    lift_text = "n/a" if lift is None or pd.isna(lift) else f"{lift:.1f}x"
    return (
        "This model is designed to rank reviewed L2M events by structural error risk, "
        "not to predict every bad call perfectly. The key question is whether the "
        f"top-risk bucket beats the held-out baseline of {baseline:.1%}. In the top "
        f"10% of scored events, the observed error rate was {top_10['observed_error_rate']:.1%}, "
        f"a {lift_text} lift."
    )


def rolling_interpretation(rolling_table: pd.DataFrame) -> str:
    if rolling_table.empty:
        return (
            "Rolling season holdout could not run because the database does not yet "
            "contain at least two seasons with usable L2M outcomes."
        )
    mean_lift = rolling_table["top_10_lift"].dropna().mean()
    if pd.isna(mean_lift):
        return "Rolling holdouts ran, but top-decile lift was not estimable."
    return (
        "The Sloan-relevant test is whether the top structural-risk decile is "
        f"consistently above baseline in future seasons. Mean top-decile lift "
        f"across evaluated holdouts was {mean_lift:.1f}x."
    )


def score_state(value: float | None) -> str:
    if pd.isna(value):
        return "unknown"
    if value == 0:
        return "tied"
    if value <= 3:
        return "one_possession"
    if value <= 10:
        return "two_to_three_possessions"
    return "larger_margin"


def boolean_context(label: str):
    def classify_value(value) -> str:
        if pd.isna(value):
            return "unknown"
        return label if int(value) == 1 else f"not_{label}"

    return classify_value


def season_sort_key(season: str | None) -> int:
    if not season:
        return -1
    return int(str(season).split("-", 1)[0])


def season_range(df: pd.DataFrame) -> str:
    seasons = sorted(df["season"].dropna().unique(), key=season_sort_key)
    if not seasons:
        return "n/a"
    if len(seasons) == 1:
        return str(seasons[0])
    return f"{seasons[0]} to {seasons[-1]}"


def safe_divide(numerator, denominator) -> float | None:
    if denominator in (0, None) or pd.isna(denominator):
        return None
    return float(numerator) / float(denominator)


def format_metric(value: float | None, decimals: int) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{value:.{decimals}f}"


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
    if df.empty:
        return "No rows available."
    formatted = df.copy()
    for column in formatted.columns:
        if column.endswith("rate") or column in {
            "share_of_all_errors_captured",
            "avg_predicted_probability",
            "observed_error_rate",
            "baseline_error_rate",
            "top_10_error_rate",
            "top_10_error_capture",
            "mean_top_10_error_rate",
            "mean_error_capture",
        }:
            formatted[column] = formatted[column].map(
                lambda value: "n/a" if pd.isna(value) else f"{value:.1%}"
            )
        elif column in {
            "lift_vs_baseline",
            "coefficient",
            "odds_ratio",
            "roc_auc",
            "avg_precision",
            "top_10_lift",
            "mean_roc_auc",
            "mean_top_10_lift",
        }:
            formatted[column] = formatted[column].map(
                lambda value: "n/a" if pd.isna(value) else f"{value:.3f}"
            )
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

