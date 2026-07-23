from __future__ import annotations

"""
Try HLS-friendly robust EyeFeature feature sets and binary SVM variants locally.

This script is intentionally exploratory. It does not modify HLS. It builds
windowed datasets from a rich frame-level CSV, evaluates feature sets with
leave-one-session-out validation, and writes ranked results.
"""

import argparse
import json
import math
import re
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.svm import LinearSVC, SVC

LABEL_NAMES = ["non_closed", "closed"]


FEATURE_SETS: Dict[str, List[str]] = {
    "base2": ["robust_f0", "robust_f1"],
    "avg2": ["avg_f0", "avg_f1"],
    "avg4_dark": ["avg_f0", "avg_f1", "avg_dark_low", "avg_dark_high"],
    "avg6_shape": ["avg_f0", "avg_f1", "avg_dark_high", "avg_col_frac_high", "avg_row_frac_high", "avg_row_run_high"],
    "avg8_runs": [
        "avg_f0", "avg_f1", "avg_dark_low", "avg_dark_high",
        "avg_col_frac_low", "avg_col_frac_high", "avg_row_run_low", "avg_row_run_high",
    ],
    "avg10_robust": [
        "avg_f0", "avg_f1", "avg_dark_low", "avg_dark_high",
        "avg_col_frac_low", "avg_col_frac_high", "avg_row_frac_low", "avg_row_frac_high",
        "avg_row_run_low", "avg_row_run_high",
    ],
    "avg12_contrast": [
        "avg_f0", "avg_f1", "avg_dark_low", "avg_dark_high",
        "avg_col_frac_low", "avg_col_frac_high", "avg_row_frac_low", "avg_row_frac_high",
        "avg_row_run_low", "avg_row_run_high", "avg_contrast", "avg_std_gray",
    ],
    "lr4": ["left_f0", "right_f0", "left_f1", "right_f1"],
    "lr8_shape": [
        "left_f0", "right_f0", "left_f1", "right_f1",
        "left_dark_high", "right_dark_high", "left_row_run_high", "right_row_run_high",
    ],
    "lr12_shape": [
        "left_f0", "right_f0", "left_f1", "right_f1",
        "left_dark_low", "right_dark_low", "left_dark_high", "right_dark_high",
        "left_col_frac_high", "right_col_frac_high", "left_row_run_high", "right_row_run_high",
    ],
    "lr20_rich": [
        "left_f0", "right_f0", "left_f1", "right_f1",
        "left_dark_low", "right_dark_low", "left_dark_high", "right_dark_high",
        "left_col_frac_low", "right_col_frac_low", "left_col_frac_high", "right_col_frac_high",
        "left_row_frac_low", "right_row_frac_low", "left_row_frac_high", "right_row_frac_high",
        "left_row_run_low", "right_row_run_low", "left_row_run_high", "right_row_run_high",
    ],
    "avg_diff8": [
        "avg_f0", "avg_f1", "avg_dark_high", "avg_row_run_high",
        "diff_f0", "diff_f1", "diff_dark_high", "diff_row_run_high",
    ],
    "avg_abslight14": [
        "avg_f0", "avg_f1", "avg_dark_low", "avg_dark_high",
        "avg_col_frac_low", "avg_col_frac_high", "avg_row_frac_low", "avg_row_frac_high",
        "avg_row_run_low", "avg_row_run_high", "avg_contrast", "avg_q_dark",
        "avg_q_ref", "avg_mean_gray",
    ],
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Experiment with robust EyeFeature feature sets and SVM variants.")
    p.add_argument("--frame_csv", required=True)
    p.add_argument("--out_dir", default="work_experiment_robust_feature_svm")
    p.add_argument("--window_size", type=int, default=15)
    p.add_argument("--central_size", type=int, default=7)
    p.add_argument("--min_same_label_in_central", type=int, default=7)
    p.add_argument("--valid_columns", default="det_ok,eye_valid")
    p.add_argument("--feature_sets", default="all", help="all or comma-separated feature-set names")
    p.add_argument("--linear_C", default="0.001,0.003,0.01,0.03,0.1,0.3,1.0")
    p.add_argument("--poly_C", default="0.001,0.003,0.01")
    p.add_argument("--max_poly_input_dim", type=int, default=120)
    p.add_argument("--include_rbf", action="store_true")
    p.add_argument("--rbf_C", default="1.0,10.0")
    p.add_argument("--tune_threshold", action="store_true", default=True)
    p.add_argument("--no_tune_threshold", dest="tune_threshold", action="store_false")
    p.add_argument("--random_seed", type=int, default=42)
    p.add_argument("--save_best_model", action="store_true", default=True)
    return p.parse_args()


def parse_list(s: str) -> List[str]:
    return [x.strip() for x in str(s).split(",") if x.strip()]


def parse_float_list(s: str) -> List[float]:
    return [float(x) for x in parse_list(s)]


def session_from_source_path(path: str) -> str:
    p = str(path).replace("\\", "/")
    m = re.search(r"raw_robust_dataset_board/([^/]+)/", p)
    if m:
        return m.group(1)
    return Path(p).parent.parent.name if p else "unknown"


def is_consecutive_frames(frame_ids: np.ndarray) -> bool:
    if len(frame_ids) <= 1:
        return True
    return bool(np.all(np.diff(frame_ids) == 1))


def build_windows(df: pd.DataFrame, feature_names: Sequence[str], valid_columns: Sequence[str], args: argparse.Namespace) -> pd.DataFrame:
    half_w = int(args.window_size) // 2
    half_c = int(args.central_size) // 2
    min_same = int(args.min_same_label_in_central)
    rows: List[dict] = []
    need = ["video_id", "frame_id", "label", "label_name", "source_path"] + list(feature_names) + list(valid_columns)
    missing = [c for c in need if c not in df.columns]
    if missing:
        raise ValueError(f"frame csv missing columns: {missing}")

    work = df[need].copy()
    for c in ["frame_id", "label"] + list(feature_names) + list(valid_columns):
        work[c] = pd.to_numeric(work[c], errors="coerce")
    work = work.sort_values(["video_id", "frame_id"]).reset_index(drop=True)

    for video_id, dfv in work.groupby("video_id", sort=True):
        dfv = dfv.sort_values("frame_id").reset_index(drop=True)
        for center_idx in range(half_w, len(dfv) - half_w):
            win = dfv.iloc[center_idx - half_w:center_idx + half_w + 1]
            if not is_consecutive_frames(win["frame_id"].to_numpy(dtype=int)):
                continue
            if win[list(feature_names)].isna().any().any():
                continue
            bad = False
            for c in valid_columns:
                if c and (win[c].isna().any() or (win[c] != 1).any()):
                    bad = True
                    break
            if bad:
                continue

            central = win.iloc[half_w - half_c:half_w + half_c + 1]
            counts = central["label"].astype(int).value_counts().to_dict()
            label = max(counts, key=lambda k: counts[k])
            if int(counts[label]) < min_same:
                continue
            row = {
                "video_id": str(video_id),
                "session": session_from_source_path(str(dfv.iloc[center_idx]["source_path"])),
                "center_frame": int(dfv.iloc[center_idx]["frame_id"]),
                "label": int(label),
                "label_name": LABEL_NAMES[int(label)],
            }
            for name in feature_names:
                vals = win[name].to_numpy(dtype=float)
                safe = name.replace("-", "_").replace(".", "_")
                for i, v in enumerate(vals):
                    row[f"{safe}_{i}"] = float(v)
            rows.append(row)
    return pd.DataFrame(rows)


def feature_columns(windows: pd.DataFrame) -> List[str]:
    meta = {"video_id", "session", "center_frame", "label", "label_name"}
    cols = [c for c in windows.columns if c not in meta]

    def key(c: str):
        base, idx = c.rsplit("_", 1)
        return base, int(idx)

    return sorted(cols, key=key)


def threshold_candidates(scores: np.ndarray) -> np.ndarray:
    if scores.size == 0:
        return np.array([0.0])
    qs = np.linspace(0.0, 1.0, 301)
    vals = np.unique(np.quantile(scores, qs))
    if 0.0 not in vals:
        vals = np.unique(np.concatenate([vals, np.array([0.0])]))
    return vals


def choose_threshold(y: np.ndarray, scores: np.ndarray) -> float:
    best = (float("-inf"), 0.0)
    for th in threshold_candidates(scores):
        pred = (scores > th).astype(np.int64)
        bal = balanced_accuracy_score(y, pred)
        if bal > best[0]:
            best = (bal, float(th))
    return best[1]


def make_model(kind: str, C: float, random_seed: int):
    if kind == "linear":
        return make_pipeline(
            StandardScaler(),
            LinearSVC(C=float(C), class_weight="balanced", dual=False, max_iter=80000, random_state=int(random_seed)),
        )
    if kind == "poly2_linear":
        return make_pipeline(
            PolynomialFeatures(degree=2, include_bias=False),
            StandardScaler(),
            LinearSVC(C=float(C), class_weight="balanced", dual=False, max_iter=100000, random_state=int(random_seed)),
        )
    if kind == "rbf":
        return make_pipeline(
            StandardScaler(),
            SVC(C=float(C), kernel="rbf", gamma="scale", class_weight="balanced"),
        )
    raise ValueError(f"unknown model kind: {kind}")


def model_hw_note(kind: str, input_dim: int) -> Tuple[int, str]:
    if kind == "linear":
        return input_dim, f"{input_dim} MACs/window, simple HLS update"
    if kind == "poly2_linear":
        expanded = input_dim + input_dim * (input_dim + 1) // 2
        return expanded, f"{expanded} expanded linear terms; HLS/PS input path must change"
    return -1, "RBF diagnostic only; support vectors usually too costly for PYNQ"


def eval_config(windows: pd.DataFrame, cols: List[str], feature_set: str, model_kind: str, C: float, args: argparse.Namespace) -> Dict[str, object]:
    X = windows[cols].to_numpy(dtype=np.float64)
    y = windows["label"].to_numpy(dtype=np.int64)
    groups = windows["session"].astype(str).to_numpy()
    logo = LeaveOneGroupOut()
    cms: List[np.ndarray] = []
    fold_rows: List[dict] = []
    support_sizes: List[int] = []
    thresholds: List[float] = []

    for train_idx, test_idx in logo.split(X, y, groups):
        model = make_model(model_kind, C, int(args.random_seed))
        model.fit(X[train_idx], y[train_idx])
        if hasattr(model, "decision_function"):
            train_scores = model.decision_function(X[train_idx])
            test_scores = model.decision_function(X[test_idx])
            th = choose_threshold(y[train_idx], train_scores) if bool(args.tune_threshold) else 0.0
            pred = (test_scores > th).astype(np.int64)
        else:
            th = 0.0
            pred = model.predict(X[test_idx])
        thresholds.append(float(th))

        cm = confusion_matrix(y[test_idx], pred, labels=[0, 1])
        cms.append(cm)
        acc = accuracy_score(y[test_idx], pred)
        bal = balanced_accuracy_score(y[test_idx], pred)
        f1 = f1_score(y[test_idx], pred, average="macro", zero_division=0)
        fold_rows.append({
            "feature_set": feature_set,
            "model": model_kind,
            "C": float(C),
            "holdout_session": str(groups[test_idx][0]),
            "samples": int(len(test_idx)),
            "accuracy": float(acc),
            "balanced_accuracy": float(bal),
            "macro_f1": float(f1),
            "threshold": float(th),
            "cm00": int(cm[0, 0]),
            "cm01": int(cm[0, 1]),
            "cm10": int(cm[1, 0]),
            "cm11": int(cm[1, 1]),
        })
        if model_kind == "rbf":
            svc = model.named_steps["svc"]
            support_sizes.append(int(svc.n_support_.sum()))

    cm_total = sum(cms)
    total = int(cm_total.sum())
    false_closed = float(cm_total[0, 1] / cm_total[0].sum()) if cm_total[0].sum() else 0.0
    missed_closed = float(cm_total[1, 0] / cm_total[1].sum()) if cm_total[1].sum() else 0.0
    hw_dim, hw_note = model_hw_note(model_kind, len(cols))
    row = {
        "feature_set": feature_set,
        "model": model_kind,
        "C": float(C),
        "frame_feature_count": int(len(FEATURE_SETS[feature_set])),
        "window_size": int(args.window_size),
        "input_dim": int(len(cols)),
        "hw_dim_or_terms": int(hw_dim),
        "samples": int(len(windows)),
        "sessions": int(len(np.unique(groups))),
        "mean_accuracy": float(np.mean([r["accuracy"] for r in fold_rows])),
        "mean_balanced_accuracy": float(np.mean([r["balanced_accuracy"] for r in fold_rows])),
        "mean_macro_f1": float(np.mean([r["macro_f1"] for r in fold_rows])),
        "micro_accuracy": float(np.trace(cm_total) / total) if total else math.nan,
        "false_closed_rate": false_closed,
        "missed_closed_rate": missed_closed,
        "cm00": int(cm_total[0, 0]),
        "cm01": int(cm_total[0, 1]),
        "cm10": int(cm_total[1, 0]),
        "cm11": int(cm_total[1, 1]),
        "threshold_mean": float(np.mean(thresholds)),
        "support_vectors_mean": float(np.mean(support_sizes)) if support_sizes else 0.0,
        "support_vectors_max": int(max(support_sizes)) if support_sizes else 0,
        "hw_note": hw_note,
    }
    return {"summary": row, "folds": fold_rows}


def fit_and_save_best(windows: pd.DataFrame, cols: List[str], best: pd.Series, out_dir: Path, args: argparse.Namespace) -> None:
    X = windows[cols].to_numpy(dtype=np.float64)
    y = windows["label"].to_numpy(dtype=np.int64)
    model = make_model(str(best["model"]), float(best["C"]), int(args.random_seed))
    model.fit(X, y)
    scores = model.decision_function(X)
    threshold = choose_threshold(y, scores) if bool(args.tune_threshold) else 0.0
    pred = (scores > threshold).astype(np.int64)
    cm = confusion_matrix(y, pred, labels=[0, 1])
    model_dir = out_dir / "best_model"
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_dir / "model.joblib")
    meta = {
        "feature_set": str(best["feature_set"]),
        "model": str(best["model"]),
        "C": float(best["C"]),
        "threshold": float(threshold),
        "feature_cols": cols,
        "frame_features": FEATURE_SETS[str(best["feature_set"])],
        "input_dim": int(len(cols)),
        "all_data_confusion_matrix": cm.tolist(),
        "all_data_accuracy": float(accuracy_score(y, pred)),
        "all_data_balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "note": "Local experiment model. HLS export needs separate fixed-point implementation for non-plain-linear models.",
    }
    (model_dir / "best_config.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(args.frame_csv, dtype={"video_id": str})
    valid_columns = parse_list(args.valid_columns)
    requested_sets = list(FEATURE_SETS.keys()) if args.feature_sets.strip().lower() == "all" else parse_list(args.feature_sets)

    summaries: List[dict] = []
    folds_all: List[dict] = []
    windows_cache: Dict[str, Tuple[pd.DataFrame, List[str]]] = {}

    for feature_set in requested_sets:
        if feature_set not in FEATURE_SETS:
            raise ValueError(f"unknown feature_set={feature_set}. Available: {sorted(FEATURE_SETS)}")
        feats = FEATURE_SETS[feature_set]
        missing = [f for f in feats if f not in df.columns]
        if missing:
            print(f"[SKIP] {feature_set}: missing columns {missing}")
            continue
        windows = build_windows(df, feats, valid_columns, args)
        if windows.empty or windows["session"].nunique() < 2:
            print(f"[SKIP] {feature_set}: insufficient windows/sessions")
            continue
        cols = feature_columns(windows)
        windows_cache[feature_set] = (windows, cols)
        windows.to_csv(out_dir / f"windows_{feature_set}.csv", index=False, encoding="utf-8-sig")
        print(f"[DATA] {feature_set}: windows={len(windows)} input_dim={len(cols)} sessions={windows['session'].nunique()}")

        model_plan: List[Tuple[str, float]] = [("linear", C) for C in parse_float_list(args.linear_C)]
        if len(cols) <= int(args.max_poly_input_dim):
            model_plan += [("poly2_linear", C) for C in parse_float_list(args.poly_C)]
        if bool(args.include_rbf):
            model_plan += [("rbf", C) for C in parse_float_list(args.rbf_C)]

        for model_kind, C in model_plan:
            result = eval_config(windows, cols, feature_set, model_kind, C, args)
            summaries.append(result["summary"])
            folds_all.extend(result["folds"])
            row = result["summary"]
            print(
                f"[EVAL] {feature_set:16s} {model_kind:12s} C={C:g} "
                f"bal={row['mean_balanced_accuracy']:.3f} micro={row['micro_accuracy']:.3f} "
                f"fcr={row['false_closed_rate']:.3f} mcr={row['missed_closed_rate']:.3f} dim={row['hw_dim_or_terms']}"
            )

    if not summaries:
        raise RuntimeError("No experiment results generated")

    res = pd.DataFrame(summaries)
    res = res.sort_values(
        ["mean_balanced_accuracy", "mean_macro_f1", "micro_accuracy"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    folds = pd.DataFrame(folds_all)
    res.to_csv(out_dir / "experiment_results.csv", index=False, encoding="utf-8-sig")
    folds.to_csv(out_dir / "fold_results.csv", index=False, encoding="utf-8-sig")
    best = res.iloc[0]
    (out_dir / "best_summary.json").write_text(best.to_json(indent=2, force_ascii=False), encoding="utf-8")
    print("\n[TOP 10]")
    print(res.head(10)[[
        "feature_set", "model", "C", "frame_feature_count", "input_dim", "hw_dim_or_terms",
        "mean_balanced_accuracy", "micro_accuracy", "false_closed_rate", "missed_closed_rate",
        "hw_note",
    ]].to_string(index=False))

    if bool(args.save_best_model):
        windows, cols = windows_cache[str(best["feature_set"])]
        fit_and_save_best(windows, cols, best, out_dir, args)
        print(f"\n[DONE] best model saved under {out_dir / 'best_model'}")
    print(f"[DONE] results -> {out_dir}")


if __name__ == "__main__":
    main()
