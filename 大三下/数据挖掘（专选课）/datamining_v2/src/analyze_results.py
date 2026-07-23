import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


def ensure_out(out_dir):
    Path(out_dir).mkdir(parents=True, exist_ok=True)


def mode_share(values):
    counts = values.value_counts(dropna=True)
    if counts.empty:
        return None
    return counts.iloc[0] / counts.sum()


def mode_value(values):
    counts = values.value_counts(dropna=True)
    if counts.empty:
        return None
    return counts.index[0]


def consistency_by_model(df):
    rows = []
    group_cols = ["model_key", "scenario_id"]
    for (model_key, scenario_id), group in df.groupby(group_cols):
        judgments = group["final_judgment"].dropna()
        rows.append(
            {
                "model_key": model_key,
                "scenario_id": scenario_id,
                "n": len(group),
                "unique_judgments": judgments.nunique(),
                "majority_share": mode_share(judgments),
            }
        )
    return pd.DataFrame(rows)


def noise_flip_rate(df):
    baseline = (
        df[df["perturbation_type"] == "none"]
        .groupby(["model_key", "scenario_id", "level"], dropna=False)["final_judgment"]
        .agg(mode_value)
        .reset_index()
        .rename(columns={"final_judgment": "baseline_judgment"})
    )

    changed = df[df["perturbation_type"] != "none"].merge(
        baseline, on=["model_key", "scenario_id", "level"], how="left"
    )
    changed["flip"] = (
        changed["baseline_judgment"].notna()
        & changed["final_judgment"].notna()
        & (changed["baseline_judgment"] != changed["final_judgment"])
    )

    return (
        changed.groupby(["model_key", "perturbation_type"], dropna=False)
        .agg(samples=("run_id", "count"), flip_rate=("flip", "mean"))
        .reset_index()
    )


def feature_summary(df):
    numeric_cols = [
        "is_correct",
        "judgment_flip",
        "reasoning_step_count",
        "uses_formula",
        "uses_coordinate_system",
        "spatial_modeling_depth",
    ]
    existing = [col for col in numeric_cols if col in df.columns]
    for col in existing:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    summary = (
        df.groupby(["model_key", "level"], dropna=False)[existing]
        .mean(numeric_only=True)
        .reset_index()
    )
    return summary


def feature_summary_by_dimension(df, dimension):
    if dimension not in df.columns:
        return pd.DataFrame()

    numeric_cols = [
        "is_correct",
        "judgment_flip",
        "reasoning_step_count",
        "uses_formula",
        "uses_coordinate_system",
        "spatial_modeling_depth",
    ]
    existing = [col for col in numeric_cols if col in df.columns]
    tmp = df.copy()
    for col in existing:
        tmp[col] = pd.to_numeric(tmp[col], errors="coerce")

    return (
        tmp.groupby(["model_key", dimension], dropna=False)[existing]
        .mean(numeric_only=True)
        .reset_index()
    )


def judgment_counts_by_dimension(df, dimension):
    if dimension not in df.columns:
        return pd.DataFrame()
    return (
        df.groupby(["model_key", dimension, "final_judgment"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["model_key", dimension, "count"], ascending=[True, True, False])
    )


def failure_mode_counts(df):
    if "failure_mode" not in df.columns:
        return pd.DataFrame()
    return (
        df.groupby(["model_key", "failure_mode"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["model_key", "count"], ascending=[True, False])
    )


def plot_heatmap(table, index, columns, values, title, out_path):
    pivot = table.pivot(index=index, columns=columns, values=values)
    plt.figure(figsize=(9, 5))
    sns.heatmap(pivot, annot=True, cmap="viridis", vmin=0, vmax=1)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def cluster_models(df, out_dir):
    numeric_cols = [
        "is_correct",
        "judgment_flip",
        "reasoning_step_count",
        "uses_formula",
        "uses_coordinate_system",
        "spatial_modeling_depth",
    ]
    existing = [col for col in numeric_cols if col in df.columns]
    if not existing or df["model_key"].nunique() < 2:
        return pd.DataFrame()

    tmp = df.copy()
    for col in existing:
        tmp[col] = pd.to_numeric(tmp[col], errors="coerce")

    features = tmp.groupby("model_key")[existing].mean(numeric_only=True).fillna(0)
    n_clusters = min(3, len(features))
    scaled = StandardScaler().fit_transform(features)
    labels = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto").fit_predict(scaled)
    result = features.reset_index()
    result["cluster"] = labels
    result.to_csv(Path(out_dir) / "model_clusters.csv", index=False, encoding="utf-8-sig")
    return result


def main():
    parser = argparse.ArgumentParser(description="Analyze annotated LLM behavior data.")
    parser.add_argument("--input", default="data/processed/annotated_responses.csv")
    parser.add_argument("--out", default="outputs")
    args = parser.parse_args()

    ensure_out(args.out)
    df = pd.read_csv(args.input, encoding="utf-8-sig")

    consistency = consistency_by_model(df)
    consistency.to_csv(Path(args.out) / "consistency_by_model.csv", index=False, encoding="utf-8-sig")

    flips = noise_flip_rate(df)
    flips.to_csv(Path(args.out) / "noise_flip_rate.csv", index=False, encoding="utf-8-sig")

    summary = feature_summary(df)
    summary.to_csv(Path(args.out) / "feature_summary_by_level.csv", index=False, encoding="utf-8-sig")

    for dimension in ["geometry_type", "obstacle_type"]:
        dimension_summary = feature_summary_by_dimension(df, dimension)
        if not dimension_summary.empty:
            dimension_summary.to_csv(
                Path(args.out) / f"feature_summary_by_{dimension}.csv",
                index=False,
                encoding="utf-8-sig",
            )

        judgment_counts = judgment_counts_by_dimension(df, dimension)
        if not judgment_counts.empty:
            judgment_counts.to_csv(
                Path(args.out) / f"judgment_counts_by_{dimension}.csv",
                index=False,
                encoding="utf-8-sig",
            )

    failures = failure_mode_counts(df)
    failures.to_csv(Path(args.out) / "failure_mode_counts.csv", index=False, encoding="utf-8-sig")

    clusters = cluster_models(df, args.out)

    if not consistency.empty:
        plot_heatmap(
            consistency,
            index="model_key",
            columns="scenario_id",
            values="majority_share",
            title="Judgment Consistency Majority Share",
            out_path=Path(args.out) / "consistency_heatmap.png",
        )

    if not flips.empty:
        plot_heatmap(
            flips,
            index="model_key",
            columns="perturbation_type",
            values="flip_rate",
            title="Noise-Induced Judgment Flip Rate",
            out_path=Path(args.out) / "noise_flip_heatmap.png",
        )

    print(f"Saved analysis outputs to {args.out}")
    if not clusters.empty:
        print("Model clustering completed.")


if __name__ == "__main__":
    main()
