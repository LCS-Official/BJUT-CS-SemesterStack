from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Train a PL-friendly linear SVM on 15-D EAR window features, "
            "and export folded/quantized parameters for HLS deployment."
        )
    )
    parser.add_argument("--train_csv", type=str, required=True)
    parser.add_argument("--val_csv", type=str, required=True)
    parser.add_argument("--test_csv", type=str, required=True)
    parser.add_argument("--out_dir", type=str, default="svm_runs/linear_run1")

    parser.add_argument("--C", type=float, default=1.0)
    parser.add_argument(
        "--class_weight",
        type=str,
        default="balanced",
        help='Use "balanced", "none", or a JSON dict string like \'{"0":1,"1":2,"2":3}\'',
    )
    parser.add_argument(
        "--max_iter",
        type=int,
        default=20000,
        help="Max iterations for LinearSVC",
    )
    parser.add_argument(
        "--fixed_scale",
        type=int,
        default=4096,
        help=(
            "Scale factor for fixed-point export. "
            "Example: 4096 ~= Q12 fractional scaling."
        ),
    )
    parser.add_argument(
        "--save_joblib",
        action="store_true",
        help="Also save sklearn pipeline as joblib.",
    )

    return parser.parse_args()


def parse_class_weight(arg: str):
    if arg.lower() == "balanced":
        return "balanced"
    if arg.lower() == "none":
        return None

    try:
        raw = json.loads(arg)
        return {int(k): float(v) for k, v in raw.items()}
    except Exception as e:
        raise ValueError(
            f"Invalid --class_weight: {arg}. "
            f'Use "balanced", "none", or JSON dict.'
        ) from e


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


def save_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def evaluate_predictions(split_name: str, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    acc = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average="macro")
    weighted_f1 = f1_score(y_true, y_pred, average="weighted")
    cm = confusion_matrix(y_true, y_pred)
    report = classification_report(y_true, y_pred, digits=4)

    print(f"\n[{split_name}]")
    print(f"accuracy   = {acc:.4f}")
    print(f"macro_f1   = {macro_f1:.4f}")
    print(f"weighted_f1= {weighted_f1:.4f}")
    print("confusion_matrix:")
    print(cm)
    print("classification_report:")
    print(report)

    return {
        "accuracy": float(acc),
        "macro_f1": float(macro_f1),
        "weighted_f1": float(weighted_f1),
        "confusion_matrix": cm.tolist(),
        "report": report,
    }


def predict_with_folded_float(x_raw: np.ndarray, w_eff: np.ndarray, b_eff: np.ndarray) -> np.ndarray:
    # x_raw: [N, D], w_eff: [C, D], b_eff: [C]
    scores = x_raw @ w_eff.T + b_eff[None, :]
    return np.argmax(scores, axis=1)


def predict_with_quantized(
    x_raw: np.ndarray,
    w_q: np.ndarray,
    b_q: np.ndarray,
) -> np.ndarray:
    # Integer-only score:
    # score_q = sum(w_q * x_raw) + b_q
    # Since all classes use same scale, argmax is preserved.
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

    class_list = ", ".join(str(int(v)) for v in class_ids.tolist())
    lines.append(f"static const int32_t SVM_CLASS_IDS[{num_classes}] = {{{class_list}}};")
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

    class_weight = parse_class_weight(args.class_weight)

    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "svc",
                LinearSVC(
                    C=args.C,
                    class_weight=class_weight,
                    max_iter=args.max_iter,
                    dual="auto",
                    random_state=42,
                ),
            ),
        ]
    )

    print("[INFO] Training start...")
    print("[INFO] model = StandardScaler + LinearSVC")
    print(f"[INFO] C = {args.C}")
    print(f"[INFO] class_weight = {class_weight}")
    print(f"[INFO] fixed_scale = {args.fixed_scale}")
    print(f"[INFO] train/val/test = {len(train_df)}/{len(val_df)}/{len(test_df)}")
    print(f"[INFO] feature_dim = {len(feat_cols)}")

    t0 = time.time()
    model.fit(x_train, y_train)
    train_seconds = time.time() - t0

    # ---------- sklearn pipeline evaluation ----------
    pred_train = model.predict(x_train)
    pred_val = model.predict(x_val)
    pred_test = model.predict(x_test)

    train_metrics = evaluate_predictions("TRAIN / sklearn", y_train, pred_train)
    val_metrics = evaluate_predictions("VAL / sklearn", y_val, pred_val)
    test_metrics = evaluate_predictions("TEST / sklearn", y_test, pred_test)

    save_text(out_dir / "train_report.txt", train_metrics["report"])
    save_text(out_dir / "val_report.txt", val_metrics["report"])
    save_text(out_dir / "test_report.txt", test_metrics["report"])

    save_text(out_dir / "train_confusion_matrix.txt", np.array2string(np.array(train_metrics["confusion_matrix"])))
    save_text(out_dir / "val_confusion_matrix.txt", np.array2string(np.array(val_metrics["confusion_matrix"])))
    save_text(out_dir / "test_confusion_matrix.txt", np.array2string(np.array(test_metrics["confusion_matrix"])))

    svc: LinearSVC = model.named_steps["svc"]
    scaler: StandardScaler = model.named_steps["scaler"]

    # Raw linear parameters after scaler
    # score = W * ((x - mu)/sigma) + b
    w = svc.coef_.astype(np.float64)          # [C, D]
    b = svc.intercept_.astype(np.float64)     # [C]
    mu = scaler.mean_.astype(np.float64)      # [D]
    sigma = scaler.scale_.astype(np.float64)  # [D]
    class_ids = svc.classes_.astype(np.int32)

    # Fold StandardScaler into weights/bias:
    # score = (W/sigma) * x + (b - sum(W * mu/sigma))
    w_eff = w / sigma
    b_eff = b - np.sum(w * (mu / sigma), axis=1)

    # ---------- folded-float evaluation ----------
    pred_val_folded = predict_with_folded_float(x_val, w_eff, b_eff)
    pred_test_folded = predict_with_folded_float(x_test, w_eff, b_eff)

    val_folded_metrics = evaluate_predictions("VAL / folded_float", y_val, pred_val_folded)
    test_folded_metrics = evaluate_predictions("TEST / folded_float", y_test, pred_test_folded)

    # ---------- quantized export ----------
    # x_raw stays in original EAR domain
    # w_eff / b_eff are quantized for PL integer MAC
    fixed_scale = int(args.fixed_scale)
    w_q = np.round(w_eff * fixed_scale).astype(np.int32)
    b_q = np.round(b_eff * fixed_scale).astype(np.int32)

    pred_val_quant = predict_with_quantized(x_val, w_q, b_q)
    pred_test_quant = predict_with_quantized(x_test, w_q, b_q)

    val_quant_metrics = evaluate_predictions("VAL / quantized", y_val, pred_val_quant)
    test_quant_metrics = evaluate_predictions("TEST / quantized", y_test, pred_test_quant)

    # ---------- save exports ----------
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
        model_path = out_dir / "svm_linear_model.joblib"
        joblib.dump(model, model_path)
        print(f"[DONE] model -> {model_path}")

    summary = {
        "model_type": "StandardScaler + LinearSVC",
        "C": args.C,
        "class_weight": class_weight,
        "max_iter": args.max_iter,
        "fixed_scale": fixed_scale,
        "feature_dim": len(feat_cols),
        "train_samples": int(len(train_df)),
        "val_samples": int(len(val_df)),
        "test_samples": int(len(test_df)),
        "train_seconds": train_seconds,

        "train_metrics_sklearn": {
            "accuracy": train_metrics["accuracy"],
            "macro_f1": train_metrics["macro_f1"],
            "weighted_f1": train_metrics["weighted_f1"],
        },
        "val_metrics_sklearn": {
            "accuracy": val_metrics["accuracy"],
            "macro_f1": val_metrics["macro_f1"],
            "weighted_f1": val_metrics["weighted_f1"],
        },
        "test_metrics_sklearn": {
            "accuracy": test_metrics["accuracy"],
            "macro_f1": test_metrics["macro_f1"],
            "weighted_f1": test_metrics["weighted_f1"],
        },
        "val_metrics_folded_float": {
            "accuracy": val_folded_metrics["accuracy"],
            "macro_f1": val_folded_metrics["macro_f1"],
            "weighted_f1": val_folded_metrics["weighted_f1"],
        },
        "test_metrics_folded_float": {
            "accuracy": test_folded_metrics["accuracy"],
            "macro_f1": test_folded_metrics["macro_f1"],
            "weighted_f1": test_folded_metrics["weighted_f1"],
        },
        "val_metrics_quantized": {
            "accuracy": val_quant_metrics["accuracy"],
            "macro_f1": val_quant_metrics["macro_f1"],
            "weighted_f1": val_quant_metrics["weighted_f1"],
        },
        "test_metrics_quantized": {
            "accuracy": test_quant_metrics["accuracy"],
            "macro_f1": test_quant_metrics["macro_f1"],
            "weighted_f1": test_quant_metrics["weighted_f1"],
        },
    }

    with (out_dir / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n[DONE] linear params json -> {out_dir / 'linear_export.json'}")
    print(f"[DONE] HLS header         -> {out_dir / 'svm_linear_params.h'}")
    print(f"[DONE] summary            -> {out_dir / 'summary.json'}")
    print(f"[DONE] training time      -> {train_seconds:.2f} s")


if __name__ == "__main__":
    main()