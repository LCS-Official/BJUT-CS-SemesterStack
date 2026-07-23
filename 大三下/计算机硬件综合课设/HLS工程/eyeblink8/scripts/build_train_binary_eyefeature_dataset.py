from __future__ import annotations

"""
Build a 2-class EyeFeature SVM dataset from already-extracted frame-level EyeFeature CSVs.

Design:
  - Eyeblink8/raw contributes NON_CLOSED windows.
      * default policy: official open + official blink are both treated as non_closed.
      * this intentionally teaches the model that short blinks should not be treated as long closed/fatigue.
  - selfrec/raw_selfrec contributes CLOSED windows only, using manual_closed_intervals.csv.
      * frames outside manual closed intervals are NOT used as non_closed.

Typical Windows usage:
  cd C:\\Users\\LC\\Desktop\\eyeblink8

  python scripts\\build_train_binary_eyefeature_dataset.py ^
    --eyeblink8_labels_csv work\\frame_labels.csv ^
    --eyeblink8_features_csv work_eyefeature\\frame_eyefeature_eyeblink8.csv ^
    --selfrec_features_csv work_eyefeature\\frame_eyefeature_selfrec.csv ^
    --manual_intervals_csv work_selfrec\\manual_closed_intervals.csv ^
    --out_dir work_dataset_eyefeature_binary_30d ^
    --feature_names col_run_topk_fixed,col_run_topk_adapt ^
    --train_svm

Output:
  work_dataset_eyefeature_binary_30d/
    windows_eyeblink8_nonclosed.csv
    windows_selfrec_closed.csv
    windows_all_mixed.csv
    train.csv / val.csv / test.csv
    summary.json
    svm_linear_binary/
      train_report.txt / val_report.txt / test_report.txt
      linear_export_binary.json
      svm_weights_eyefeature_binary.h

HLS convention for exported binary SVM:
  x_q[i] = round(x[i] * SVM_INPUT_SCALE)
  score_q = sum_i(SVM_W[i] * x_q[i]) + SVM_B
  pred_closed = (score_q > 0)
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

LABEL_MAP = {"non_closed": 0, "closed": 1}
LABEL_NAMES = ["non_closed", "closed"]

DEFAULT_SELFREC_TRAIN = "11,22,33,WIN_20260414_20_31_10_Pro,WIN_20260414_20_41_42_Pro,test1,test2"
DEFAULT_SELFREC_VAL = "WIN_20260414_20_42_23_Pro,test3"
DEFAULT_SELFREC_TEST = "WIN_20260414_21_29_13_Pro,test4"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build binary EyeFeature windows and optionally train a binary linear SVM.")
    p.add_argument("--eyeblink8_labels_csv", type=str, default="work/frame_labels.csv")
    p.add_argument("--eyeblink8_features_csv", type=str, default="work_eyefeature/frame_eyefeature_eyeblink8.csv")
    p.add_argument("--selfrec_features_csv", type=str, default="work_eyefeature/frame_eyefeature_selfrec.csv")
    p.add_argument("--manual_intervals_csv", type=str, default="work_selfrec/manual_closed_intervals.csv")
    p.add_argument("--out_dir", type=str, default="work_dataset_eyefeature_binary_30d")
    p.add_argument("--feature_names", type=str, default="col_run_topk_fixed,col_run_topk_adapt", help="Comma-separated frame feature names. 2 features with window_size=15 gives 30D.")
    p.add_argument("--window_size", type=int, default=15)
    p.add_argument("--central_size", type=int, default=7)
    p.add_argument("--min_closed_in_central", type=int, default=6, help="Selfrec closed windows: min closed frames inside central span.")
    p.add_argument("--open_step", type=int, default=3, help="Keep every N-th pure-open Eyeblink8 window. Blink windows are not downsampled by this counter.")
    p.add_argument("--eyeblink8_policy", type=str, default="open_blink_as_nonclosed", choices=["open_blink_as_nonclosed", "open_only"], help="Whether to include official blink windows as non_closed, or discard blink windows.")
    p.add_argument("--train_videos", type=str, default="1,2,3,4,8,9")
    p.add_argument("--val_videos", type=str, default="A")
    p.add_argument("--test_videos", type=str, default="B")
    p.add_argument("--selfrec_train_videos", type=str, default=DEFAULT_SELFREC_TRAIN)
    p.add_argument("--selfrec_val_videos", type=str, default=DEFAULT_SELFREC_VAL)
    p.add_argument("--selfrec_test_videos", type=str, default=DEFAULT_SELFREC_TEST)
    p.add_argument("--shuffle_train", action="store_true")
    p.add_argument("--random_seed", type=int, default=42)
    p.add_argument("--train_svm", action="store_true")
    p.add_argument("--C", type=float, default=1.0)
    p.add_argument("--class_weight", type=str, default="balanced", help="balanced, none, or e.g. non_closed:1,closed:2")
    p.add_argument("--max_iter", type=int, default=20000)
    p.add_argument("--fixed_scale", type=int, default=4096, help="Input fixed-point scale used by PL: x_q=round(x*fixed_scale)")
    p.add_argument("--weight_scale", type=int, default=1048576, help="Quantized export scale for folded weights")
    return p.parse_args()


def parse_list_arg(s: str) -> List[str]:
    return [x.strip() for x in str(s).split(",") if x.strip()]


def is_consecutive_frames(frame_ids: np.ndarray) -> bool:
    if len(frame_ids) <= 1:
        return True
    return bool(np.all(np.diff(frame_ids) == 1))


def load_csv(path: Path, required: List[str]) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing: {path}")
    df = pd.read_csv(path, dtype={"video_id": str})
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{path} missing columns: {missing}")
    return df


def validate_feature_names(df: pd.DataFrame, feature_names: List[str], name: str) -> None:
    missing = [f for f in feature_names if f not in df.columns]
    if missing:
        raise ValueError(f"{name} missing feature columns: {missing}")


def add_window_features(row: dict, win: pd.DataFrame, feature_names: List[str]) -> None:
    # Feature layout: featureA_0..featureA_14, featureB_0..featureB_14, ...
    for name in feature_names:
        safe = name.replace("-", "_").replace(".", "_")
        vals = win[name].to_numpy(dtype=float)
        for i, v in enumerate(vals):
            row[f"{safe}_{i}"] = float(v)


def split_by_video(df: pd.DataFrame, train_videos: List[str], val_videos: List[str], test_videos: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train = df[df["video_id"].astype(str).isin(train_videos)].copy()
    val = df[df["video_id"].astype(str).isin(val_videos)].copy()
    test = df[df["video_id"].astype(str).isin(test_videos)].copy()
    return train, val, test


def build_eyeblink8_nonclosed_windows(labels: pd.DataFrame, features: pd.DataFrame, feature_names: List[str], args: argparse.Namespace) -> pd.DataFrame:
    need_labels = ["video_id", "frame_id", "blink_id", "is_blink", "is_closed", "is_valid"]
    need_feats = ["video_id", "frame_id", "det_ok"] + feature_names
    missing_l = [c for c in need_labels if c not in labels.columns]
    missing_f = [c for c in need_feats if c not in features.columns]
    if missing_l:
        raise ValueError(f"Eyeblink8 labels missing columns: {missing_l}")
    if missing_f:
        raise ValueError(f"Eyeblink8 features missing columns: {missing_f}")

    lab = labels[need_labels].copy()
    feat = features[need_feats].copy()
    for c in ["frame_id", "blink_id", "is_blink", "is_closed", "is_valid"]:
        lab[c] = pd.to_numeric(lab[c], errors="coerce")
    for c in ["frame_id", "det_ok"] + feature_names:
        feat[c] = pd.to_numeric(feat[c], errors="coerce")

    merged = pd.merge(lab, feat, on=["video_id", "frame_id"], how="inner", validate="one_to_one")
    merged = merged.sort_values(["video_id", "frame_id"]).reset_index(drop=True)

    half_w = int(args.window_size) // 2
    half_c = int(args.central_size) // 2
    rows: List[dict] = []
    open_kept_counter = 0

    for video_id, dfv in merged.groupby("video_id", sort=True):
        dfv = dfv.sort_values("frame_id").reset_index(drop=True)
        for center_idx in range(half_w, len(dfv) - half_w):
            win = dfv.iloc[center_idx - half_w:center_idx + half_w + 1].copy()
            if not is_consecutive_frames(win["frame_id"].to_numpy(dtype=int)):
                continue
            if win["det_ok"].isna().any() or (win["det_ok"] != 1).any():
                continue
            if win["is_valid"].isna().any() or (win["is_valid"] != 1).any():
                continue
            if win[feature_names].isna().any().any():
                continue

            central = win.iloc[half_w - half_c:half_w + half_c + 1].copy()
            blink_present = int(central["is_blink"].sum()) > 0
            closed_count = int(central["is_closed"].sum())

            if blink_present:
                orig_label_name = "blink"
                if args.eyeblink8_policy == "open_only":
                    continue
            elif closed_count == 0:
                orig_label_name = "open"
                # Downsample pure-open windows to reduce easy non_closed dominance.
                if open_kept_counter % max(1, int(args.open_step)) != 0:
                    open_kept_counter += 1
                    continue
                open_kept_counter += 1
            else:
                # Not official blink, but central closed frames exist: skip ambiguous Eyeblink8 windows.
                continue

            row = {
                "video_id": str(video_id),
                "center_frame": int(dfv.iloc[center_idx]["frame_id"]),
                "label_name": "non_closed",
                "label": LABEL_MAP["non_closed"],
                "orig_label_name": orig_label_name,
                "source": "eyeblink8",
            }
            add_window_features(row, win, feature_names)
            rows.append(row)

    return pd.DataFrame(rows)


def expand_selfrec_closed(features: pd.DataFrame, intervals: pd.DataFrame) -> pd.DataFrame:
    df = features.copy()
    df["is_closed_manual"] = 0
    for _, r in intervals.iterrows():
        if str(r.get("label", "closed")).lower() != "closed":
            continue
        vid = str(r["video_id"])
        s = int(r["start_frame"])
        e = int(r["end_frame"])
        if e < s:
            s, e = e, s
        mask = (df["video_id"].astype(str) == vid) & (df["frame_id"] >= s) & (df["frame_id"] <= e)
        df.loc[mask, "is_closed_manual"] = 1
    return df


def build_selfrec_closed_windows(features: pd.DataFrame, intervals: pd.DataFrame, feature_names: List[str], args: argparse.Namespace) -> pd.DataFrame:
    need_feats = ["video_id", "frame_id", "det_ok"] + feature_names
    missing_f = [c for c in need_feats if c not in features.columns]
    if missing_f:
        raise ValueError(f"selfrec features missing columns: {missing_f}")
    need_intervals = ["video_id", "start_frame", "end_frame", "label"]
    missing_i = [c for c in need_intervals if c not in intervals.columns]
    if missing_i:
        raise ValueError(f"manual intervals missing columns: {missing_i}")

    feat = features[need_feats].copy()
    for c in ["frame_id", "det_ok"] + feature_names:
        feat[c] = pd.to_numeric(feat[c], errors="coerce")
    inter = intervals.copy()
    inter["start_frame"] = pd.to_numeric(inter["start_frame"], errors="coerce")
    inter["end_frame"] = pd.to_numeric(inter["end_frame"], errors="coerce")
    inter = inter.dropna(subset=["start_frame", "end_frame"]).copy()
    inter["start_frame"] = inter["start_frame"].astype(int)
    inter["end_frame"] = inter["end_frame"].astype(int)
    inter = inter[inter["label"].astype(str).str.lower() == "closed"].copy()

    df = expand_selfrec_closed(feat, inter)
    df = df.sort_values(["video_id", "frame_id"]).reset_index(drop=True)

    half_w = int(args.window_size) // 2
    half_c = int(args.central_size) // 2
    rows: List[dict] = []

    for video_id, dfv in df.groupby("video_id", sort=True):
        dfv = dfv.sort_values("frame_id").reset_index(drop=True)
        for center_idx in range(half_w, len(dfv) - half_w):
            win = dfv.iloc[center_idx - half_w:center_idx + half_w + 1].copy()
            if not is_consecutive_frames(win["frame_id"].to_numpy(dtype=int)):
                continue
            if win["det_ok"].isna().any() or (win["det_ok"] != 1).any():
                continue
            if win[feature_names].isna().any().any():
                continue
            central = win.iloc[half_w - half_c:half_w + half_c + 1].copy()
            closed_count = int(central["is_closed_manual"].sum())
            if closed_count < int(args.min_closed_in_central):
                continue
            row = {
                "video_id": str(video_id),
                "center_frame": int(dfv.iloc[center_idx]["frame_id"]),
                "label_name": "closed",
                "label": LABEL_MAP["closed"],
                "orig_label_name": "closed",
                "source": "selfrec",
            }
            add_window_features(row, win, feature_names)
            rows.append(row)
    return pd.DataFrame(rows)


def parse_class_weight(s: str):
    s = str(s).strip()
    if s.lower() in {"", "none", "null"}:
        return None
    if s.lower() == "balanced":
        return "balanced"
    out: Dict[int, float] = {}
    name_to_id = {"non_closed": 0, "open": 0, "blink": 0, "closed": 1, "0": 0, "1": 1}
    for item in s.split(","):
        if not item.strip():
            continue
        k, v = item.split(":")
        out[name_to_id[k.strip().lower()]] = float(v)
    return out


def get_train_feature_cols(df: pd.DataFrame) -> List[str]:
    meta = {"video_id", "center_frame", "label_name", "label", "orig_label_name", "source"}
    cols = [c for c in df.columns if c not in meta]

    def sort_key(c: str):
        base, idx = c.rsplit("_", 1)
        return base, int(idx) if idx.isdigit() else 0

    return sorted(cols, key=sort_key)


def train_binary_linear_svm(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame, out_dir: Path, args: argparse.Namespace, feature_cols: List[str]) -> None:
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_recall_fscore_support
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.svm import LinearSVC

    svm_dir = out_dir / "svm_linear_binary"
    svm_dir.mkdir(parents=True, exist_ok=True)

    X_train = train_df[feature_cols].to_numpy(dtype=np.float64)
    y_train = train_df["label"].to_numpy(dtype=np.int64)
    X_val = val_df[feature_cols].to_numpy(dtype=np.float64)
    y_val = val_df["label"].to_numpy(dtype=np.int64)
    X_test = test_df[feature_cols].to_numpy(dtype=np.float64)
    y_test = test_df["label"].to_numpy(dtype=np.int64)

    model = make_pipeline(
        StandardScaler(),
        LinearSVC(
            C=float(args.C),
            class_weight=parse_class_weight(args.class_weight),
            dual=False,
            max_iter=int(args.max_iter),
            random_state=int(args.random_seed),
        ),
    )
    model.fit(X_train, y_train)

    def eval_split(name: str, X: np.ndarray, y: np.ndarray) -> Dict[str, object]:
        pred = model.predict(X)
        cm = confusion_matrix(y, pred, labels=[0, 1])
        report = classification_report(y, pred, labels=[0, 1], target_names=LABEL_NAMES, digits=4, zero_division=0)
        pr, rc, f1, sup = precision_recall_fscore_support(y, pred, labels=[0, 1], zero_division=0)
        # cm layout:
        # [[true non_closed predicted non_closed, true non_closed predicted closed],
        #  [true closed     predicted non_closed, true closed     predicted closed]]
        false_closed_rate = float(cm[0, 1] / cm[0].sum()) if cm[0].sum() else 0.0
        missed_closed_rate = float(cm[1, 0] / cm[1].sum()) if cm[1].sum() else 0.0
        text = (
            report
            + "\nconfusion_matrix(labels=non_closed,closed):\n"
            + str(cm)
            + f"\nfalse_closed_rate(non_closed->closed)={false_closed_rate:.6f}"
            + f"\nmissed_closed_rate(closed->non_closed)={missed_closed_rate:.6f}\n"
        )
        (svm_dir / f"{name}_report.txt").write_text(text, encoding="utf-8")
        print(f"\n[{name}] acc={accuracy_score(y, pred):.4f} macro_f1={f1_score(y, pred, average='macro', zero_division=0):.4f}")
        print(cm)
        print(f"false_closed_rate={false_closed_rate:.4f}, missed_closed_rate={missed_closed_rate:.4f}")
        return {
            "accuracy": float(accuracy_score(y, pred)),
            "macro_f1": float(f1_score(y, pred, average="macro", zero_division=0)),
            "weighted_f1": float(f1_score(y, pred, average="weighted", zero_division=0)),
            "precision": {LABEL_NAMES[i]: float(pr[i]) for i in range(2)},
            "recall": {LABEL_NAMES[i]: float(rc[i]) for i in range(2)},
            "f1": {LABEL_NAMES[i]: float(f1[i]) for i in range(2)},
            "support": {LABEL_NAMES[i]: int(sup[i]) for i in range(2)},
            "false_closed_rate": false_closed_rate,
            "missed_closed_rate": missed_closed_rate,
            "confusion_matrix": cm.tolist(),
        }

    metrics = {
        "train": eval_split("train", X_train, y_train),
        "val": eval_split("val", X_val, y_val),
        "test": eval_split("test", X_test, y_test),
    }

    scaler = model.named_steps["standardscaler"]
    clf = model.named_steps["linearsvc"]
    if list(clf.classes_) != [0, 1]:
        raise RuntimeError(f"Unexpected LinearSVC classes: {clf.classes_}. Expected [0, 1].")

    sigma = scaler.scale_.copy()
    sigma[sigma == 0] = 1.0
    # Binary LinearSVC has one hyperplane. decision_function > 0 means class 1 (closed).
    w_eff = (clf.coef_[0] / sigma).astype(np.float64)
    b_eff = float(clf.intercept_[0] - np.sum(clf.coef_[0] * scaler.mean_ / sigma))

    w_q = np.round(w_eff * int(args.weight_scale)).astype(np.int64)
    b_q = int(np.round(b_eff * int(args.weight_scale) * int(args.fixed_scale)))

    export = {
        "feature_cols": feature_cols,
        "classes": [0, 1],
        "class_names": LABEL_NAMES,
        "positive_class": "closed",
        "decision_rule": "pred_closed = decision_score > 0",
        "fixed_scale_for_input_x_q": int(args.fixed_scale),
        "weight_scale": int(args.weight_scale),
        "note": "score_q = sum(w_q * x_q) + b_q; x_q=round(x*fixed_scale); score_q>0 => closed.",
        "w_eff_float": w_eff.tolist(),
        "b_eff_float": b_eff,
        "w_q": w_q.tolist(),
        "b_q": b_q,
        "metrics": metrics,
    }
    (svm_dir / "linear_export_binary.json").write_text(json.dumps(export, indent=2, ensure_ascii=False), encoding="utf-8")

    with (svm_dir / "svm_weights_eyefeature_binary.h").open("w", encoding="utf-8") as f:
        f.write("#pragma once\n#include <stdint.h>\n\n")
        f.write("// Binary EyeFeature SVM. score_q > 0 => closed, else non_closed.\n")
        f.write(f"#define SVM_INPUT_DIM {len(feature_cols)}\n")
        f.write(f"#define SVM_INPUT_SCALE {int(args.fixed_scale)}\n")
        f.write(f"#define SVM_WEIGHT_SCALE {int(args.weight_scale)}\n\n")
        f.write("static const int32_t SVM_W[SVM_INPUT_DIM] = {")
        f.write(", ".join(str(int(x)) for x in w_q))
        f.write("};\n")
        f.write(f"static const int64_t SVM_B = {int(b_q)};\n")


def print_stats(name: str, df: pd.DataFrame) -> None:
    print(f"\n[{name}] samples={len(df)}")
    if len(df):
        print(df["label_name"].value_counts().to_string())
        if "orig_label_name" in df.columns:
            print("orig_label_name:")
            print(df["orig_label_name"].value_counts().to_string())
        print("source:")
        print(df["source"].value_counts().to_string())


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    feature_names = parse_list_arg(args.feature_names)
    if not feature_names:
        raise ValueError("--feature_names is empty")

    labels = load_csv(Path(args.eyeblink8_labels_csv), ["video_id", "frame_id", "is_blink", "is_closed", "is_valid"])
    eb_feat = load_csv(Path(args.eyeblink8_features_csv), ["video_id", "frame_id", "det_ok"])
    sr_feat = load_csv(Path(args.selfrec_features_csv), ["video_id", "frame_id", "det_ok"])
    intervals = load_csv(Path(args.manual_intervals_csv), ["video_id", "start_frame", "end_frame", "label"])
    validate_feature_names(eb_feat, feature_names, "eyeblink8 feature csv")
    validate_feature_names(sr_feat, feature_names, "selfrec feature csv")

    eb_windows = build_eyeblink8_nonclosed_windows(labels, eb_feat, feature_names, args)
    sr_windows = build_selfrec_closed_windows(sr_feat, intervals, feature_names, args)
    if eb_windows.empty:
        raise RuntimeError("No Eyeblink8 non_closed windows were built")
    if sr_windows.empty:
        raise RuntimeError("No selfrec closed windows were built")

    eb_windows.to_csv(out_dir / "windows_eyeblink8_nonclosed.csv", index=False, encoding="utf-8-sig")
    sr_windows.to_csv(out_dir / "windows_selfrec_closed.csv", index=False, encoding="utf-8-sig")

    eb_train, eb_val, eb_test = split_by_video(eb_windows, parse_list_arg(args.train_videos), parse_list_arg(args.val_videos), parse_list_arg(args.test_videos))
    sr_train, sr_val, sr_test = split_by_video(sr_windows, parse_list_arg(args.selfrec_train_videos), parse_list_arg(args.selfrec_val_videos), parse_list_arg(args.selfrec_test_videos))

    cols = list(eb_windows.columns)
    sr_train = sr_train.reindex(columns=cols)
    sr_val = sr_val.reindex(columns=cols)
    sr_test = sr_test.reindex(columns=cols)

    train_df = pd.concat([eb_train, sr_train], ignore_index=True)
    val_df = pd.concat([eb_val, sr_val], ignore_index=True)
    test_df = pd.concat([eb_test, sr_test], ignore_index=True)
    if args.shuffle_train:
        train_df = train_df.sample(frac=1.0, random_state=int(args.random_seed)).reset_index(drop=True)
    all_df = pd.concat([train_df, val_df, test_df], ignore_index=True)

    train_df.to_csv(out_dir / "train.csv", index=False, encoding="utf-8-sig")
    val_df.to_csv(out_dir / "val.csv", index=False, encoding="utf-8-sig")
    test_df.to_csv(out_dir / "test.csv", index=False, encoding="utf-8-sig")
    all_df.to_csv(out_dir / "windows_all_mixed.csv", index=False, encoding="utf-8-sig")

    feature_cols = get_train_feature_cols(train_df)
    summary = {
        "note": "Binary dataset: Eyeblink8 open/blink => non_closed; selfrec manual closed intervals => closed. Selfrec outside closed intervals is not used.",
        "eyeblink8_policy": str(args.eyeblink8_policy),
        "feature_names": feature_names,
        "feature_cols": feature_cols,
        "input_dim": len(feature_cols),
        "window_size": int(args.window_size),
        "central_size": int(args.central_size),
        "train_samples": int(len(train_df)),
        "val_samples": int(len(val_df)),
        "test_samples": int(len(test_df)),
        "train_label_counts": train_df["label_name"].value_counts().to_dict(),
        "val_label_counts": val_df["label_name"].value_counts().to_dict(),
        "test_label_counts": test_df["label_name"].value_counts().to_dict(),
        "train_orig_label_counts": train_df["orig_label_name"].value_counts().to_dict(),
        "val_orig_label_counts": val_df["orig_label_name"].value_counts().to_dict(),
        "test_orig_label_counts": test_df["orig_label_name"].value_counts().to_dict(),
        "selfrec_train_videos_used": sorted(sr_train["video_id"].dropna().astype(str).unique().tolist()),
        "selfrec_val_videos_used": sorted(sr_val["video_id"].dropna().astype(str).unique().tolist()),
        "selfrec_test_videos_used": sorted(sr_test["video_id"].dropna().astype(str).unique().tolist()),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print_stats("EYEBLINK8_NON_CLOSED", eb_windows)
    print_stats("SELFREC_CLOSED", sr_windows)
    print_stats("TRAIN", train_df)
    print_stats("VAL", val_df)
    print_stats("TEST", test_df)
    print(f"\n[DONE] binary dataset -> {out_dir}")
    print(f"[INFO] input_dim={len(feature_cols)} feature_cols={feature_cols[:3]} ... {feature_cols[-3:]}")

    if args.train_svm:
        train_binary_linear_svm(train_df, val_df, test_df, out_dir, args, feature_cols)


if __name__ == "__main__":
    main()
