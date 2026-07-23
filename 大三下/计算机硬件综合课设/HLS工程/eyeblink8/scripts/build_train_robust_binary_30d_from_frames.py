from __future__ import annotations

"""
Build a 30D binary SVM dataset from robust frame-level EyeFeature CSV files.

This is for constant-state recordings such as:
  data/robust_eye_dataset/session/open/*.avi
  data/robust_eye_dataset/session/closed/*.avi

First extract robust frame CSVs with extract_eyefeature_robust_all.py, then run:
  python scripts\\build_train_robust_binary_30d_from_frames.py ^
    --frame_csvs work_eyefeature_robust\\frame_robust.csv ^
    --out_dir work_dataset_robust_binary_30d ^
    --train_svm

The feature layout is robust_f0_0..robust_f0_14 followed by
robust_f1_0..robust_f1_14, matching the board-side f0_then_f1 SVM window.
"""

import argparse
import glob
import json
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

LABEL_MAP = {"non_closed": 0, "open": 0, "opened": 0, "closed": 1, "0": 0, "1": 1}
LABEL_NAMES = ["non_closed", "closed"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build robust 30D binary EyeFeature windows and optionally train linear SVM.")
    p.add_argument("--frame_csvs", type=str, required=True, help="Comma/semicolon-separated csv paths or glob patterns")
    p.add_argument("--out_dir", type=str, default="work_dataset_robust_binary_30d")
    p.add_argument("--feature_names", type=str, default="robust_f0,robust_f1")
    p.add_argument("--window_size", type=int, default=15)
    p.add_argument("--central_size", type=int, default=7)
    p.add_argument("--min_same_label_in_central", type=int, default=7)
    p.add_argument("--valid_columns", type=str, default="det_ok,eye_valid")
    p.add_argument("--split_mode", type=str, default="by_video", choices=["by_video", "by_window"])
    p.add_argument("--train_videos", type=str, default="", help="Optional video_id list for train split")
    p.add_argument("--val_videos", type=str, default="", help="Optional video_id list for val split")
    p.add_argument("--test_videos", type=str, default="", help="Optional video_id list for test split")
    p.add_argument("--train_frac", type=float, default=0.70)
    p.add_argument("--val_frac", type=float, default=0.15)
    p.add_argument("--test_frac", type=float, default=0.15)
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


def parse_paths_arg(s: str) -> List[Path]:
    items: List[str] = []
    for part in str(s).replace(";", ",").split(","):
        part = part.strip().strip('"')
        if part:
            items.append(part)
    paths: List[Path] = []
    for item in items:
        matches = sorted(glob.glob(item))
        if matches:
            paths.extend(Path(m) for m in matches)
        else:
            paths.append(Path(item))
    unique: Dict[str, Path] = {}
    for p in paths:
        unique[str(p.resolve())] = p
    return [unique[k] for k in sorted(unique)]


def is_consecutive_frames(frame_ids: np.ndarray) -> bool:
    if len(frame_ids) <= 1:
        return True
    return bool(np.all(np.diff(frame_ids) == 1))


def normalize_label_name(value) -> Tuple[str, int]:
    key = str(value).strip().lower()
    if key not in LABEL_MAP:
        raise ValueError(f"Unknown label value: {value!r}. Expected open/non_closed/closed/0/1.")
    label = int(LABEL_MAP[key])
    return ("closed" if label == 1 else "non_closed"), label


def load_frame_csvs(paths: Sequence[Path], feature_names: Sequence[str], valid_columns: Sequence[str]) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    required_base = ["video_id", "frame_id"] + list(feature_names)
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(f"missing frame csv: {path}")
        df = pd.read_csv(path, dtype={"video_id": str})
        missing = [c for c in required_base if c not in df.columns]
        if missing:
            raise ValueError(f"{path} missing columns: {missing}")
        if "label" not in df.columns and "label_name" not in df.columns:
            raise ValueError(f"{path} must contain label or label_name. Use extractor --label_name or parent open/closed folders.")
        for c in valid_columns:
            if c and c not in df.columns:
                raise ValueError(f"{path} missing valid column: {c}")

        if "label_name" in df.columns:
            labels = df["label_name"].apply(normalize_label_name)
            df["label_name"] = [x[0] for x in labels]
            df["label"] = [x[1] for x in labels]
        else:
            labels = df["label"].apply(normalize_label_name)
            df["label_name"] = [x[0] for x in labels]
            df["label"] = [x[1] for x in labels]

        df["source_csv"] = str(path)
        frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    for c in ["frame_id", "label"] + list(feature_names) + list(valid_columns):
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    return out


def add_window_features(row: dict, win: pd.DataFrame, feature_names: Sequence[str]) -> None:
    for name in feature_names:
        safe = name.replace("-", "_").replace(".", "_")
        vals = win[name].to_numpy(dtype=float)
        for i, v in enumerate(vals):
            row[f"{safe}_{i}"] = float(v)


def build_windows(df: pd.DataFrame, feature_names: Sequence[str], valid_columns: Sequence[str], args: argparse.Namespace) -> pd.DataFrame:
    half_w = int(args.window_size) // 2
    half_c = int(args.central_size) // 2
    min_same = int(args.min_same_label_in_central)
    rows: List[dict] = []
    df = df.sort_values(["video_id", "frame_id"]).reset_index(drop=True)

    for video_id, dfv in df.groupby("video_id", sort=True):
        dfv = dfv.sort_values("frame_id").reset_index(drop=True)
        for center_idx in range(half_w, len(dfv) - half_w):
            win = dfv.iloc[center_idx - half_w:center_idx + half_w + 1].copy()
            if not is_consecutive_frames(win["frame_id"].to_numpy(dtype=int)):
                continue
            bad = False
            for c in valid_columns:
                if c and (win[c].isna().any() or (win[c] != 1).any()):
                    bad = True
                    break
            if bad:
                continue
            if win[list(feature_names)].isna().any().any():
                continue

            central = win.iloc[half_w - half_c:half_w + half_c + 1].copy()
            counts = central["label"].astype(int).value_counts().to_dict()
            label = max(counts, key=lambda k: counts[k])
            if int(counts[label]) < min_same:
                continue
            label_name = LABEL_NAMES[int(label)]
            row = {
                "video_id": str(video_id),
                "center_frame": int(dfv.iloc[center_idx]["frame_id"]),
                "label_name": label_name,
                "label": int(label),
                "orig_label_name": label_name,
                "source": "robust_recording",
                "source_csv": str(dfv.iloc[center_idx].get("source_csv", "")),
            }
            add_window_features(row, win, feature_names)
            rows.append(row)
    return pd.DataFrame(rows)


def split_by_video_lists(df: pd.DataFrame, train_videos: List[str], val_videos: List[str], test_videos: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train = df[df["video_id"].astype(str).isin(train_videos)].copy()
    val = df[df["video_id"].astype(str).isin(val_videos)].copy()
    test = df[df["video_id"].astype(str).isin(test_videos)].copy()
    return train, val, test


def split_by_window(df: pd.DataFrame, args: argparse.Namespace) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(int(args.random_seed))
    train_idx: List[int] = []
    val_idx: List[int] = []
    test_idx: List[int] = []
    for _, dfl in df.groupby("label", sort=True):
        idx = dfl.index.to_numpy()
        rng.shuffle(idx)
        n = len(idx)
        n_train = int(round(n * float(args.train_frac)))
        n_val = int(round(n * float(args.val_frac)))
        n_train = min(max(0, n_train), n)
        n_val = min(max(0, n_val), n - n_train)
        train_idx.extend(idx[:n_train].tolist())
        val_idx.extend(idx[n_train:n_train + n_val].tolist())
        test_idx.extend(idx[n_train + n_val:].tolist())
    return df.loc[train_idx].copy(), df.loc[val_idx].copy(), df.loc[test_idx].copy()


def split_by_video_auto(df: pd.DataFrame, args: argparse.Namespace) -> Optional[Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]:
    rng = np.random.default_rng(int(args.random_seed))
    assignments: Dict[str, str] = {}
    for label, dfl in df.groupby("label", sort=True):
        vids = sorted(dfl["video_id"].astype(str).unique().tolist())
        if len(vids) < 3:
            return None
        rng.shuffle(vids)
        n = len(vids)
        n_train = max(1, int(round(n * float(args.train_frac))))
        n_val = max(1, int(round(n * float(args.val_frac))))
        if n_train + n_val >= n:
            n_train = max(1, n - 2)
            n_val = 1
        for vid in vids[:n_train]:
            assignments[vid] = "train"
        for vid in vids[n_train:n_train + n_val]:
            assignments[vid] = "val"
        for vid in vids[n_train + n_val:]:
            assignments[vid] = "test"
    split = df["video_id"].astype(str).map(assignments)
    return df[split == "train"].copy(), df[split == "val"].copy(), df[split == "test"].copy()


def get_train_feature_cols(df: pd.DataFrame) -> List[str]:
    meta = {"video_id", "center_frame", "label_name", "label", "orig_label_name", "source", "source_csv"}
    cols = [c for c in df.columns if c not in meta]

    def sort_key(c: str):
        base, idx = c.rsplit("_", 1)
        return base, int(idx) if idx.isdigit() else 0

    return sorted(cols, key=sort_key)


def print_stats(name: str, df: pd.DataFrame) -> None:
    print(f"\n[{name}] samples={len(df)}")
    if len(df):
        print(df["label_name"].value_counts().to_string())
        print("videos:")
        print(df["video_id"].value_counts().to_string())


def train_svm_if_requested(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame, out_dir: Path, args: argparse.Namespace, feature_cols: List[str]) -> None:
    if not bool(args.train_svm):
        return
    import sys

    script_dir = Path(__file__).resolve().parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    from build_train_binary_eyefeature_dataset import train_binary_linear_svm

    if train_df.empty or val_df.empty or test_df.empty:
        raise RuntimeError("Cannot train SVM: train/val/test must all be non-empty.")
    train_binary_linear_svm(train_df, val_df, test_df, out_dir, args, feature_cols)


def main() -> None:
    args = parse_args()
    frame_csvs = parse_paths_arg(args.frame_csvs)
    feature_names = parse_list_arg(args.feature_names)
    valid_columns = parse_list_arg(args.valid_columns)
    if len(feature_names) * int(args.window_size) != 30:
        raise ValueError("--feature_names count * --window_size must be 30 for the current PL SVM IP.")
    if int(args.central_size) > int(args.window_size):
        raise ValueError("--central_size must be <= --window_size")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    frames = load_frame_csvs(frame_csvs, feature_names, valid_columns)
    windows = build_windows(frames, feature_names, valid_columns, args)
    if windows.empty:
        raise RuntimeError("No robust windows were built. Check labels, det_ok/eye_valid, and feature columns.")

    train_videos = parse_list_arg(args.train_videos)
    val_videos = parse_list_arg(args.val_videos)
    test_videos = parse_list_arg(args.test_videos)
    if train_videos or val_videos or test_videos:
        train_df, val_df, test_df = split_by_video_lists(windows, train_videos, val_videos, test_videos)
        split_note = "explicit_video_lists"
    elif args.split_mode == "by_video":
        split = split_by_video_auto(windows, args)
        if split is None:
            print("[WARN] Fewer than 3 videos for at least one class; falling back to stratified by-window split.")
            train_df, val_df, test_df = split_by_window(windows, args)
            split_note = "by_window_fallback"
        else:
            train_df, val_df, test_df = split
            split_note = "by_video_auto"
    else:
        train_df, val_df, test_df = split_by_window(windows, args)
        split_note = "by_window"

    if args.shuffle_train and not train_df.empty:
        train_df = train_df.sample(frac=1.0, random_state=int(args.random_seed)).reset_index(drop=True)

    feature_cols = get_train_feature_cols(windows)
    windows.to_csv(out_dir / "windows_all_robust.csv", index=False, encoding="utf-8-sig")
    train_df.to_csv(out_dir / "train.csv", index=False, encoding="utf-8-sig")
    val_df.to_csv(out_dir / "val.csv", index=False, encoding="utf-8-sig")
    test_df.to_csv(out_dir / "test.csv", index=False, encoding="utf-8-sig")

    summary = {
        "note": "Robust binary 30D dataset from constant open/closed recordings.",
        "frame_csvs": [str(p) for p in frame_csvs],
        "feature_names": feature_names,
        "feature_cols": feature_cols,
        "input_dim": len(feature_cols),
        "window_size": int(args.window_size),
        "central_size": int(args.central_size),
        "min_same_label_in_central": int(args.min_same_label_in_central),
        "valid_columns": valid_columns,
        "split_note": split_note,
        "all_samples": int(len(windows)),
        "train_samples": int(len(train_df)),
        "val_samples": int(len(val_df)),
        "test_samples": int(len(test_df)),
        "all_label_counts": windows["label_name"].value_counts().to_dict(),
        "train_label_counts": train_df["label_name"].value_counts().to_dict() if len(train_df) else {},
        "val_label_counts": val_df["label_name"].value_counts().to_dict() if len(val_df) else {},
        "test_label_counts": test_df["label_name"].value_counts().to_dict() if len(test_df) else {},
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print_stats("ALL", windows)
    print_stats("TRAIN", train_df)
    print_stats("VAL", val_df)
    print_stats("TEST", test_df)
    print(f"\n[DONE] robust binary 30D dataset -> {out_dir}")
    print(f"[INFO] input_dim={len(feature_cols)} split={split_note}")

    train_svm_if_requested(train_df, val_df, test_df, out_dir, args, feature_cols)


if __name__ == "__main__":
    main()
