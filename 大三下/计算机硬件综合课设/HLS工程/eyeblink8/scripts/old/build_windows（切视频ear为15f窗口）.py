from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd


LABEL_MAP_3CLASS = {
    "open": 0,
    "blink": 1,
    "closed": 2,
}

LABEL_MAP_BINARY = {
    "open": 0,
    "blink": 1,
}


def parse_list_arg(s: str) -> List[str]:
    return [x.strip() for x in s.split(",") if x.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge frame labels + frame EAR, then build 15-frame windows for SVM."
    )
    parser.add_argument(
        "--labels_csv",
        type=str,
        default="work/frame_labels.csv",
        help="Path to frame_labels.csv",
    )
    parser.add_argument(
        "--ear_csv",
        type=str,
        default="work_all/frame_ear.csv",
        help="Path to frame_ear.csv",
    )
    parser.add_argument(
        "--out_dir",
        type=str,
        default="work_dataset",
        help="Output folder",
    )
    parser.add_argument(
        "--task",
        type=str,
        default="three_class",
        choices=["three_class", "binary"],
        help="three_class: open/blink/closed, binary: open/blink",
    )
    parser.add_argument(
        "--window_size",
        type=int,
        default=15,
        help="Sliding window length",
    )
    parser.add_argument(
        "--central_size",
        type=int,
        default=7,
        help="Central decision span inside a window",
    )
    parser.add_argument(
        "--min_closed_in_central",
        type=int,
        default=4,
        help="For closed label: min closed frames in central span",
    )
    parser.add_argument(
        "--ear_min",
        type=float,
        default=0.10,
        help="Reject window if any EAR below this",
    )
    parser.add_argument(
        "--ear_max",
        type=float,
        default=0.60,
        help="Reject window if any EAR above this",
    )
    parser.add_argument(
        "--max_lr_diff",
        type=float,
        default=0.20,
        help="Reject frame if abs(ear_l - ear_r) is too large",
    )
    parser.add_argument(
        "--open_step",
        type=int,
        default=3,
        help="Keep only every N-th open window to reduce redundancy",
    )
    parser.add_argument(
        "--train_videos",
        type=str,
        default="1,2,3,4,8,9",
        help="Comma-separated video ids for train split",
    )
    parser.add_argument(
        "--val_videos",
        type=str,
        default="A",
        help="Comma-separated video ids for val split",
    )
    parser.add_argument(
        "--test_videos",
        type=str,
        default="B",
        help="Comma-separated video ids for test split",
    )
    return parser.parse_args()


def load_and_merge(labels_csv: Path, ear_csv: Path) -> pd.DataFrame:
    if not labels_csv.exists():
        raise FileNotFoundError(f"labels_csv not found: {labels_csv}")
    if not ear_csv.exists():
        raise FileNotFoundError(f"ear_csv not found: {ear_csv}")

    labels = pd.read_csv(labels_csv, dtype={"video_id": str})
    ear = pd.read_csv(ear_csv, dtype={"video_id": str})

    # 只保留需要的列
    labels_keep = [
        "video_id",
        "frame_id",
        "timestamp",
        "blink_id",
        "is_blink",
        "is_closed",
        "is_valid",
    ]
    ear_keep = [
        "video_id",
        "frame_id",
        "ear_l",
        "ear_r",
        "ear_avg",
        "det_ok",
    ]

    missing_labels = [c for c in labels_keep if c not in labels.columns]
    missing_ear = [c for c in ear_keep if c not in ear.columns]
    if missing_labels:
        raise ValueError(f"Missing columns in labels_csv: {missing_labels}")
    if missing_ear:
        raise ValueError(f"Missing columns in ear_csv: {missing_ear}")

    labels = labels[labels_keep].copy()
    ear = ear[ear_keep].copy()

    # 数值列转型
    for c in ["frame_id", "blink_id", "is_blink", "is_closed", "is_valid"]:
        labels[c] = pd.to_numeric(labels[c], errors="coerce")
    labels["timestamp"] = pd.to_numeric(labels["timestamp"], errors="coerce")

    for c in ["frame_id", "ear_l", "ear_r", "ear_avg", "det_ok"]:
        ear[c] = pd.to_numeric(ear[c], errors="coerce")

    merged = pd.merge(
        labels,
        ear,
        on=["video_id", "frame_id"],
        how="inner",
        validate="one_to_one",
    )

    merged = merged.sort_values(["video_id", "frame_id"]).reset_index(drop=True)
    return merged


def is_consecutive_frames(frame_ids: np.ndarray) -> bool:
    if len(frame_ids) <= 1:
        return True
    return bool(np.all(np.diff(frame_ids) == 1))


def classify_window(
    central: pd.DataFrame,
    task: str,
    min_closed_in_central: int,
) -> Optional[str]:
    closed_count = int(central["is_closed"].sum())
    blink_present = int(central["is_blink"].sum()) > 0

    # closed 优先级高于 blink
    if task == "three_class":
        if closed_count >= min_closed_in_central:
            return "closed"
        if blink_present:
            return "blink"
        if closed_count == 0 and not blink_present:
            return "open"
        return None

    # binary: 只保留 open / blink
    if blink_present and closed_count < min_closed_in_central:
        return "blink"
    if closed_count == 0 and not blink_present:
        return "open"
    return None


def build_windows(
    merged: pd.DataFrame,
    task: str,
    window_size: int,
    central_size: int,
    min_closed_in_central: int,
    ear_min: float,
    ear_max: float,
    max_lr_diff: float,
    open_step: int,
) -> pd.DataFrame:
    assert window_size % 2 == 1, "window_size must be odd"
    assert central_size % 2 == 1, "central_size must be odd"

    half_w = window_size // 2
    half_c = central_size // 2

    rows = []
    open_kept_counter = 0

    for video_id, dfv in merged.groupby("video_id", sort=True):
        dfv = dfv.sort_values("frame_id").reset_index(drop=True)

        for center_idx in range(half_w, len(dfv) - half_w):
            win = dfv.iloc[center_idx - half_w : center_idx + half_w + 1].copy()
            center_frame = int(dfv.iloc[center_idx]["frame_id"])

            # 1) 帧必须连续
            frame_ids = win["frame_id"].to_numpy()
            if not is_consecutive_frames(frame_ids):
                continue

            # 2) 每帧都需要有效标签与有效 EAR
            if win["det_ok"].isna().any() or (win["det_ok"] != 1).any():
                continue
            if win["is_valid"].isna().any() or (win["is_valid"] != 1).any():
                continue
            if win["ear_avg"].isna().any():
                continue
            if win["ear_l"].isna().any() or win["ear_r"].isna().any():
                continue

            # 3) EAR 合理范围过滤
            ear_vals = win["ear_avg"].to_numpy(dtype=float)
            if np.any(ear_vals < ear_min) or np.any(ear_vals > ear_max):
                continue

            # 4) 左右眼差异过滤
            lr_diff = np.abs(win["ear_l"].to_numpy(dtype=float) - win["ear_r"].to_numpy(dtype=float))
            if np.any(lr_diff > max_lr_diff):
                continue

            # 5) 中央决策区
            central = win.iloc[half_w - half_c : half_w + half_c + 1].copy()
            label_name = classify_window(
                central=central,
                task=task,
                min_closed_in_central=min_closed_in_central,
            )
            if label_name is None:
                continue

            # 6) 对 open 做降采样，减少冗余
            if label_name == "open":
                if open_kept_counter % max(1, open_step) != 0:
                    open_kept_counter += 1
                    continue
                open_kept_counter += 1

            # 7) 组装 15 维特征
            row = {
                "video_id": video_id,
                "center_frame": center_frame,
                "label_name": label_name,
                "label": LABEL_MAP_3CLASS[label_name] if task == "three_class" else LABEL_MAP_BINARY[label_name],
            }

            for i, ear in enumerate(ear_vals):
                row[f"ear_{i}"] = float(ear)

            rows.append(row)

    windows = pd.DataFrame(rows)
    return windows


def split_by_videos(
    windows: pd.DataFrame,
    train_videos: List[str],
    val_videos: List[str],
    test_videos: List[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_df = windows[windows["video_id"].isin(train_videos)].copy()
    val_df = windows[windows["video_id"].isin(val_videos)].copy()
    test_df = windows[windows["video_id"].isin(test_videos)].copy()
    return train_df, val_df, test_df


def print_stats(name: str, df: pd.DataFrame) -> None:
    print(f"\n[{name}] samples = {len(df)}")
    if len(df) == 0:
        return
    print(df["label_name"].value_counts(dropna=False).to_string())


def main() -> None:
    args = parse_args()

    labels_csv = Path(args.labels_csv)
    ear_csv = Path(args.ear_csv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    train_videos = parse_list_arg(args.train_videos)
    val_videos = parse_list_arg(args.val_videos)
    test_videos = parse_list_arg(args.test_videos)

    print("[INFO] Loading and merging frame-level data...")
    merged = load_and_merge(labels_csv=labels_csv, ear_csv=ear_csv)

    merged_out = out_dir / "frame_merged.csv"
    merged.to_csv(merged_out, index=False, encoding="utf-8-sig")
    print(f"[DONE] frame_merged.csv -> {merged_out}")

    print("[INFO] Building windows...")
    windows = build_windows(
        merged=merged,
        task=args.task,
        window_size=args.window_size,
        central_size=args.central_size,
        min_closed_in_central=args.min_closed_in_central,
        ear_min=args.ear_min,
        ear_max=args.ear_max,
        max_lr_diff=args.max_lr_diff,
        open_step=args.open_step,
    )

    if len(windows) == 0:
        raise RuntimeError("No valid windows were built. Try loosening the filter conditions.")

    windows_out = out_dir / "windows_all.csv"
    windows.to_csv(windows_out, index=False, encoding="utf-8-sig")
    print(f"[DONE] windows_all.csv -> {windows_out}")

    train_df, val_df, test_df = split_by_videos(
        windows=windows,
        train_videos=train_videos,
        val_videos=val_videos,
        test_videos=test_videos,
    )

    train_out = out_dir / "train.csv"
    val_out = out_dir / "val.csv"
    test_out = out_dir / "test.csv"

    train_df.to_csv(train_out, index=False, encoding="utf-8-sig")
    val_df.to_csv(val_out, index=False, encoding="utf-8-sig")
    test_df.to_csv(test_out, index=False, encoding="utf-8-sig")

    print(f"[DONE] train.csv -> {train_out}")
    print(f"[DONE] val.csv   -> {val_out}")
    print(f"[DONE] test.csv  -> {test_out}")

    print_stats("ALL", windows)
    print_stats("TRAIN", train_df)
    print_stats("VAL", val_df)
    print_stats("TEST", test_df)


if __name__ == "__main__":
    main()