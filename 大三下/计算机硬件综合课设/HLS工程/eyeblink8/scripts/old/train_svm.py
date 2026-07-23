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
from sklearn.svm import SVC


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train and evaluate SVM on EAR-window dataset."
    )
    parser.add_argument("--train_csv", type=str, required=True)
    parser.add_argument("--val_csv", type=str, required=True)
    parser.add_argument("--test_csv", type=str, required=True)
    parser.add_argument("--out_dir", type=str, default="svm_runs/run1")

    parser.add_argument(
        "--kernel",
        type=str,
        default="rbf",
        choices=["linear", "rbf", "poly", "sigmoid"],
        help="SVC kernel",
    )
    parser.add_argument("--C", type=float, default=1.0)
    parser.add_argument("--gamma", type=str, default="scale")
    parser.add_argument("--degree", type=int, default=3)

    parser.add_argument(
        "--class_weight",
        type=str,
        default="balanced",
        help='Use "balanced", "none", or a JSON dict string like \'{"0":1,"1":2,"2":3}\'',
    )

    parser.add_argument(
        "--use_sklearnex",
        action="store_true",
        help="Try patching sklearn with scikit-learn-intelex. "
             "Useful mainly for binary SVC with supported settings.",
    )

    parser.add_argument(
        "--probability",
        action="store_true",
        help="Enable probability estimates. Slower.",
    )

    return parser.parse_args()


def maybe_patch_sklearn(use_sklearnex: bool) -> Tuple[bool, str]:
    if not use_sklearnex:
        return False, "disabled"

    try:
        from sklearnex import patch_sklearn  # type: ignore
        patch_sklearn()
        return True, "patched"
    except Exception as e:
        return False, f"failed: {e}"


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


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    patched, patch_msg = maybe_patch_sklearn(args.use_sklearnex)

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
                SVC(
                    kernel=args.kernel,
                    C=args.C,
                    gamma=args.gamma,
                    degree=args.degree,
                    class_weight=class_weight,
                    probability=args.probability,
                    decision_function_shape="ovr",
                ),
            ),
        ]
    )

    print("[INFO] Training start...")
    print(f"[INFO] sklearnex = {patched} ({patch_msg})")
    print(f"[INFO] kernel = {args.kernel}")
    print(f"[INFO] C = {args.C}")
    print(f"[INFO] gamma = {args.gamma}")
    print(f"[INFO] class_weight = {class_weight}")
    print(f"[INFO] train/val/test = {len(train_df)}/{len(val_df)}/{len(test_df)}")
    print(f"[INFO] feature_dim = {len(feat_cols)}")

    t0 = time.time()
    model.fit(x_train, y_train)
    train_seconds = time.time() - t0

    def evaluate(split_name: str, x: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        pred = model.predict(x)

        acc = accuracy_score(y, pred)
        macro_f1 = f1_score(y, pred, average="macro")
        weighted_f1 = f1_score(y, pred, average="weighted")
        cm = confusion_matrix(y, pred)
        report = classification_report(y, pred, digits=4)

        print(f"\n[{split_name}]")
        print(f"accuracy   = {acc:.4f}")
        print(f"macro_f1   = {macro_f1:.4f}")
        print(f"weighted_f1= {weighted_f1:.4f}")
        print("confusion_matrix:")
        print(cm)
        print("classification_report:")
        print(report)

        save_text(out_dir / f"{split_name.lower()}_report.txt", report)
        save_text(out_dir / f"{split_name.lower()}_confusion_matrix.txt", np.array2string(cm))

        return {
            "accuracy": float(acc),
            "macro_f1": float(macro_f1),
            "weighted_f1": float(weighted_f1),
        }

    train_metrics = evaluate("TRAIN", x_train, y_train)
    val_metrics = evaluate("VAL", x_val, y_val)
    test_metrics = evaluate("TEST", x_test, y_test)

    model_path = out_dir / "svm_model.joblib"
    joblib.dump(model, model_path)

    summary = {
        "patched_sklearnex": patched,
        "patch_message": patch_msg,
        "kernel": args.kernel,
        "C": args.C,
        "gamma": args.gamma,
        "degree": args.degree,
        "class_weight": class_weight,
        "train_seconds": train_seconds,
        "feature_dim": len(feat_cols),
        "train_samples": int(len(train_df)),
        "val_samples": int(len(val_df)),
        "test_samples": int(len(test_df)),
        "train_metrics": train_metrics,
        "val_metrics": val_metrics,
        "test_metrics": test_metrics,
    }

    with (out_dir / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n[DONE] model -> {model_path}")
    print(f"[DONE] summary -> {out_dir / 'summary.json'}")
    print(f"[DONE] training time = {train_seconds:.2f} s")


if __name__ == "__main__":
    main()