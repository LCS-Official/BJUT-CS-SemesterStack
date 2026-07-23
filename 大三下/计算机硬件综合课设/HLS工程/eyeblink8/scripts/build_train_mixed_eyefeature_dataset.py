from __future__ import annotations

"""
Build a mixed 3-class EyeFeature SVM dataset using the same idea as the previous EAR dataset:
  - Eyeblink8/raw contributes only open + blink windows, using official .tag-derived frame labels.
  - selfrec/raw_selfrec contributes only manually annotated closed windows.

The selfrec frames outside manual closed intervals are deliberately NOT used as open samples.

This script consumes frame-level EyeFeature CSVs produced by extract_eyefeature_hybrid_all.py.
It can also train a PL-friendly linear SVM immediately.

Typical Windows usage:
  cd C:\\Users\\LC\\Desktop\\eyeblink8

  # First generate Eyeblink8 official frame labels using your old script:
  python scripts\\parse_labels（解析eyeblink8元数据）.py --raw_dir raw --out_dir work

  # Then build + train a single-score 15D dataset:
  python scripts\\build_train_mixed_eyefeature_dataset.py ^
    --eyeblink8_labels_csv work\\frame_labels.csv ^
    --eyeblink8_features_csv work_eyefeature\\frame_eyefeature_eyeblink8.csv ^
    --selfrec_features_csv work_eyefeature\\frame_eyefeature_selfrec.csv ^
    --manual_intervals_csv work_selfrec\\manual_closed_intervals.csv ^
    --feature_names col_run_topk_fixed ^
    --legacy_ear_prefix ^
    --train_svm

  # Optional 30D version:
  python scripts\\build_train_mixed_eyefeature_dataset.py ^
    --feature_names col_run_topk_fixed,col_run_topk_adapt ^
    --out_dir work_dataset_eyefeature_30d ^
    --train_svm
"""

import argparse
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

LABEL_MAP = {"open": 0, "blink": 1, "closed": 2}
LABEL_NAMES = ["open", "blink", "closed"]

DEFAULT_SELFREC_TRAIN = "11,22,33,WIN_20260414_20_31_10_Pro,WIN_20260414_20_41_42_Pro,test1,test2"
DEFAULT_SELFREC_VAL = "WIN_20260414_20_42_23_Pro,test3"
DEFAULT_SELFREC_TEST = "WIN_20260414_21_29_13_Pro,test4"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build mixed EyeFeature windows and optionally train linear SVM.")
    p.add_argument("--eyeblink8_labels_csv", type=str, default="work/frame_labels.csv")
    p.add_argument("--eyeblink8_features_csv", type=str, default="work_eyefeature/frame_eyefeature_eyeblink8.csv")
    p.add_argument("--selfrec_features_csv", type=str, default="work_eyefeature/frame_eyefeature_selfrec.csv")
    p.add_argument("--manual_intervals_csv", type=str, default="work_selfrec/manual_closed_intervals.csv")
    p.add_argument("--out_dir", type=str, default="work_dataset_eyefeature_mixed")
    p.add_argument("--feature_names", type=str, default="col_run_topk_fixed", help="Comma-separated frame feature names")
    p.add_argument("--window_size", type=int, default=15)
    p.add_argument("--central_size", type=int, default=7)
    p.add_argument("--min_closed_in_central", type=int, default=6, help="Selfrec closed windows: min closed frames in central span")
    p.add_argument("--open_step", type=int, default=3, help="Keep every N-th Eyeblink8 open window")
    p.add_argument("--train_videos", type=str, default="1,2,3,4,8,9")
    p.add_argument("--val_videos", type=str, default="A")
    p.add_argument("--test_videos", type=str, default="B")
    p.add_argument("--selfrec_train_videos", type=str, default=DEFAULT_SELFREC_TRAIN)
    p.add_argument("--selfrec_val_videos", type=str, default=DEFAULT_SELFREC_VAL)
    p.add_argument("--selfrec_test_videos", type=str, default=DEFAULT_SELFREC_TEST)
    p.add_argument("--legacy_ear_prefix", action="store_true", help="For single feature only: write columns as ear_0..ear_14 so old train_svm scripts can read them")
    p.add_argument("--shuffle_train", action="store_true")
    p.add_argument("--random_seed", type=int, default=42)
    p.add_argument("--train_svm", action="store_true")
    p.add_argument("--C", type=float, default=1.0)
    p.add_argument("--class_weight", type=str, default="balanced", help="balanced, none, or e.g. open:1,blink:3,closed:2")
    p.add_argument("--max_iter", type=int, default=20000)
    p.add_argument("--fixed_scale", type=int, default=4096, help="Used only in exported metadata")
    p.add_argument("--weight_scale", type=int, default=1048576, help="Quantized export scale for folded weights")
    return p.parse_args()


def parse_list_arg(s: str) -> List[str]:
    return [x.strip() for x in str(s).split(",") if x.strip()]


def is_consecutive_frames(frame_ids: np.ndarray) -> bool:
    if len(frame_ids) <= 1:
        return True
    return bool(np.all(np.diff(frame_ids) == 1))


def load_csv(path: Path, required: List[str], dtype_video: bool = True) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing: {path}")
    df = pd.read_csv(path, dtype={"video_id": str} if dtype_video else None)
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{path} missing columns: {missing}")
    return df


def validate_feature_names(df: pd.DataFrame, feature_names: List[str], name: str) -> None:
    missing = [f for f in feature_names if f not in df.columns]
    if missing:
        raise ValueError(f"{name} missing feature columns: {missing}")


def out_feature_columns(feature_names: List[str], window_size: int, legacy_ear_prefix: bool) -> List[str]:
    if legacy_ear_prefix and len(feature_names) != 1:
        raise ValueError("--legacy_ear_prefix only supports a single --feature_names item")
    if legacy_ear_prefix:
        return [f"ear_{i}" for i in range(window_size)]
    if len(feature_names) == 1:
        return [f"eye_{i}" for i in range(window_size)]
    cols: List[str] = []
    for name in feature_names:
        safe = name.replace("-", "_").replace(".", "_")
        cols.extend([f"{safe}_{i}" for i in range(window_size)])
    return cols


def add_window_features(row: dict, win: pd.DataFrame, feature_names: List[str], legacy_ear_prefix: bool) -> None:
    n = len(win)
    if legacy_ear_prefix:
        vals = win[feature_names[0]].to_numpy(dtype=float)
        for i, v in enumerate(vals):
            row[f"ear_{i}"] = float(v)
        return
    if len(feature_names) == 1:
        vals = win[feature_names[0]].to_numpy(dtype=float)
        for i, v in enumerate(vals):
            row[f"eye_{i}"] = float(v)
        return
    for name in feature_names:
        safe = name.replace("-", "_").replace(".", "_")
        vals = win[name].to_numpy(dtype=float)
        for i in range(n):
            row[f"{safe}_{i}"] = float(vals[i])


def split_by_video(df: pd.DataFrame, train_videos: List[str], val_videos: List[str], test_videos: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train = df[df["video_id"].isin(train_videos)].copy()
    val = df[df["video_id"].isin(val_videos)].copy()
    test = df[df["video_id"].isin(test_videos)].copy()
    return train, val, test


def build_eyeblink8_openblink_windows(labels: pd.DataFrame, features: pd.DataFrame, feature_names: List[str], args: argparse.Namespace) -> pd.DataFrame:
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

            # Eyeblink8 only contributes open/blink.
            # Blink windows can include short closed-eye frames, but sustained closed is not treated as class 2 here.
            if blink_present:
                label_name = "blink"
            elif closed_count == 0:
                label_name = "open"
            else:
                continue

            if label_name == "open":
                if open_kept_counter % max(1, int(args.open_step)) != 0:
                    open_kept_counter += 1
                    continue
                open_kept_counter += 1

            row = {
                "video_id": str(video_id),
                "center_frame": int(dfv.iloc[center_idx]["frame_id"]),
                "label_name": label_name,
                "label": LABEL_MAP[label_name],
                "source": "eyeblink8",
            }
            add_window_features(row, win, feature_names, bool(args.legacy_ear_prefix))
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
                "source": "selfrec",
            }
            add_window_features(row, win, feature_names, bool(args.legacy_ear_prefix))
            rows.append(row)
    return pd.DataFrame(rows)


def parse_class_weight(s: str):
    s = str(s).strip()
    if s.lower() in {"", "none", "null"}:
        return None
    if s.lower() == "balanced":
        return "balanced"
    out: Dict[int, float] = {}
    name_to_id = {"open": 0, "blink": 1, "closed": 2, "0": 0, "1": 1, "2": 2}
    for item in s.split(","):
        if not item.strip():
            continue
        k, v = item.split(":")
        out[name_to_id[k.strip().lower()]] = float(v)
    return out


def get_train_feature_cols(df: pd.DataFrame) -> List[str]:
    meta = {"video_id", "center_frame", "label_name", "label", "source"}
    cols = [c for c in df.columns if c not in meta]
    # Prefer stable chronological ordering if legacy/single feature.
    if all(c.startswith("ear_") for c in cols):
        return sorted(cols, key=lambda x: int(x.split("_")[1]))
    if all(c.startswith("eye_") for c in cols):
        return sorted(cols, key=lambda x: int(x.split("_")[1]))
    def sort_key(c: str):
        base, idx = c.rsplit("_", 1)
        return base, int(idx) if idx.isdigit() else 0
    return sorted(cols, key=sort_key)


def train_linear_svm(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame, out_dir: Path, args: argparse.Namespace, feature_cols: List[str]) -> None:
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.svm import LinearSVC

    svm_dir = out_dir / "svm_linear"
    svm_dir.mkdir(parents=True, exist_ok=True)

    X_train = train_df[feature_cols].to_numpy(dtype=np.float64)
    y_train = train_df["label"].to_numpy(dtype=np.int64)
    X_val = val_df[feature_cols].to_numpy(dtype=np.float64)
    y_val = val_df["label"].to_numpy(dtype=np.int64)
    X_test = test_df[feature_cols].to_numpy(dtype=np.float64)
    y_test = test_df["label"].to_numpy(dtype=np.int64)

    model = make_pipeline(
        StandardScaler(),
        LinearSVC(C=float(args.C), class_weight=parse_class_weight(args.class_weight), dual=False, max_iter=int(args.max_iter), random_state=int(args.random_seed)),
    )
    model.fit(X_train, y_train)

    def eval_split(name: str, X: np.ndarray, y: np.ndarray) -> Dict[str, object]:
        pred = model.predict(X)
        cm = confusion_matrix(y, pred, labels=[0, 1, 2])
        report = classification_report(y, pred, labels=[0, 1, 2], target_names=LABEL_NAMES, digits=4, zero_division=0)
        (svm_dir / f"{name}_report.txt").write_text(report + "\n\nconfusion_matrix(labels=open,blink,closed):\n" + str(cm) + "\n", encoding="utf-8")
        print(f"\n[{name}] acc={accuracy_score(y, pred):.4f} macro_f1={f1_score(y, pred, average='macro', zero_division=0):.4f}")
        print(cm)
        return {
            "accuracy": float(accuracy_score(y, pred)),
            "macro_f1": float(f1_score(y, pred, average="macro", zero_division=0)),
            "weighted_f1": float(f1_score(y, pred, average="weighted", zero_division=0)),
            "confusion_matrix": cm.tolist(),
        }

    metrics = {
        "train": eval_split("train", X_train, y_train),
        "val": eval_split("val", X_val, y_val),
        "test": eval_split("test", X_test, y_test),
    }

    scaler = model.named_steps["standardscaler"]
    clf = model.named_steps["linearsvc"]
    sigma = scaler.scale_.copy()
    sigma[sigma == 0] = 1.0
    w_eff = clf.coef_ / sigma[None, :]
    b_eff = clf.intercept_ - (clf.coef_ * (scaler.mean_ / sigma)[None, :]).sum(axis=1)
    w_q = np.round(w_eff * int(args.weight_scale)).astype(np.int64)
    b_q = np.round(b_eff * int(args.weight_scale) * int(args.fixed_scale)).astype(np.int64)

    export = {
        "feature_cols": feature_cols,
        "classes": [0, 1, 2],
        "class_names": LABEL_NAMES,
        "fixed_scale_for_input_x_q": int(args.fixed_scale),
        "weight_scale": int(args.weight_scale),
        "note": "Integer score can be approximated as sum(w_q * x_q) + b_q, where x_q=round(x*fixed_scale).",
        "w_eff_float": w_eff.tolist(),
        "b_eff_float": b_eff.tolist(),
        "w_q": w_q.tolist(),
        "b_q": b_q.tolist(),
        "metrics": metrics,
    }
    (svm_dir / "linear_export.json").write_text(json.dumps(export, indent=2, ensure_ascii=False), encoding="utf-8")

    # Simple HLS-style header. User can copy arrays after choosing final feature set.
    with (svm_dir / "svm_weights_eyefeature.h").open("w", encoding="utf-8") as f:
        f.write("#pragma once\n#include <stdint.h>\n\n")
        f.write(f"#define SVM_NUM_CLASSES 3\n#define SVM_INPUT_DIM {len(feature_cols)}\n")
        f.write(f"#define SVM_INPUT_SCALE {int(args.fixed_scale)}\n#define SVM_WEIGHT_SCALE {int(args.weight_scale)}\n\n")
        f.write("static const int32_t SVM_W[SVM_NUM_CLASSES][SVM_INPUT_DIM] = {\n")
        for row in w_q:
            f.write("  {" + ", ".join(str(int(x)) for x in row) + "},\n")
        f.write("};\n")
        f.write("static const int64_t SVM_B[SVM_NUM_CLASSES] = {" + ", ".join(str(int(x)) for x in b_q) + "};\n")


def print_stats(name: str, df: pd.DataFrame) -> None:
    print(f"\n[{name}] samples={len(df)}")
    if len(df):
        print(df["label_name"].value_counts().to_string())
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

    eb_windows = build_eyeblink8_openblink_windows(labels, eb_feat, feature_names, args)
    sr_windows = build_selfrec_closed_windows(sr_feat, intervals, feature_names, args)
    if eb_windows.empty:
        raise RuntimeError("No Eyeblink8 open/blink windows were built")
    if sr_windows.empty:
        raise RuntimeError("No selfrec closed windows were built")

    eb_windows.to_csv(out_dir / "windows_eyeblink8_openblink.csv", index=False, encoding="utf-8-sig")
    sr_windows.to_csv(out_dir / "windows_selfrec_closed.csv", index=False, encoding="utf-8-sig")

    eb_train, eb_val, eb_test = split_by_video(eb_windows, parse_list_arg(args.train_videos), parse_list_arg(args.val_videos), parse_list_arg(args.test_videos))
    sr_train, sr_val, sr_test = split_by_video(sr_windows, parse_list_arg(args.selfrec_train_videos), parse_list_arg(args.selfrec_val_videos), parse_list_arg(args.selfrec_test_videos))

    # Align columns to be safe.
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
        "note": "Eyeblink8 contributes only open/blink. selfrec contributes only manually annotated closed windows.",
        "feature_names": feature_names,
        "feature_cols": feature_cols,
        "window_size": int(args.window_size),
        "central_size": int(args.central_size),
        "train_samples": int(len(train_df)),
        "val_samples": int(len(val_df)),
        "test_samples": int(len(test_df)),
        "train_label_counts": train_df["label_name"].value_counts().to_dict(),
        "val_label_counts": val_df["label_name"].value_counts().to_dict(),
        "test_label_counts": test_df["label_name"].value_counts().to_dict(),
        "selfrec_train_videos_used": sorted(sr_train["video_id"].dropna().astype(str).unique().tolist()),
        "selfrec_val_videos_used": sorted(sr_val["video_id"].dropna().astype(str).unique().tolist()),
        "selfrec_test_videos_used": sorted(sr_test["video_id"].dropna().astype(str).unique().tolist()),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print_stats("EYEBLINK8_OPENBLINK", eb_windows)
    print_stats("SELFREC_CLOSED", sr_windows)
    print_stats("TRAIN", train_df)
    print_stats("VAL", val_df)
    print_stats("TEST", test_df)
    print(f"\n[DONE] dataset -> {out_dir}")

    if args.train_svm:
        train_linear_svm(train_df, val_df, test_df, out_dir, args, feature_cols)


if __name__ == "__main__":
    main()
