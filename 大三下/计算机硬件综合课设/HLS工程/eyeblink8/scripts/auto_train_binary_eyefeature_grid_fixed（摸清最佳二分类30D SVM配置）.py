from __future__ import annotations

"""
Auto-train many 30D binary EyeFeature LinearSVM configurations.

Goal for this project:
  - Binary task: non_closed vs closed
  - Eyeblink8/raw contributes non_closed windows from official open/blink labels
  - selfrec/raw_selfrec contributes closed windows from manual closed intervals only
  - 30D input = two frame-level EyeFeature scores over a 15-frame window

Typical Windows usage:
  cd C:\\Users\\LC\\Desktop\\eyeblink8

  python scripts\\auto_train_binary_eyefeature_grid.py ^
    --eyeblink8_labels_csv work\\frame_labels.csv ^
    --eyeblink8_features_csv work_eyefeature\\frame_eyefeature_eyeblink8.csv ^
    --selfrec_features_csv work_eyefeature\\frame_eyefeature_selfrec.csv ^
    --manual_intervals_csv work_selfrec\\manual_closed_intervals.csv ^
    --out_dir work_autotune_binary_30d

Outputs:
  work_autotune_binary_30d/
    config_table.csv
    results_all.csv
    results_ranked.csv
    best_config.json
    best_model.joblib
    best_linear_export_binary.json
    best_svm_weights_eyefeature_binary.h
    best_threshold_report.txt
    best_train.csv / best_val.csv / best_test.csv
    dataset_cache/*.csv

HLS convention for exported best model:
  x_q[i] = round(x[i] * SVM_INPUT_SCALE)
  score_q = sum_i(SVM_W[i] * x_q[i]) + SVM_B_TUNED
  pred_closed = (score_q > 0)

Notes:
  - The tuned threshold is selected on VAL only, then folded into exported bias.
  - TEST is only used for reporting/ranking visibility, not for choosing threshold.
"""

import argparse
import hashlib
import itertools
import json
import math
import shutil
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from tqdm import tqdm

LABEL_MAP = {"non_closed": 0, "closed": 1}
LABEL_NAMES = ["non_closed", "closed"]

DEFAULT_SELFREC_TRAIN = "11,22,33,WIN_20260414_20_31_10_Pro,WIN_20260414_20_41_42_Pro,test1,test2"
DEFAULT_SELFREC_VAL = "WIN_20260414_20_42_23_Pro,test3"
DEFAULT_SELFREC_TEST = "WIN_20260414_21_29_13_Pro,test4"

DEFAULT_FEATURE_PAIRS = (
    "col_run_topk_fixed+col_run_topk_adapt;"
    "col_run_max_fixed+col_run_topk_adapt;"
    "col_run_topk_fixed+vertical_contrast;"
    "col_run_topk_fixed+h_edge_density"
)

DEFAULT_DATASET_RULES = (
    # name, central_size, min_closed_in_central, open_step, eyeblink8_policy
    "std_7_6_openstep3_blinkasnonclosed:7:6:3:open_blink_as_nonclosed;"
    "loose_5_4_openstep3_blinkasnonclosed:5:4:3:open_blink_as_nonclosed;"
    "strict_9_8_openstep3_blinkasnonclosed:9:8:3:open_blink_as_nonclosed;"
    "std_7_6_openstep5_blinkasnonclosed:7:6:5:open_blink_as_nonclosed;"
    "std_7_6_openonly:7:6:3:open_only"
)

DEFAULT_C_VALUES = "0.03,0.1,0.3,1,3"
DEFAULT_CLASS_WEIGHTS = "balanced;non_closed:1,closed:2;non_closed:1,closed:3;non_closed:1,closed:5"


@dataclass(frozen=True)
class DatasetRule:
    name: str
    central_size: int
    min_closed_in_central: int
    open_step: int
    eyeblink8_policy: str


@dataclass(frozen=True)
class Config:
    config_id: int
    feature_pair_name: str
    feature_names: Tuple[str, str]
    dataset_rule_name: str
    central_size: int
    min_closed_in_central: int
    open_step: int
    eyeblink8_policy: str
    C: float
    class_weight: str


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Auto grid-train 30D binary EyeFeature LinearSVM configs.")
    p.add_argument("--eyeblink8_labels_csv", type=str, default="work/frame_labels.csv")
    p.add_argument("--eyeblink8_features_csv", type=str, default="work_eyefeature/frame_eyefeature_eyeblink8.csv")
    p.add_argument("--selfrec_features_csv", type=str, default="work_eyefeature/frame_eyefeature_selfrec.csv")
    p.add_argument("--manual_intervals_csv", type=str, default="work_selfrec/manual_closed_intervals.csv")
    p.add_argument("--out_dir", type=str, default="work_autotune_binary_30d")

    p.add_argument("--feature_pairs", type=str, default=DEFAULT_FEATURE_PAIRS,
                   help="Semicolon-separated pairs, e.g. 'a+b;c+d'. Each pair gives 30D when window_size=15.")
    p.add_argument("--dataset_rules", type=str, default=DEFAULT_DATASET_RULES,
                   help="Semicolon-separated rules: name:central:minclosed:openstep:policy")
    p.add_argument("--C_values", type=str, default=DEFAULT_C_VALUES)
    p.add_argument("--class_weights", type=str, default=DEFAULT_CLASS_WEIGHTS,
                   help="Semicolon-separated: balanced;none;non_closed:1,closed:3")
    p.add_argument("--max_configs", type=int, default=0, help="0 means all configs. Useful for quick smoke tests.")

    p.add_argument("--window_size", type=int, default=15)
    p.add_argument("--train_videos", type=str, default="1,2,3,4,8,9")
    p.add_argument("--val_videos", type=str, default="A")
    p.add_argument("--test_videos", type=str, default="B")
    p.add_argument("--selfrec_train_videos", type=str, default=DEFAULT_SELFREC_TRAIN)
    p.add_argument("--selfrec_val_videos", type=str, default=DEFAULT_SELFREC_VAL)
    p.add_argument("--selfrec_test_videos", type=str, default=DEFAULT_SELFREC_TEST)

    p.add_argument("--shuffle_train", action="store_true", default=True)
    p.add_argument("--no_shuffle_train", action="store_false", dest="shuffle_train")
    p.add_argument("--random_seed", type=int, default=42)
    p.add_argument("--max_iter", type=int, default=20000)

    p.add_argument("--threshold_points", type=int, default=201)
    p.add_argument("--max_false_closed_rate", type=float, default=0.20,
                   help="VAL constraint for threshold selection. If possible, choose high recall under this false-closed rate.")
    p.add_argument("--min_val_closed_recall", type=float, default=0.0,
                   help="Optional VAL lower bound during threshold selection. 0 disables.")

    p.add_argument("--fixed_scale", type=int, default=4096)
    p.add_argument("--weight_scale", type=int, default=1048576)
    p.add_argument("--save_top_k", type=int, default=5, help="Save reports/exports for top K configs in top_configs/.")
    p.add_argument("--force_rebuild_cache", action="store_true")
    p.add_argument("--export_only_from_results", action="store_true",
                   help="Skip the 400-config training loop and only re-export best/top models from an existing results_ranked.csv.")
    return p.parse_args()


def parse_list_arg(s: str) -> List[str]:
    return [x.strip() for x in str(s).split(",") if x.strip()]


def parse_feature_pairs(s: str) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    for item in str(s).split(";"):
        item = item.strip()
        if not item:
            continue
        if "+" not in item:
            raise ValueError(f"Bad feature pair '{item}', expected a+b")
        a, b = [x.strip() for x in item.split("+", 1)]
        if not a or not b:
            raise ValueError(f"Bad feature pair '{item}'")
        out.append((a, b))
    return out


def parse_dataset_rules(s: str) -> List[DatasetRule]:
    out: List[DatasetRule] = []
    for item in str(s).split(";"):
        item = item.strip()
        if not item:
            continue
        parts = item.split(":")
        if len(parts) != 5:
            raise ValueError(f"Bad dataset rule '{item}', expected name:central:minclosed:openstep:policy")
        name, central, minclosed, openstep, policy = parts
        policy = policy.strip()
        if policy not in {"open_blink_as_nonclosed", "open_only"}:
            raise ValueError(f"Bad policy in rule '{item}'")
        out.append(DatasetRule(name.strip(), int(central), int(minclosed), int(openstep), policy))
    return out


def parse_float_list(s: str) -> List[float]:
    return [float(x.strip()) for x in str(s).split(",") if x.strip()]


def parse_str_list_semicolon(s: str) -> List[str]:
    return [x.strip() for x in str(s).split(";") if x.strip()]


def load_csv(path: Path, required: Sequence[str]) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing: {path}")
    df = pd.read_csv(path, dtype={"video_id": str})
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{path} missing columns: {missing}")
    return df


def validate_pair_columns(eb_feat: pd.DataFrame, sr_feat: pd.DataFrame, pairs: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    ok: List[Tuple[str, str]] = []
    for a, b in pairs:
        missing = [x for x in (a, b) if x not in eb_feat.columns or x not in sr_feat.columns]
        if missing:
            print(f"[WARN] skip feature pair {a}+{b}, missing columns: {missing}")
            continue
        ok.append((a, b))
    if not ok:
        raise ValueError("No valid feature pairs left. Check CSV columns or --feature_pairs.")
    return ok


def is_consecutive_frames(frame_ids: np.ndarray) -> bool:
    if len(frame_ids) <= 1:
        return True
    return bool(np.all(np.diff(frame_ids) == 1))


def add_window_features(row: dict, win: pd.DataFrame, feature_names: Sequence[str]) -> None:
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


def get_train_feature_cols(df: pd.DataFrame) -> List[str]:
    meta = {"video_id", "center_frame", "label_name", "label", "orig_label_name", "source"}
    cols = [c for c in df.columns if c not in meta]

    def sort_key(c: str):
        base, idx = c.rsplit("_", 1)
        return base, int(idx) if idx.isdigit() else 0

    return sorted(cols, key=sort_key)


def build_eyeblink8_nonclosed_windows(
    labels: pd.DataFrame,
    features: pd.DataFrame,
    feature_names: Sequence[str],
    window_size: int,
    central_size: int,
    open_step: int,
    eyeblink8_policy: str,
) -> pd.DataFrame:
    need_labels = ["video_id", "frame_id", "blink_id", "is_blink", "is_closed", "is_valid"]
    need_feats = ["video_id", "frame_id", "det_ok"] + list(feature_names)
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
    for c in ["frame_id", "det_ok"] + list(feature_names):
        feat[c] = pd.to_numeric(feat[c], errors="coerce")

    merged = pd.merge(lab, feat, on=["video_id", "frame_id"], how="inner", validate="one_to_one")
    merged = merged.sort_values(["video_id", "frame_id"]).reset_index(drop=True)

    half_w = window_size // 2
    half_c = central_size // 2
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
            if win[list(feature_names)].isna().any().any():
                continue

            central = win.iloc[half_w - half_c:half_w + half_c + 1].copy()
            blink_present = int(central["is_blink"].sum()) > 0
            closed_count = int(central["is_closed"].sum())

            if blink_present:
                orig_label_name = "blink"
                if eyeblink8_policy == "open_only":
                    continue
            elif closed_count == 0:
                orig_label_name = "open"
                if open_kept_counter % max(1, int(open_step)) != 0:
                    open_kept_counter += 1
                    continue
                open_kept_counter += 1
            else:
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


def build_selfrec_closed_windows(
    features: pd.DataFrame,
    intervals: pd.DataFrame,
    feature_names: Sequence[str],
    window_size: int,
    central_size: int,
    min_closed_in_central: int,
) -> pd.DataFrame:
    need_feats = ["video_id", "frame_id", "det_ok"] + list(feature_names)
    missing_f = [c for c in need_feats if c not in features.columns]
    if missing_f:
        raise ValueError(f"selfrec features missing columns: {missing_f}")
    need_intervals = ["video_id", "start_frame", "end_frame", "label"]
    missing_i = [c for c in need_intervals if c not in intervals.columns]
    if missing_i:
        raise ValueError(f"manual intervals missing columns: {missing_i}")

    feat = features[need_feats].copy()
    for c in ["frame_id", "det_ok"] + list(feature_names):
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

    half_w = window_size // 2
    half_c = central_size // 2
    rows: List[dict] = []

    for video_id, dfv in df.groupby("video_id", sort=True):
        dfv = dfv.sort_values("frame_id").reset_index(drop=True)
        for center_idx in range(half_w, len(dfv) - half_w):
            win = dfv.iloc[center_idx - half_w:center_idx + half_w + 1].copy()
            if not is_consecutive_frames(win["frame_id"].to_numpy(dtype=int)):
                continue
            if win["det_ok"].isna().any() or (win["det_ok"] != 1).any():
                continue
            if win[list(feature_names)].isna().any().any():
                continue
            central = win.iloc[half_w - half_c:half_w + half_c + 1].copy()
            closed_count = int(central["is_closed_manual"].sum())
            if closed_count < int(min_closed_in_central):
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


def safe_name(s: str) -> str:
    out = []
    for ch in str(s):
        if ch.isalnum() or ch in {"_", "-"}:
            out.append(ch)
        else:
            out.append("_")
    return "".join(out)


def dataset_cache_key(cfg: Config, args: argparse.Namespace) -> str:
    key = {
        "feature_names": cfg.feature_names,
        "window_size": int(args.window_size),
        "central_size": cfg.central_size,
        "min_closed_in_central": cfg.min_closed_in_central,
        "open_step": cfg.open_step,
        "eyeblink8_policy": cfg.eyeblink8_policy,
        "train_videos": parse_list_arg(args.train_videos),
        "val_videos": parse_list_arg(args.val_videos),
        "test_videos": parse_list_arg(args.test_videos),
        "selfrec_train_videos": parse_list_arg(args.selfrec_train_videos),
        "selfrec_val_videos": parse_list_arg(args.selfrec_val_videos),
        "selfrec_test_videos": parse_list_arg(args.selfrec_test_videos),
    }
    txt = json.dumps(key, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(txt.encode("utf-8")).hexdigest()[:12]


def build_or_load_dataset(
    cfg: Config,
    args: argparse.Namespace,
    labels: pd.DataFrame,
    eb_feat: pd.DataFrame,
    sr_feat: pd.DataFrame,
    intervals: pd.DataFrame,
    cache_dir: Path,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, List[str], Path]:
    key = dataset_cache_key(cfg, args)
    ds_dir = cache_dir / f"ds_{key}_{safe_name(cfg.feature_pair_name)}_{safe_name(cfg.dataset_rule_name)}"
    train_path, val_path, test_path = ds_dir / "train.csv", ds_dir / "val.csv", ds_dir / "test.csv"
    meta_path = ds_dir / "meta.json"

    if (not args.force_rebuild_cache) and train_path.exists() and val_path.exists() and test_path.exists():
        train_df = pd.read_csv(train_path, dtype={"video_id": str})
        val_df = pd.read_csv(val_path, dtype={"video_id": str})
        test_df = pd.read_csv(test_path, dtype={"video_id": str})
        feature_cols = get_train_feature_cols(train_df)
        return train_df, val_df, test_df, feature_cols, ds_dir

    ds_dir.mkdir(parents=True, exist_ok=True)
    eb_windows = build_eyeblink8_nonclosed_windows(
        labels, eb_feat, cfg.feature_names, int(args.window_size), cfg.central_size, cfg.open_step, cfg.eyeblink8_policy
    )
    sr_windows = build_selfrec_closed_windows(
        sr_feat, intervals, cfg.feature_names, int(args.window_size), cfg.central_size, cfg.min_closed_in_central
    )
    if eb_windows.empty or sr_windows.empty:
        raise RuntimeError(f"empty windows: eb={len(eb_windows)}, sr={len(sr_windows)}")

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

    if train_df.empty or val_df.empty or test_df.empty:
        raise RuntimeError(f"empty split: train={len(train_df)}, val={len(val_df)}, test={len(test_df)}")

    feature_cols = get_train_feature_cols(train_df)
    if len(feature_cols) != int(args.window_size) * 2:
        raise RuntimeError(f"Expected 30D with 2 features and window={args.window_size}; got dim={len(feature_cols)}")

    train_df.to_csv(train_path, index=False, encoding="utf-8-sig")
    val_df.to_csv(val_path, index=False, encoding="utf-8-sig")
    test_df.to_csv(test_path, index=False, encoding="utf-8-sig")
    pd.concat([train_df, val_df, test_df], ignore_index=True).to_csv(ds_dir / "windows_all_mixed.csv", index=False, encoding="utf-8-sig")

    meta = {
        "config": asdict(cfg),
        "input_dim": len(feature_cols),
        "feature_cols": feature_cols,
        "train_label_counts": train_df["label_name"].value_counts().to_dict(),
        "val_label_counts": val_df["label_name"].value_counts().to_dict(),
        "test_label_counts": test_df["label_name"].value_counts().to_dict(),
        "train_orig_label_counts": train_df["orig_label_name"].value_counts().to_dict(),
        "val_orig_label_counts": val_df["orig_label_name"].value_counts().to_dict(),
        "test_orig_label_counts": test_df["orig_label_name"].value_counts().to_dict(),
    }
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return train_df, val_df, test_df, feature_cols, ds_dir


def metric_from_cm(cm: np.ndarray) -> Dict[str, float]:
    tn, fp, fn, tp = cm.ravel()
    total = tn + fp + fn + tp
    acc = (tn + tp) / total if total else 0.0
    nonclosed_recall = tn / (tn + fp) if (tn + fp) else 0.0
    closed_recall = tp / (tp + fn) if (tp + fn) else 0.0
    nonclosed_precision = tn / (tn + fn) if (tn + fn) else 0.0
    closed_precision = tp / (tp + fp) if (tp + fp) else 0.0
    nonclosed_f1 = 2 * nonclosed_precision * nonclosed_recall / (nonclosed_precision + nonclosed_recall) if (nonclosed_precision + nonclosed_recall) else 0.0
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


def confusion_for_threshold(y: np.ndarray, scores: np.ndarray, threshold: float) -> np.ndarray:
    pred = (scores > threshold).astype(np.int64)
    # labels [0, 1]
    tn = int(((y == 0) & (pred == 0)).sum())
    fp = int(((y == 0) & (pred == 1)).sum())
    fn = int(((y == 1) & (pred == 0)).sum())
    tp = int(((y == 1) & (pred == 1)).sum())
    return np.array([[tn, fp], [fn, tp]], dtype=np.int64)


def make_thresholds(scores: np.ndarray, n: int) -> np.ndarray:
    scores = np.asarray(scores, dtype=float)
    if scores.size == 0 or np.all(~np.isfinite(scores)):
        return np.array([0.0])
    finite = scores[np.isfinite(scores)]
    qs = np.linspace(0.0, 1.0, max(3, int(n)))
    th = np.unique(np.quantile(finite, qs))
    # Add sentinel thresholds and default zero.
    eps = max(1e-6, float(np.std(finite)) * 1e-6)
    extra = np.array([finite.min() - eps, finite.max() + eps, 0.0])
    th = np.unique(np.concatenate([th, extra]))
    return th


def project_score(m: Dict[str, float]) -> float:
    # Project preference: catch real closed; false closed can be filtered by consecutive-frame logic but should not explode.
    return (
        0.45 * m["closed_recall"]
        + 0.20 * (1.0 - m["false_closed_rate"])
        + 0.20 * m["macro_f1"]
        + 0.15 * m["closed_f1"]
    )


def select_threshold(y_val: np.ndarray, val_scores: np.ndarray, args: argparse.Namespace) -> Tuple[float, Dict[str, float], pd.DataFrame]:
    rows = []
    for th in make_thresholds(val_scores, int(args.threshold_points)):
        cm = confusion_for_threshold(y_val, val_scores, float(th))
        m = metric_from_cm(cm)
        m["threshold"] = float(th)
        m["project_score"] = float(project_score(m))
        rows.append(m)
    df = pd.DataFrame(rows)
    candidates = df[df["false_closed_rate"] <= float(args.max_false_closed_rate)].copy()
    if float(args.min_val_closed_recall) > 0:
        candidates = candidates[candidates["closed_recall"] >= float(args.min_val_closed_recall)].copy()
    if len(candidates):
        # Under false-closed constraint, first maximize closed recall, then macro_f1, then closed_f1.
        cand = candidates.sort_values(
            ["closed_recall", "macro_f1", "closed_f1", "accuracy", "false_closed_rate"],
            ascending=[False, False, False, False, True],
        ).iloc[0]
    else:
        cand = df.sort_values(["project_score", "closed_recall", "macro_f1"], ascending=[False, False, False]).iloc[0]
    th = float(cand["threshold"])
    return th, cand.to_dict(), df


def eval_scores(y: np.ndarray, scores: np.ndarray, threshold: float) -> Dict[str, float]:
    cm = confusion_for_threshold(y, scores, threshold)
    m = metric_from_cm(cm)
    m["threshold"] = float(threshold)
    m["project_score"] = float(project_score(m))
    return m


def fit_and_eval_config(cfg: Config, train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame, feature_cols: List[str], args: argparse.Namespace):
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.svm import LinearSVC

    X_train = train_df[feature_cols].to_numpy(dtype=np.float64)
    y_train = train_df["label"].to_numpy(dtype=np.int64)
    X_val = val_df[feature_cols].to_numpy(dtype=np.float64)
    y_val = val_df["label"].to_numpy(dtype=np.int64)
    X_test = test_df[feature_cols].to_numpy(dtype=np.float64)
    y_test = test_df["label"].to_numpy(dtype=np.int64)

    model = make_pipeline(
        StandardScaler(),
        LinearSVC(
            C=float(cfg.C),
            class_weight=parse_class_weight(cfg.class_weight),
            dual=False,
            max_iter=int(args.max_iter),
            random_state=int(args.random_seed),
        ),
    )
    model.fit(X_train, y_train)

    train_scores = model.decision_function(X_train)
    val_scores = model.decision_function(X_val)
    test_scores = model.decision_function(X_test)

    threshold, threshold_val_metrics, sweep_df = select_threshold(y_val, val_scores, args)

    out: Dict[str, object] = {
        **asdict(cfg),
        "feature_names": "+".join(cfg.feature_names),
        "input_dim": int(len(feature_cols)),
        "train_samples": int(len(train_df)),
        "val_samples": int(len(val_df)),
        "test_samples": int(len(test_df)),
        "train_closed": int((y_train == 1).sum()),
        "val_closed": int((y_val == 1).sum()),
        "test_closed": int((y_test == 1).sum()),
        "best_threshold": float(threshold),
        "val_threshold_selected_by": "max_closed_recall_under_false_closed_constraint",
    }

    for split, y, scores in [
        ("train_tuned", y_train, train_scores),
        ("val_tuned", y_val, val_scores),
        ("test_tuned", y_test, test_scores),
        ("train_zero", y_train, train_scores),
        ("val_zero", y_val, val_scores),
        ("test_zero", y_test, test_scores),
    ]:
        th = threshold if split.endswith("tuned") else 0.0
        m = eval_scores(y, scores, th)
        for k, v in m.items():
            out[f"{split}_{k}"] = v

    # Ranking uses VAL tuned metrics only; TEST kept for sanity check.
    out["rank_score"] = float(out["val_tuned_project_score"])
    return model, out, sweep_df


def export_model(model, feature_cols: List[str], threshold: float, out_prefix: Path, args: argparse.Namespace, meta: Dict[str, object]) -> None:
    import joblib

    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    model_path = out_prefix.with_suffix(".joblib")
    joblib.dump(model, model_path)

    scaler = model.named_steps["standardscaler"]
    clf = model.named_steps["linearsvc"]
    sigma = scaler.scale_.copy()
    sigma[sigma == 0] = 1.0
    w_eff = (clf.coef_[0] / sigma).astype(np.float64)
    b_eff = float(clf.intercept_[0] - np.sum(clf.coef_[0] * scaler.mean_ / sigma))
    # Fold tuned threshold into bias: (w*x + b > threshold) == (w*x + b - threshold > 0)
    b_eff_tuned = float(b_eff - threshold)

    w_q = np.round(w_eff * int(args.weight_scale)).astype(np.int64)
    b_q_zero = int(np.round(b_eff * int(args.weight_scale) * int(args.fixed_scale)))
    b_q_tuned = int(np.round(b_eff_tuned * int(args.weight_scale) * int(args.fixed_scale)))
    th_q = int(np.round(float(threshold) * int(args.weight_scale) * int(args.fixed_scale)))

    export = {
        "feature_cols": feature_cols,
        "classes": [0, 1],
        "class_names": LABEL_NAMES,
        "positive_class": "closed",
        "decision_rule_zero": "raw score > 0 => closed",
        "decision_rule_tuned": "score_tuned = raw_score - best_threshold; score_tuned > 0 => closed",
        "best_threshold_float": float(threshold),
        "fixed_scale_for_input_x_q": int(args.fixed_scale),
        "weight_scale": int(args.weight_scale),
        "note": "Use tuned bias for deployment: score_q = sum(w_q*x_q)+SVM_B_TUNED; score_q>0 => closed.",
        "w_eff_float": w_eff.tolist(),
        "b_eff_float_zero_threshold": b_eff,
        "b_eff_float_tuned": b_eff_tuned,
        "w_q": w_q.tolist(),
        "b_q_zero_threshold": b_q_zero,
        "threshold_q": th_q,
        "b_q_tuned": b_q_tuned,
        "meta": meta,
    }
    out_prefix.with_name(out_prefix.name + "_linear_export_binary.json").write_text(
        json.dumps(export, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    with out_prefix.with_name(out_prefix.name + "_svm_weights_eyefeature_binary.h").open("w", encoding="utf-8") as f:
        f.write("#pragma once\n#include <stdint.h>\n\n")
        f.write("// Binary EyeFeature SVM. Tuned deployment bias is folded: score_q > 0 => closed.\n")
        f.write(f"#define SVM_INPUT_DIM {len(feature_cols)}\n")
        f.write(f"#define SVM_INPUT_SCALE {int(args.fixed_scale)}\n")
        f.write(f"#define SVM_WEIGHT_SCALE {int(args.weight_scale)}\n")
        f.write(f"#define SVM_BEST_THRESHOLD_FLOAT {float(threshold):.9g}\n\n")
        f.write("static const int32_t SVM_W[SVM_INPUT_DIM] = {")
        f.write(", ".join(str(int(x)) for x in w_q))
        f.write("};\n")
        f.write(f"static const int64_t SVM_B_ZERO_THRESHOLD = {int(b_q_zero)};\n")
        f.write(f"static const int64_t SVM_THRESHOLD_Q = {int(th_q)};\n")
        f.write(f"static const int64_t SVM_B_TUNED = {int(b_q_tuned)};\n")


def build_config_table(feature_pairs: List[Tuple[str, str]], rules: List[DatasetRule], C_values: List[float], class_weights: List[str], args: argparse.Namespace) -> List[Config]:
    configs: List[Config] = []
    cid = 0
    for pair, rule, C, cw in itertools.product(feature_pairs, rules, C_values, class_weights):
        cid += 1
        configs.append(
            Config(
                config_id=cid,
                feature_pair_name="+".join(pair),
                feature_names=(pair[0], pair[1]),
                dataset_rule_name=rule.name,
                central_size=int(rule.central_size),
                min_closed_in_central=int(rule.min_closed_in_central),
                open_step=int(rule.open_step),
                eyeblink8_policy=rule.eyeblink8_policy,
                C=float(C),
                class_weight=str(cw),
            )
        )
    if int(args.max_configs) > 0:
        configs = configs[: int(args.max_configs)]
    return configs


def write_best_report(out_dir: Path, best_row: pd.Series, results_ranked: pd.DataFrame) -> None:
    lines = []
    lines.append("# Binary 30D EyeFeature AutoTune Best Result\n")
    lines.append("## Best config\n")
    keys = [
        "config_id", "feature_names", "dataset_rule_name", "central_size", "min_closed_in_central",
        "open_step", "eyeblink8_policy", "C", "class_weight", "best_threshold", "rank_score",
    ]
    for k in keys:
        lines.append(f"- {k}: {best_row.get(k)}")
    lines.append("\n## Key metrics\n")
    metric_keys = [
        "val_tuned_accuracy", "val_tuned_macro_f1", "val_tuned_closed_precision", "val_tuned_closed_recall",
        "val_tuned_false_closed_rate", "val_tuned_missed_closed_rate",
        "test_tuned_accuracy", "test_tuned_macro_f1", "test_tuned_closed_precision", "test_tuned_closed_recall",
        "test_tuned_false_closed_rate", "test_tuned_missed_closed_rate",
        "test_zero_closed_recall", "test_zero_false_closed_rate",
    ]
    for k in metric_keys:
        v = best_row.get(k)
        if isinstance(v, float):
            lines.append(f"- {k}: {v:.6f}")
        else:
            lines.append(f"- {k}: {v}")
    lines.append("\n## Top 10 configs\n")
    top_cols = [
        "config_id", "feature_names", "dataset_rule_name", "C", "class_weight", "best_threshold",
        "rank_score", "val_tuned_closed_recall", "val_tuned_false_closed_rate", "val_tuned_macro_f1",
        "test_tuned_closed_recall", "test_tuned_false_closed_rate", "test_tuned_macro_f1",
    ]
    lines.append(results_ranked.head(10)[top_cols].to_string(index=False))
    (out_dir / "best_threshold_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = out_dir / "dataset_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    print("[INFO] Loading CSV files...")
    labels = load_csv(Path(args.eyeblink8_labels_csv), ["video_id", "frame_id", "is_blink", "is_closed", "is_valid"])
    eb_feat = load_csv(Path(args.eyeblink8_features_csv), ["video_id", "frame_id", "det_ok"])
    sr_feat = load_csv(Path(args.selfrec_features_csv), ["video_id", "frame_id", "det_ok"])
    intervals = load_csv(Path(args.manual_intervals_csv), ["video_id", "start_frame", "end_frame", "label"])

    feature_pairs = validate_pair_columns(eb_feat, sr_feat, parse_feature_pairs(args.feature_pairs))
    rules = parse_dataset_rules(args.dataset_rules)
    C_values = parse_float_list(args.C_values)
    class_weights = parse_str_list_semicolon(args.class_weights)
    configs = build_config_table(feature_pairs, rules, C_values, class_weights, args)

    cfg_df = pd.DataFrame([asdict(c) | {"feature_names": "+".join(c.feature_names)} for c in configs])
    cfg_df.to_csv(out_dir / "config_table.csv", index=False, encoding="utf-8-sig")
    print(f"[INFO] configs={len(configs)}; feature_pairs={len(feature_pairs)}; dataset_rules={len(rules)}")
    print(f"[INFO] config table -> {out_dir / 'config_table.csv'}")

    results: List[Dict[str, object]] = []
    failures: List[Dict[str, object]] = []

    # Keep best info; export after final ranking by retraining or from stored best model.
    best_model = None
    best_train = best_val = best_test = None
    best_feature_cols: Optional[List[str]] = None
    best_sweep = None
    best_result: Optional[Dict[str, object]] = None
    best_ds_dir: Optional[Path] = None

    sort_cols = ["rank_score", "val_tuned_closed_recall", "val_tuned_macro_f1", "val_tuned_false_closed_rate"]

    if args.export_only_from_results:
        ranked_path = out_dir / "results_ranked.csv"
        if not ranked_path.exists():
            raise FileNotFoundError(f"--export_only_from_results requires existing {ranked_path}")
        print(f"[INFO] export_only_from_results: loading {ranked_path}")
        ranked = pd.read_csv(ranked_path)
        if ranked.empty:
            raise RuntimeError(f"{ranked_path} is empty")

        best_row = ranked.iloc[0]
        cfg_match = [c for c in configs if int(c.config_id) == int(best_row["config_id"])][0]
        best_train, best_val, best_test, best_feature_cols, best_ds_dir = build_or_load_dataset(
            cfg_match, args, labels, eb_feat, sr_feat, intervals, cache_dir
        )
        best_model, row, best_sweep = fit_and_eval_config(
            cfg_match, best_train, best_val, best_test, best_feature_cols, args
        )
        row["status"] = "ok"
        row["dataset_cache_dir"] = str(best_ds_dir)
        # Keep the threshold/metrics as recomputed from the same cached dataset and args.
        best_row = pd.Series(row)
    else:
        pbar = tqdm(configs, desc="Training configs", unit="cfg")
        for cfg in pbar:
            pbar.set_postfix_str(f"{cfg.config_id}/{len(configs)} {cfg.feature_pair_name} C={cfg.C} cw={cfg.class_weight}")
            try:
                train_df, val_df, test_df, feature_cols, ds_dir = build_or_load_dataset(cfg, args, labels, eb_feat, sr_feat, intervals, cache_dir)
                model, row, sweep_df = fit_and_eval_config(cfg, train_df, val_df, test_df, feature_cols, args)
                row["status"] = "ok"
                row["dataset_cache_dir"] = str(ds_dir)
                results.append(row)
                if best_result is None or float(row["rank_score"]) > float(best_result["rank_score"]):
                    best_result = row
                    best_model = model
                    best_train, best_val, best_test = train_df.copy(), val_df.copy(), test_df.copy()
                    best_feature_cols = list(feature_cols)
                    best_sweep = sweep_df.copy()
                    best_ds_dir = ds_dir
            except Exception as e:
                failures.append({**asdict(cfg), "feature_names": "+".join(cfg.feature_names), "status": "failed", "error": repr(e)})
                tqdm.write(f"[WARN] config {cfg.config_id} failed: {e}")

            # Periodic checkpoint.
            if len(results) and len(results) % 10 == 0:
                pd.DataFrame(results).to_csv(out_dir / "results_all_checkpoint.csv", index=False, encoding="utf-8-sig")
                if failures:
                    pd.DataFrame(failures).to_csv(out_dir / "failures_checkpoint.csv", index=False, encoding="utf-8-sig")

        if not results:
            raise RuntimeError("All configs failed. See failures_checkpoint.csv if present.")

        res_df = pd.DataFrame(results)
        fail_df = pd.DataFrame(failures) if failures else pd.DataFrame()
        res_df.to_csv(out_dir / "results_all.csv", index=False, encoding="utf-8-sig")
        if not fail_df.empty:
            fail_df.to_csv(out_dir / "failures.csv", index=False, encoding="utf-8-sig")

        ranked = res_df.sort_values(sort_cols, ascending=[False, False, False, True]).reset_index(drop=True)
        ranked.to_csv(out_dir / "results_ranked.csv", index=False, encoding="utf-8-sig")

        best_row = ranked.iloc[0]
        # If best was not the in-memory best due tie-sort, retrain exact best for export.
        if best_result is None or int(best_result["config_id"]) != int(best_row["config_id"]):
            cfg_match = [c for c in configs if int(c.config_id) == int(best_row["config_id"])][0]
            best_train, best_val, best_test, best_feature_cols, best_ds_dir = build_or_load_dataset(cfg_match, args, labels, eb_feat, sr_feat, intervals, cache_dir)
            best_model, row, best_sweep = fit_and_eval_config(cfg_match, best_train, best_val, best_test, best_feature_cols, args)
            best_result = row

    assert best_model is not None and best_train is not None and best_val is not None and best_test is not None and best_feature_cols is not None and best_sweep is not None

    # Save best datasets and artifacts.
    best_train.to_csv(out_dir / "best_train.csv", index=False, encoding="utf-8-sig")
    best_val.to_csv(out_dir / "best_val.csv", index=False, encoding="utf-8-sig")
    best_test.to_csv(out_dir / "best_test.csv", index=False, encoding="utf-8-sig")
    best_sweep.to_csv(out_dir / "best_val_threshold_sweep.csv", index=False, encoding="utf-8-sig")

    best_meta = {k: (v.item() if hasattr(v, "item") else v) for k, v in dict(best_row).items()}
    (out_dir / "best_config.json").write_text(json.dumps(best_meta, indent=2, ensure_ascii=False), encoding="utf-8")

    export_model(best_model, best_feature_cols, float(best_row["best_threshold"]), out_dir / "best_model", args, best_meta)
    # Convenience copy names requested by many scripts.
    for src_name, dst_name in [
        ("best_model.joblib", "best_model.joblib"),
        ("best_model_linear_export_binary.json", "best_linear_export_binary.json"),
        ("best_model_svm_weights_eyefeature_binary.h", "best_svm_weights_eyefeature_binary.h"),
    ]:
        src = out_dir / src_name
        dst = out_dir / dst_name
        if src.exists() and src != dst:
            shutil.copyfile(src, dst)

    write_best_report(out_dir, best_row, ranked)

    # Export top K models/reports by retraining to avoid storing every model.
    top_dir = out_dir / "top_configs"
    top_dir.mkdir(exist_ok=True)
    for rank_idx, (_, r) in enumerate(tqdm(ranked.head(max(0, int(args.save_top_k))).iterrows(), total=min(int(args.save_top_k), len(ranked)), desc="Saving top models", unit="model"), start=1):
        cfg_match = [c for c in configs if int(c.config_id) == int(r["config_id"])][0]
        train_df, val_df, test_df, feature_cols, ds_dir = build_or_load_dataset(cfg_match, args, labels, eb_feat, sr_feat, intervals, cache_dir)
        model, row, sweep_df = fit_and_eval_config(cfg_match, train_df, val_df, test_df, feature_cols, args)
        sub = top_dir / f"rank_{rank_idx:02d}_cfg_{int(r['config_id']):04d}"
        sub.mkdir(exist_ok=True)
        sweep_df.to_csv(sub / "val_threshold_sweep.csv", index=False, encoding="utf-8-sig")
        (sub / "config_result.json").write_text(json.dumps(row, indent=2, ensure_ascii=False), encoding="utf-8")
        export_model(model, feature_cols, float(row["best_threshold"]), sub / "model", args, row)

    print("\n[DONE] AutoTune finished")
    print(f"[BEST] config_id={int(best_row['config_id'])} feature={best_row['feature_names']} rule={best_row['dataset_rule_name']} C={best_row['C']} cw={best_row['class_weight']}")
    print(f"[BEST] threshold={float(best_row['best_threshold']):+.6f}")
    print(f"[VAL] closed_recall={float(best_row['val_tuned_closed_recall']):.4f}, false_closed={float(best_row['val_tuned_false_closed_rate']):.4f}, macro_f1={float(best_row['val_tuned_macro_f1']):.4f}")
    print(f"[TEST] closed_recall={float(best_row['test_tuned_closed_recall']):.4f}, false_closed={float(best_row['test_tuned_false_closed_rate']):.4f}, macro_f1={float(best_row['test_tuned_macro_f1']):.4f}")
    print(f"[OUT] {out_dir}")


if __name__ == "__main__":
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FutureWarning)
        main()
