from __future__ import annotations

r"""
Export a practical 30D binary EyeFeature LinearSVM for HLS/PL use.

This script is meant to run AFTER auto_train_binary_eyefeature_grid.py has produced:
  work_autotune_binary_30d/results_ranked.csv
  work_autotune_binary_30d/dataset_cache/.../train.csv,val.csv,test.csv

Default practical choice:
  config_id = 193
  threshold = 0.0

Why threshold=0:
  The previous VAL-tuned threshold overfit validation and nearly missed all TEST closed samples.
  For deployment, the raw hyperplane threshold is a more practical baseline, and PS-side
  consecutive-frame filtering can suppress short false closed blips.

Windows usage:
  cd C:\Users\LC\Desktop\eyeblink8

  python scripts\export_practical_binary_svm.py ^
    --results_csv work_autotune_binary_30d\results_ranked.csv ^
    --config_id 193 ^
    --threshold 0 ^
    --out_dir work_practical_binary_svm_cfg193

Outputs:
  work_practical_binary_svm_cfg193/
    practical_report.md
    practical_metrics.json
    practical_linear_export_binary.json
    practical_svm_weights_eyefeature_binary.h
    practical_model.joblib
    train_predictions.csv / val_predictions.csv / test_predictions.csv
    per_video_metrics.csv
    copied_train.csv / copied_val.csv / copied_test.csv
"""

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from tqdm import tqdm

LABEL_NAMES = ["non_closed", "closed"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export a practical 30D binary EyeFeature SVM model from an AutoTune config.")
    p.add_argument("--results_csv", type=str, default="work_autotune_binary_30d/results_ranked.csv")
    p.add_argument("--config_id", type=int, default=193)
    p.add_argument("--threshold", type=float, default=0.0,
                   help="Decision threshold on raw decision_function. Use 0 for practical baseline.")
    p.add_argument("--out_dir", type=str, default="work_practical_binary_svm_cfg193")
    p.add_argument("--fixed_scale", type=int, default=4096,
                   help="Input quantization scale: x_q=round(feature*fixed_scale)")
    p.add_argument("--weight_scale", type=int, default=1048576,
                   help="Weight quantization scale. 2^20 default.")
    p.add_argument("--max_iter", type=int, default=20000)
    p.add_argument("--random_seed", type=int, default=42)
    p.add_argument("--also_export_tuned_bias", action="store_true",
                   help="Also export bias folded with config's best_threshold from results_csv for comparison.")
    return p.parse_args()


def normalize_path_from_results(p: str, results_csv: Path) -> Path:
    """Resolve a path saved in results CSV. It is usually relative to the project CWD."""
    raw = Path(str(p))
    if raw.is_absolute():
        return raw
    # Try relative to current working directory first.
    if raw.exists():
        return raw
    # Try relative to parent of results_csv's parent. Usually results_csv = out_dir/results_ranked.csv,
    # and dataset_cache_dir may start with out_dir/...
    candidate = results_csv.parent.parent / raw
    if candidate.exists():
        return candidate
    # Try relative to results_csv parent if only dataset_cache/... was saved.
    candidate2 = results_csv.parent / raw
    if candidate2.exists():
        return candidate2
    return raw


def get_feature_cols(df: pd.DataFrame) -> List[str]:
    meta_cols = {
        "video_id", "center_frame", "label_name", "label", "orig_label_name", "source",
        "decision_score", "pred", "pred_name", "threshold"
    }
    cols = [c for c in df.columns if c not in meta_cols]
    # Keep numeric feature columns only, in original CSV order.
    out = []
    for c in cols:
        if pd.api.types.is_numeric_dtype(df[c]):
            out.append(c)
    return out


def parse_class_weight(s: str):
    s = str(s).strip()
    if s.lower() in {"", "none", "null", "nan"}:
        return None
    if s.lower() == "balanced":
        return "balanced"
    out: Dict[int, float] = {}
    name_to_id = {"non_closed": 0, "open": 0, "blink": 0, "closed": 1, "0": 0, "1": 1}
    for item in s.split(","):
        if not item.strip():
            continue
        if ":" not in item:
            raise ValueError(f"Bad class_weight item: {item}")
        k, v = item.split(":", 1)
        out[name_to_id[k.strip().lower()]] = float(v)
    return out


def confusion_for_threshold(y: np.ndarray, scores: np.ndarray, threshold: float) -> np.ndarray:
    pred = (scores > threshold).astype(np.int64)
    tn = int(((y == 0) & (pred == 0)).sum())
    fp = int(((y == 0) & (pred == 1)).sum())
    fn = int(((y == 1) & (pred == 0)).sum())
    tp = int(((y == 1) & (pred == 1)).sum())
    return np.array([[tn, fp], [fn, tp]], dtype=np.int64)


def metric_from_cm(cm: np.ndarray) -> Dict[str, float]:
    tn, fp, fn, tp = cm.ravel()
    total = tn + fp + fn + tp
    acc = (tn + tp) / total if total else 0.0
    nonclosed_precision = tn / (tn + fn) if (tn + fn) else 0.0
    nonclosed_recall = tn / (tn + fp) if (tn + fp) else 0.0
    nonclosed_f1 = 2 * nonclosed_precision * nonclosed_recall / (nonclosed_precision + nonclosed_recall) if (nonclosed_precision + nonclosed_recall) else 0.0
    closed_precision = tp / (tp + fp) if (tp + fp) else 0.0
    closed_recall = tp / (tp + fn) if (tp + fn) else 0.0
    closed_f1 = 2 * closed_precision * closed_recall / (closed_precision + closed_recall) if (closed_precision + closed_recall) else 0.0
    macro_f1 = 0.5 * (nonclosed_f1 + closed_f1)
    false_closed_rate = fp / (tn + fp) if (tn + fp) else 0.0
    missed_closed_rate = fn / (fn + tp) if (fn + tp) else 0.0
    return {
        "accuracy": float(acc),
        "macro_f1": float(macro_f1),
        "nonclosed_precision": float(nonclosed_precision),
        "nonclosed_recall": float(nonclosed_recall),
        "nonclosed_f1": float(nonclosed_f1),
        "closed_precision": float(closed_precision),
        "closed_recall": float(closed_recall),
        "closed_f1": float(closed_f1),
        "false_closed_rate": float(false_closed_rate),
        "missed_closed_rate": float(missed_closed_rate),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }


def eval_split(model, df: pd.DataFrame, feature_cols: List[str], threshold: float) -> Tuple[pd.DataFrame, Dict[str, float]]:
    X = df[feature_cols].to_numpy(dtype=np.float64)
    y = df["label"].to_numpy(dtype=np.int64)
    scores = model.decision_function(X)
    pred = (scores > threshold).astype(np.int64)
    out = df.copy()
    out["decision_score"] = scores
    out["threshold"] = float(threshold)
    out["pred"] = pred
    out["pred_name"] = np.where(pred == 1, "closed", "non_closed")
    cm = confusion_for_threshold(y, scores, threshold)
    m = metric_from_cm(cm)
    m["threshold"] = float(threshold)
    return out, m


def per_video_metrics(pred_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if "video_id" not in pred_df.columns:
        return pd.DataFrame()
    for vid, g in pred_df.groupby("video_id", sort=True):
        y = g["label"].to_numpy(dtype=np.int64)
        pred = g["pred"].to_numpy(dtype=np.int64)
        tn = int(((y == 0) & (pred == 0)).sum())
        fp = int(((y == 0) & (pred == 1)).sum())
        fn = int(((y == 1) & (pred == 0)).sum())
        tp = int(((y == 1) & (pred == 1)).sum())
        m = metric_from_cm(np.array([[tn, fp], [fn, tp]], dtype=np.int64))
        rows.append({
            "video_id": str(vid),
            "n": int(len(g)),
            "n_non_closed": int((y == 0).sum()),
            "n_closed": int((y == 1).sum()),
            **m,
        })
    return pd.DataFrame(rows)


def export_model(model, feature_cols: List[str], threshold: float, out_dir: Path, args: argparse.Namespace, meta: Dict[str, object]) -> None:
    import joblib

    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, out_dir / "practical_model.joblib")

    scaler = model.named_steps["standardscaler"]
    clf = model.named_steps["linearsvc"]
    sigma = scaler.scale_.copy()
    sigma[sigma == 0] = 1.0
    w_eff = (clf.coef_[0] / sigma).astype(np.float64)
    b_eff = float(clf.intercept_[0] - np.sum(clf.coef_[0] * scaler.mean_ / sigma))
    b_eff_thresholded = float(b_eff - threshold)

    fixed_scale = int(args.fixed_scale)
    weight_scale = int(args.weight_scale)
    w_q = np.round(w_eff * weight_scale).astype(np.int64)
    b_q_zero = int(np.round(b_eff * weight_scale * fixed_scale))
    th_q = int(np.round(float(threshold) * weight_scale * fixed_scale))
    b_q_practical = int(np.round(b_eff_thresholded * weight_scale * fixed_scale))

    export = {
        "feature_cols": feature_cols,
        "input_dim": len(feature_cols),
        "classes": [0, 1],
        "class_names": LABEL_NAMES,
        "positive_class": "closed",
        "threshold_float": float(threshold),
        "decision_rule": "score_q = sum(SVM_W[i] * x_q[i]) + SVM_B_PRACTICAL; score_q > 0 => closed",
        "x_q_rule": "x_q[i] = round(feature[i] * SVM_INPUT_SCALE)",
        "fixed_scale_for_input_x_q": fixed_scale,
        "weight_scale": weight_scale,
        "w_eff_float": w_eff.tolist(),
        "b_eff_float_zero_threshold": b_eff,
        "b_eff_float_practical": b_eff_thresholded,
        "w_q": w_q.tolist(),
        "b_q_zero_threshold": b_q_zero,
        "threshold_q": th_q,
        "b_q_practical": b_q_practical,
        "meta": meta,
    }
    (out_dir / "practical_linear_export_binary.json").write_text(json.dumps(export, indent=2, ensure_ascii=False), encoding="utf-8")

    with (out_dir / "practical_svm_weights_eyefeature_binary.h").open("w", encoding="utf-8") as f:
        f.write("#pragma once\n#include <stdint.h>\n\n")
        f.write("// Practical binary EyeFeature SVM. score_q > 0 => closed.\n")
        f.write("// Inputs must be quantized as x_q[i] = round(feature[i] * SVM_INPUT_SCALE).\n")
        f.write(f"#define SVM_INPUT_DIM {len(feature_cols)}\n")
        f.write(f"#define SVM_INPUT_SCALE {fixed_scale}\n")
        f.write(f"#define SVM_WEIGHT_SCALE {weight_scale}\n")
        f.write(f"#define SVM_THRESHOLD_FLOAT {float(threshold):.9g}\n\n")
        f.write("static const int32_t SVM_W[SVM_INPUT_DIM] = {\n    ")
        f.write(",\n    ".join(str(int(x)) for x in w_q))
        f.write("\n};\n")
        f.write(f"static const int64_t SVM_B_ZERO_THRESHOLD = {int(b_q_zero)};\n")
        f.write(f"static const int64_t SVM_THRESHOLD_Q = {int(th_q)};\n")
        f.write(f"static const int64_t SVM_B_PRACTICAL = {int(b_q_practical)};\n\n")
        f.write("static inline int classify_eye_closed_binary(const int32_t x_q[SVM_INPUT_DIM]) {\n")
        f.write("    int64_t acc = SVM_B_PRACTICAL;\n")
        f.write("    for (int i = 0; i < SVM_INPUT_DIM; ++i) {\n")
        f.write("        acc += (int64_t)SVM_W[i] * (int64_t)x_q[i];\n")
        f.write("    }\n")
        f.write("    return acc > 0 ? 1 : 0; // 1=closed, 0=non_closed\n")
        f.write("}\n")


def main() -> None:
    args = parse_args()
    results_csv = Path(args.results_csv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Loading results: {results_csv}")
    results = pd.read_csv(results_csv)
    if "config_id" not in results.columns:
        raise ValueError("results_csv must contain config_id")
    rows = results[results["config_id"].astype(int) == int(args.config_id)]
    if rows.empty:
        raise ValueError(f"config_id={args.config_id} not found in {results_csv}")
    cfg = rows.iloc[0].to_dict()

    ds_dir = normalize_path_from_results(str(cfg["dataset_cache_dir"]), results_csv)
    print(f"[INFO] config_id={args.config_id}")
    print(f"[INFO] feature_names={cfg.get('feature_names')}")
    print(f"[INFO] dataset_rule={cfg.get('dataset_rule_name')}, C={cfg.get('C')}, class_weight={cfg.get('class_weight')}")
    print(f"[INFO] dataset cache: {ds_dir}")

    train_path, val_path, test_path = ds_dir / "train.csv", ds_dir / "val.csv", ds_dir / "test.csv"
    if not train_path.exists() or not val_path.exists() or not test_path.exists():
        raise FileNotFoundError(f"Missing cached train/val/test under {ds_dir}. Run auto_train grid first.")

    print("[INFO] Loading cached datasets...")
    train_df = pd.read_csv(train_path, dtype={"video_id": str})
    val_df = pd.read_csv(val_path, dtype={"video_id": str})
    test_df = pd.read_csv(test_path, dtype={"video_id": str})
    feature_cols = get_feature_cols(train_df)
    if not feature_cols:
        raise ValueError("No feature columns found in cached train.csv")
    print(f"[INFO] input_dim={len(feature_cols)}")

    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.svm import LinearSVC

    print("[INFO] Training practical LinearSVC...")
    with tqdm(total=4, desc="Export practical model", unit="step") as pbar:
        X_train = train_df[feature_cols].to_numpy(dtype=np.float64)
        y_train = train_df["label"].to_numpy(dtype=np.int64)
        model = make_pipeline(
            StandardScaler(),
            LinearSVC(
                C=float(cfg["C"]),
                class_weight=parse_class_weight(str(cfg["class_weight"])),
                dual=False,
                max_iter=int(args.max_iter),
                random_state=int(args.random_seed),
            ),
        )
        pbar.set_postfix_str("fit")
        model.fit(X_train, y_train)
        pbar.update(1)

        split_metrics = {}
        split_preds = {}
        for name, df in [("train", train_df), ("val", val_df), ("test", test_df)]:
            pbar.set_postfix_str(f"eval {name}")
            pred_df, m = eval_split(model, df, feature_cols, float(args.threshold))
            split_preds[name] = pred_df
            split_metrics[name] = m
            pbar.update(1 if name != "test" else 0)
        pbar.set_postfix_str("export")
        meta = {
            "config_from_results": cfg,
            "chosen_config_id": int(args.config_id),
            "chosen_threshold": float(args.threshold),
            "note": "Practical export uses a fixed threshold, default 0.0, not VAL-tuned threshold.",
        }
        export_model(model, feature_cols, float(args.threshold), out_dir, args, meta)
        pbar.update(1)

    # Save datasets and predictions.
    shutil.copy2(train_path, out_dir / "copied_train.csv")
    shutil.copy2(val_path, out_dir / "copied_val.csv")
    shutil.copy2(test_path, out_dir / "copied_test.csv")
    for name, pred_df in split_preds.items():
        pred_df.to_csv(out_dir / f"{name}_predictions.csv", index=False, encoding="utf-8-sig")

    pv = pd.concat([
        per_video_metrics(split_preds["train"]).assign(split="train"),
        per_video_metrics(split_preds["val"]).assign(split="val"),
        per_video_metrics(split_preds["test"]).assign(split="test"),
    ], ignore_index=True)
    pv.to_csv(out_dir / "per_video_metrics.csv", index=False, encoding="utf-8-sig")

    metrics = {
        "config_id": int(args.config_id),
        "threshold": float(args.threshold),
        "feature_cols": feature_cols,
        "split_metrics": split_metrics,
        "config_from_results": cfg,
    }
    (out_dir / "practical_metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")

    def fmt(m: Dict[str, float]) -> str:
        return (
            f"acc={m['accuracy']:.4f}, macro_f1={m['macro_f1']:.4f}, "
            f"closed_precision={m['closed_precision']:.4f}, closed_recall={m['closed_recall']:.4f}, "
            f"false_closed_rate={m['false_closed_rate']:.4f}, missed_closed_rate={m['missed_closed_rate']:.4f}, "
            f"cm=[[{m['tn']},{m['fp']}],[{m['fn']},{m['tp']}]]"
        )

    report = []
    report.append("# Practical Binary 30D EyeFeature SVM Export\n")
    report.append("## Chosen config\n")
    report.append(f"- config_id: {int(args.config_id)}")
    report.append(f"- feature_names: {cfg.get('feature_names')}")
    report.append(f"- dataset_rule_name: {cfg.get('dataset_rule_name')}")
    report.append(f"- C: {cfg.get('C')}")
    report.append(f"- class_weight: {cfg.get('class_weight')}")
    report.append(f"- threshold used for export: {float(args.threshold)}")
    report.append(f"- input_dim: {len(feature_cols)}")
    report.append("\n## Metrics with exported threshold\n")
    for name in ["train", "val", "test"]:
        report.append(f"- {name}: {fmt(split_metrics[name])}")
    report.append("\n## HLS rule\n")
    report.append("```c")
    report.append("x_q[i] = round(feature[i] * SVM_INPUT_SCALE);")
    report.append("score_q = sum(SVM_W[i] * x_q[i]) + SVM_B_PRACTICAL;")
    report.append("pred_closed = (score_q > 0);")
    report.append("```")
    report.append("\n## Files\n")
    report.append("- practical_svm_weights_eyefeature_binary.h")
    report.append("- practical_linear_export_binary.json")
    report.append("- practical_model.joblib")
    report.append("- per_video_metrics.csv")
    report.append("- train_predictions.csv / val_predictions.csv / test_predictions.csv")
    (out_dir / "practical_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print("\n[DONE] Practical export complete.")
    print(f"[OUT] {out_dir}")
    print(f"[REPORT] {out_dir / 'practical_report.md'}")
    print(f"[HLS] {out_dir / 'practical_svm_weights_eyefeature_binary.h'}")
    print(f"[TEST] {fmt(split_metrics['test'])}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        raise
