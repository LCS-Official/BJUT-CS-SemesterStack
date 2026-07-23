from __future__ import annotations

import argparse
import itertools
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any

import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Grid-search a PL-friendly linear SVM with special focus on blink-class performance."
        )
    )
    parser.add_argument("--train_csv", type=str, required=True)
    parser.add_argument("--val_csv", type=str, required=True)
    parser.add_argument("--test_csv", type=str, required=True)
    parser.add_argument("--out_dir", type=str, default="svm_runs/linear_grid_blink")

    parser.add_argument(
        "--c_grid",
        type=str,
        default="0.03,0.1,0.3,1,3,10,30",
        help="Comma-separated C values."
    )
    parser.add_argument(
        "--blink_weight_grid",
        type=str,
        default="1.5,1.8,2.2,2.6,3.0,3.5",
        help="Comma-separated class-1 weights."
    )
    parser.add_argument(
        "--closed_weight_grid",
        type=str,
        default="0.7,0.8,1.0,1.2",
        help="Comma-separated class-2 weights."
    )
    parser.add_argument(
        "--open_weight_grid",
        type=str,
        default="1.0",
        help="Comma-separated class-0 weights."
    )
    parser.add_argument(
        "--multi_class_grid",
        type=str,
        default="ovr,crammer_singer",
        help='Comma-separated choices from {"ovr","crammer_singer"}.'
    )
    parser.add_argument(
        "--max_iter",
        type=int,
        default=30000,
        help="Max iterations for LinearSVC."
    )
    parser.add_argument(
        "--fixed_scale",
        type=int,
        default=4096,
        help="Scale factor for quantized export."
    )
    parser.add_argument(
        "--refit_train_val",
        action="store_true",
        help=(
            "After selecting best hyperparameters on VAL, refit on TRAIN+VAL "
            "and report final TEST metrics/export params from the refit model."
        ),
    )
    parser.add_argument(
        "--save_joblib",
        action="store_true",
        help="Save the best sklearn pipeline as joblib."
    )
    return parser.parse_args()


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    df = pd.read_csv(path)
    if "label" not in df.columns:
        raise ValueError(f"{path} must contain a 'label' column.")
    return df


def get_feature_columns(df: pd.DataFrame) -> List[str]:
    feat_cols = [c for c in df.columns if c.startswith("ear_")]
    if not feat_cols:
        raise ValueError("No feature columns like ear_0 ... ear_14 found.")
    feat_cols = sorted(feat_cols, key=lambda x: int(x.split("_")[1]))
    return feat_cols


def prepare_xy(df: pd.DataFrame, feat_cols: List[str]) -> Tuple[np.ndarray, np.ndarray]:
    x = df[feat_cols].to_numpy(dtype=np.float64)
    y = df["label"].to_numpy(dtype=np.int64)
    return x, y


def parse_float_grid(text: str) -> List[float]:
    return [float(x.strip()) for x in text.split(",") if x.strip()]


def parse_multi_class_grid(text: str) -> List[str]:
    vals = [x.strip() for x in text.split(",") if x.strip()]
    valid = {"ovr", "crammer_singer"}
    for v in vals:
        if v not in valid:
            raise ValueError(f"Invalid multi_class value: {v}")
    return vals


def save_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def evaluate_detailed(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
    acc = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average="macro")
    weighted_f1 = f1_score(y_true, y_pred, average="weighted")
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2])
    report = classification_report(y_true, y_pred, digits=4)

    prec, rec, f1, sup = precision_recall_fscore_support(
        y_true, y_pred, labels=[0, 1, 2], zero_division=0
    )

    cls_metrics = {
        0: {
            "precision": float(prec[0]),
            "recall": float(rec[0]),
            "f1": float(f1[0]),
            "support": int(sup[0]),
        },
        1: {
            "precision": float(prec[1]),
            "recall": float(rec[1]),
            "f1": float(f1[1]),
            "support": int(sup[1]),
        },
        2: {
            "precision": float(prec[2]),
            "recall": float(rec[2]),
            "f1": float(f1[2]),
            "support": int(sup[2]),
        },
    }

    return {
        "accuracy": float(acc),
        "macro_f1": float(macro_f1),
        "weighted_f1": float(weighted_f1),
        "confusion_matrix": cm.tolist(),
        "report": report,
        "per_class": cls_metrics,
    }


def print_metrics(title: str, metrics: Dict[str, Any]) -> None:
    print(f"\n[{title}]")
    print(f"accuracy   = {metrics['accuracy']:.4f}")
    print(f"macro_f1   = {metrics['macro_f1']:.4f}")
    print(f"weighted_f1= {metrics['weighted_f1']:.4f}")
    print("confusion_matrix:")
    print(np.array(metrics["confusion_matrix"]))
    print("classification_report:")
    print(metrics["report"])


def blink_priority_score(metrics: Dict[str, Any]) -> float:
    """
    Blink-oriented model selection score.
    Priority:
    - blink F1
    - blink recall
    - macro F1
    - penalize open->(1/2) false alarms slightly
    """
    blink_f1 = metrics["per_class"][1]["f1"]
    blink_recall = metrics["per_class"][1]["recall"]
    macro_f1 = metrics["macro_f1"]

    cm = np.array(metrics["confusion_matrix"], dtype=np.int64)
    # open predicted as blink or closed
    open_false_alarm = cm[0, 1] + cm[0, 2]
    open_total = max(cm[0].sum(), 1)
    open_false_alarm_rate = open_false_alarm / open_total

    score = (
        0.55 * blink_f1
        + 0.25 * blink_recall
        + 0.20 * macro_f1
        - 0.10 * open_false_alarm_rate
    )
    return float(score)


def predict_with_folded_float(x_raw: np.ndarray, w_eff: np.ndarray, b_eff: np.ndarray) -> np.ndarray:
    scores = x_raw @ w_eff.T + b_eff[None, :]
    return np.argmax(scores, axis=1)


def predict_with_quantized(x_raw: np.ndarray, w_q: np.ndarray, b_q: np.ndarray) -> np.ndarray:
    scores = x_raw @ w_q.T + b_q[None, :]
    return np.argmax(scores, axis=1)


def export_hls_header(
    out_path: Path,
    class_ids: np.ndarray,
    w_q: np.ndarray,
    b_q: np.ndarray,
    fixed_scale: int,
) -> None:
    num_classes, feature_dim = w_q.shape
    lines = []
    lines.append("#pragma once")
    lines.append("#include <stdint.h>")
    lines.append("")
    lines.append(f"static const int SVM_NUM_CLASSES = {num_classes};")
    lines.append(f"static const int SVM_FEATURE_DIM = {feature_dim};")
    lines.append(f"static const int SVM_FIXED_SCALE = {fixed_scale};")
    lines.append("")

    cls_str = ", ".join(str(int(v)) for v in class_ids.tolist())
    lines.append(f"static const int32_t SVM_CLASS_IDS[{num_classes}] = {{{cls_str}}};")
    lines.append("")

    lines.append(f"static const int32_t SVM_B[{num_classes}] = {{")
    for i in range(num_classes):
        comma = "," if i < num_classes - 1 else ""
        lines.append(f"    {int(b_q[i])}{comma}")
    lines.append("};")
    lines.append("")

    lines.append(f"static const int32_t SVM_W[{num_classes}][{feature_dim}] = {{")
    for c in range(num_classes):
        row = ", ".join(str(int(v)) for v in w_q[c].tolist())
        comma = "," if c < num_classes - 1 else ""
        lines.append(f"    {{{row}}}{comma}")
    lines.append("};")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def build_model(
    c_value: float,
    class_weight: Dict[int, float],
    multi_class: str,
    max_iter: int,
) -> Pipeline:
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "svc",
                LinearSVC(
                    C=c_value,
                    class_weight=class_weight,
                    max_iter=max_iter,
                    dual="auto",
                    random_state=42,
                    multi_class=multi_class,
                ),
            ),
        ]
    )


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    train_df = load_csv(Path(args.train_csv))
    val_df = load_csv(Path(args.val_csv))
    test_df = load_csv(Path(args.test_csv))

    feat_cols = get_feature_columns(train_df)

    x_train, y_train = prepare_xy(train_df, feat_cols)
    x_val, y_val = prepare_xy(val_df, feat_cols)
    x_test, y_test = prepare_xy(test_df, feat_cols)

    c_grid = parse_float_grid(args.c_grid)
    blink_weight_grid = parse_float_grid(args.blink_weight_grid)
    closed_weight_grid = parse_float_grid(args.closed_weight_grid)
    open_weight_grid = parse_float_grid(args.open_weight_grid)
    multi_class_grid = parse_multi_class_grid(args.multi_class_grid)

    search_space = list(itertools.product(
        c_grid,
        open_weight_grid,
        blink_weight_grid,
        closed_weight_grid,
        multi_class_grid,
    ))

    print("[INFO] Grid search start...")
    print(f"[INFO] train/val/test = {len(train_df)}/{len(val_df)}/{len(test_df)}")
    print(f"[INFO] feature_dim = {len(feat_cols)}")
    print(f"[INFO] num_candidates = {len(search_space)}")

    all_results: List[Dict[str, Any]] = []
    best_model = None
    best_result = None
    best_score = -1e18
    t0_all = time.time()

    for idx, (c_value, w0, w1, w2, multi_class) in enumerate(search_space, start=1):
        class_weight = {0: float(w0), 1: float(w1), 2: float(w2)}
        model = build_model(
            c_value=c_value,
            class_weight=class_weight,
            multi_class=multi_class,
            max_iter=args.max_iter,
        )

        t0 = time.time()
        model.fit(x_train, y_train)
        fit_sec = time.time() - t0

        val_pred = model.predict(x_val)
        val_metrics = evaluate_detailed(y_val, val_pred)
        score = blink_priority_score(val_metrics)

        result = {
            "rank_score": float(score),
            "C": float(c_value),
            "class_weight": class_weight,
            "multi_class": multi_class,
            "fit_seconds": float(fit_sec),
            "val_accuracy": val_metrics["accuracy"],
            "val_macro_f1": val_metrics["macro_f1"],
            "val_weighted_f1": val_metrics["weighted_f1"],
            "val_blink_precision": val_metrics["per_class"][1]["precision"],
            "val_blink_recall": val_metrics["per_class"][1]["recall"],
            "val_blink_f1": val_metrics["per_class"][1]["f1"],
            "val_open_f1": val_metrics["per_class"][0]["f1"],
            "val_closed_f1": val_metrics["per_class"][2]["f1"],
            "val_confusion_matrix": val_metrics["confusion_matrix"],
        }
        all_results.append(result)

        print(
            f"[{idx:03d}/{len(search_space)}] "
            f"C={c_value}, cw={class_weight}, multi={multi_class} | "
            f"score={score:.4f} | "
            f"blink_f1={val_metrics['per_class'][1]['f1']:.4f}, "
            f"blink_rec={val_metrics['per_class'][1]['recall']:.4f}, "
            f"macro_f1={val_metrics['macro_f1']:.4f}"
        )

        if score > best_score:
            best_score = score
            best_model = model
            best_result = {
                "search_record": result,
                "val_metrics": val_metrics,
            }

    total_search_sec = time.time() - t0_all

    if best_model is None or best_result is None:
        raise RuntimeError("No valid model found in search.")

    print("\n[INFO] Best hyperparameters found:")
    print(json.dumps(best_result["search_record"], indent=2, ensure_ascii=False))

    # Optional refit on TRAIN+VAL
    final_model = best_model
    fit_mode = "train_only_best_val_selected"

    if args.refit_train_val:
        x_trainval = np.concatenate([x_train, x_val], axis=0)
        y_trainval = np.concatenate([y_train, y_val], axis=0)

        rec = best_result["search_record"]
        final_model = build_model(
            c_value=rec["C"],
            class_weight=rec["class_weight"],
            multi_class=rec["multi_class"],
            max_iter=args.max_iter,
        )
        final_model.fit(x_trainval, y_trainval)
        fit_mode = "refit_on_train_plus_val"

    # Final evaluation
    pred_train = final_model.predict(x_train)
    pred_val = final_model.predict(x_val)
    pred_test = final_model.predict(x_test)

    train_metrics = evaluate_detailed(y_train, pred_train)
    val_metrics = evaluate_detailed(y_val, pred_val)
    test_metrics = evaluate_detailed(y_test, pred_test)

    print_metrics("TRAIN / sklearn", train_metrics)
    print_metrics("VAL / sklearn", val_metrics)
    print_metrics("TEST / sklearn", test_metrics)

    svc: LinearSVC = final_model.named_steps["svc"]
    scaler: StandardScaler = final_model.named_steps["scaler"]

    w = svc.coef_.astype(np.float64)
    b = svc.intercept_.astype(np.float64)
    mu = scaler.mean_.astype(np.float64)
    sigma = scaler.scale_.astype(np.float64)
    class_ids = svc.classes_.astype(np.int32)

    w_eff = w / sigma
    b_eff = b - np.sum(w * (mu / sigma), axis=1)

    pred_val_folded = predict_with_folded_float(x_val, w_eff, b_eff)
    pred_test_folded = predict_with_folded_float(x_test, w_eff, b_eff)
    val_folded_metrics = evaluate_detailed(y_val, pred_val_folded)
    test_folded_metrics = evaluate_detailed(y_test, pred_test_folded)

    fixed_scale = int(args.fixed_scale)
    w_q = np.round(w_eff * fixed_scale).astype(np.int32)
    b_q = np.round(b_eff * fixed_scale).astype(np.int32)

    pred_val_quant = predict_with_quantized(x_val, w_q, b_q)
    pred_test_quant = predict_with_quantized(x_test, w_q, b_q)
    val_quant_metrics = evaluate_detailed(y_val, pred_val_quant)
    test_quant_metrics = evaluate_detailed(y_test, pred_test_quant)

    print_metrics("VAL / folded_float", val_folded_metrics)
    print_metrics("TEST / folded_float", test_folded_metrics)
    print_metrics("VAL / quantized", val_quant_metrics)
    print_metrics("TEST / quantized", test_quant_metrics)

    # Save text reports
    save_text(out_dir / "train_report.txt", train_metrics["report"])
    save_text(out_dir / "val_report.txt", val_metrics["report"])
    save_text(out_dir / "test_report.txt", test_metrics["report"])

    save_text(out_dir / "val_folded_report.txt", val_folded_metrics["report"])
    save_text(out_dir / "test_folded_report.txt", test_folded_metrics["report"])
    save_text(out_dir / "val_quant_report.txt", val_quant_metrics["report"])
    save_text(out_dir / "test_quant_report.txt", test_quant_metrics["report"])

    # Save search records
    results_df = pd.DataFrame(all_results)
    results_df = results_df.sort_values(
        by=["rank_score", "val_blink_f1", "val_blink_recall", "val_macro_f1"],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)
    results_df.to_csv(out_dir / "grid_search_results.csv", index=False)

    export_dict = {
        "classes": class_ids.tolist(),
        "feature_dim": int(len(feat_cols)),
        "fixed_scale": fixed_scale,

        "coef": w.tolist(),
        "intercept": b.tolist(),
        "scaler_mean": mu.tolist(),
        "scaler_scale": sigma.tolist(),

        "coef_eff": w_eff.tolist(),
        "intercept_eff": b_eff.tolist(),

        "coef_q": w_q.tolist(),
        "intercept_q": b_q.tolist(),
    }

    with (out_dir / "linear_export.json").open("w", encoding="utf-8") as f:
        json.dump(export_dict, f, indent=2, ensure_ascii=False)

    export_hls_header(
        out_path=out_dir / "svm_linear_params.h",
        class_ids=class_ids,
        w_q=w_q,
        b_q=b_q,
        fixed_scale=fixed_scale,
    )

    if args.save_joblib:
        joblib.dump(final_model, out_dir / "svm_linear_model.joblib")

    summary = {
        "fit_mode": fit_mode,
        "search_seconds": total_search_sec,
        "num_candidates": len(search_space),
        "best_search_record": best_result["search_record"],
        "train_metrics_sklearn": {
            "accuracy": train_metrics["accuracy"],
            "macro_f1": train_metrics["macro_f1"],
            "weighted_f1": train_metrics["weighted_f1"],
            "blink_f1": train_metrics["per_class"][1]["f1"],
            "blink_recall": train_metrics["per_class"][1]["recall"],
        },
        "val_metrics_sklearn": {
            "accuracy": val_metrics["accuracy"],
            "macro_f1": val_metrics["macro_f1"],
            "weighted_f1": val_metrics["weighted_f1"],
            "blink_f1": val_metrics["per_class"][1]["f1"],
            "blink_recall": val_metrics["per_class"][1]["recall"],
        },
        "test_metrics_sklearn": {
            "accuracy": test_metrics["accuracy"],
            "macro_f1": test_metrics["macro_f1"],
            "weighted_f1": test_metrics["weighted_f1"],
            "blink_f1": test_metrics["per_class"][1]["f1"],
            "blink_recall": test_metrics["per_class"][1]["recall"],
        },
        "val_metrics_quantized": {
            "accuracy": val_quant_metrics["accuracy"],
            "macro_f1": val_quant_metrics["macro_f1"],
            "weighted_f1": val_quant_metrics["weighted_f1"],
            "blink_f1": val_quant_metrics["per_class"][1]["f1"],
            "blink_recall": val_quant_metrics["per_class"][1]["recall"],
        },
        "test_metrics_quantized": {
            "accuracy": test_quant_metrics["accuracy"],
            "macro_f1": test_quant_metrics["macro_f1"],
            "weighted_f1": test_quant_metrics["weighted_f1"],
            "blink_f1": test_quant_metrics["per_class"][1]["f1"],
            "blink_recall": test_quant_metrics["per_class"][1]["recall"],
        },
    }

    with (out_dir / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n[DONE] grid results -> {out_dir / 'grid_search_results.csv'}")
    print(f"[DONE] params json  -> {out_dir / 'linear_export.json'}")
    print(f"[DONE] HLS header   -> {out_dir / 'svm_linear_params.h'}")
    print(f"[DONE] summary      -> {out_dir / 'summary.json'}")


if __name__ == "__main__":
    main()