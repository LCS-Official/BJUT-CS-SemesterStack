from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build frame-level manual closed labels and 15-frame closed windows from self-recorded EAR data."
    )
    parser.add_argument(
        "--ear_csv",
        type=str,
        default="work_selfrec/frame_ear_selfrec.csv",
        help="Merged self-recorded frame EAR csv",
    )
    parser.add_argument(
        "--intervals_csv",
        type=str,
        default="work_selfrec/manual_closed_intervals.csv",
        help="Manual closed interval annotations",
    )
    parser.add_argument(
        "--out_dir",
        type=str,
        default="work_selfrec_labeled",
        help="Output folder",
    )
    parser.add_argument(
        "--window_size",
        type=int,
        default=15,
        help="Sliding window size",
    )
    parser.add_argument(
        "--central_size",
        type=int,
        default=7,
        help="Central decision region size",
    )
    parser.add_argument(
        "--min_closed_in_central",
        type=int,
        default=6,
        help="Min manually-closed frames in central region to accept a closed window",
    )
    parser.add_argument(
        "--ear_min",
        type=float,
        default=0.05,
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
        help="Reject window if abs(ear_l - ear_r) too large on any frame",
    )
    return parser.parse_args()


def ensure_template(intervals_csv: Path) -> None:
    if intervals_csv.exists():
        return

    intervals_csv.parent.mkdir(parents=True, exist_ok=True)
    template = pd.DataFrame(
        [
            {
                "video_id": "11",
                "start_frame": 120,
                "end_frame": 215,
                "label": "closed",
                "notes": "stable closed example",
            }
        ]
    )
    template.to_csv(intervals_csv, index=False, encoding="utf-8-sig")
    raise FileNotFoundError(
        f"{intervals_csv} not found.\n"
        f"A template has been created for you. Please edit it first, then rerun."
    )


def is_consecutive_frames(frame_ids: np.ndarray) -> bool:
    if len(frame_ids) <= 1:
        return True
    return bool(np.all(np.diff(frame_ids) == 1))


def load_data(ear_csv: Path, intervals_csv: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not ear_csv.exists():
        raise FileNotFoundError(f"ear_csv not found: {ear_csv}")

    ensure_template(intervals_csv)

    ear_df = pd.read_csv(ear_csv, dtype={"video_id": str})
    intervals_df = pd.read_csv(intervals_csv, dtype={"video_id": str})

    needed_ear = [
        "video_id",
        "frame_id",
        "timestamp_sec",
        "ear_l",
        "ear_r",
        "ear_avg",
        "det_ok",
    ]
    missing_ear = [c for c in needed_ear if c not in ear_df.columns]
    if missing_ear:
        raise ValueError(f"Missing columns in ear_csv: {missing_ear}")

    needed_intervals = ["video_id", "start_frame", "end_frame", "label"]
    missing_intervals = [c for c in needed_intervals if c not in intervals_df.columns]
    if missing_intervals:
        raise ValueError(f"Missing columns in intervals_csv: {missing_intervals}")

    for c in ["frame_id", "det_ok", "ear_l", "ear_r", "ear_avg", "timestamp_sec"]:
        ear_df[c] = pd.to_numeric(ear_df[c], errors="coerce")

    for c in ["start_frame", "end_frame"]:
        intervals_df[c] = pd.to_numeric(intervals_df[c], errors="coerce")

    intervals_df = intervals_df.dropna(subset=["start_frame", "end_frame"]).copy()
    intervals_df["start_frame"] = intervals_df["start_frame"].astype(int)
    intervals_df["end_frame"] = intervals_df["end_frame"].astype(int)

    intervals_df = intervals_df[intervals_df["label"].astype(str).str.lower() == "closed"].copy()
    intervals_df = intervals_df.sort_values(["video_id", "start_frame"]).reset_index(drop=True)

    return ear_df, intervals_df


def expand_manual_closed(ear_df: pd.DataFrame, intervals_df: pd.DataFrame) -> pd.DataFrame:
    df = ear_df.copy()
    df["is_closed_manual"] = 0
    df["manual_source"] = ""

    for _, row in intervals_df.iterrows():
        video_id = str(row["video_id"])
        start_f = int(row["start_frame"])
        end_f = int(row["end_frame"])

        if end_f < start_f:
            start_f, end_f = end_f, start_f

        mask = (
            (df["video_id"] == video_id) &
            (df["frame_id"] >= start_f) &
            (df["frame_id"] <= end_f)
        )
        df.loc[mask, "is_closed_manual"] = 1
        df.loc[mask, "manual_source"] = "selfrec_closed_interval"

    return df.sort_values(["video_id", "frame_id"]).reset_index(drop=True)


def build_closed_windows(
    df: pd.DataFrame,
    window_size: int,
    central_size: int,
    min_closed_in_central: int,
    ear_min: float,
    ear_max: float,
    max_lr_diff: float,
) -> pd.DataFrame:
    assert window_size % 2 == 1, "window_size must be odd"
    assert central_size % 2 == 1, "central_size must be odd"

    half_w = window_size // 2
    half_c = central_size // 2

    rows: List[dict] = []

    for video_id, dfv in df.groupby("video_id", sort=True):
        dfv = dfv.sort_values("frame_id").reset_index(drop=True)

        for center_idx in range(half_w, len(dfv) - half_w):
            win = dfv.iloc[center_idx - half_w : center_idx + half_w + 1].copy()
            center_frame = int(dfv.iloc[center_idx]["frame_id"])

            frame_ids = win["frame_id"].to_numpy()
            if not is_consecutive_frames(frame_ids):
                continue

            if win["det_ok"].isna().any() or (win["det_ok"] != 1).any():
                continue
            if win["ear_avg"].isna().any() or win["ear_l"].isna().any() or win["ear_r"].isna().any():
                continue

            ear_vals = win["ear_avg"].to_numpy(dtype=float)
            if np.any(ear_vals < ear_min) or np.any(ear_vals > ear_max):
                continue

            lr_diff = np.abs(win["ear_l"].to_numpy(dtype=float) - win["ear_r"].to_numpy(dtype=float))
            if np.any(lr_diff > max_lr_diff):
                continue

            central = win.iloc[half_w - half_c : half_w + half_c + 1].copy()
            closed_count = int(central["is_closed_manual"].sum())

            if closed_count < min_closed_in_central:
                continue

            row = {
                "video_id": video_id,
                "center_frame": center_frame,
                "label_name": "closed",
                "label": 2,
                "source": "selfrec",
            }

            for i, ear in enumerate(ear_vals):
                row[f"ear_{i}"] = float(ear)

            rows.append(row)

    return pd.DataFrame(rows)


def print_stats(frame_df: pd.DataFrame, windows_df: pd.DataFrame) -> None:
    print("\n[FRAME LEVEL]")
    print(f"total_frames        = {len(frame_df)}")
    print(f"manual_closed_frames= {int(frame_df['is_closed_manual'].sum())}")

    print("\n[WINDOW LEVEL]")
    print(f"closed_windows      = {len(windows_df)}")
    if len(windows_df) > 0:
        print(windows_df["video_id"].value_counts().sort_index().to_string())


def main() -> None:
    args = parse_args()

    ear_csv = Path(args.ear_csv)
    intervals_csv = Path(args.intervals_csv)
    out_dir = Path(args.out_dir)
    per_video_dir = out_dir / "per_video_frame_labels"

    out_dir.mkdir(parents=True, exist_ok=True)
    per_video_dir.mkdir(parents=True, exist_ok=True)

    ear_df, intervals_df = load_data(ear_csv=ear_csv, intervals_csv=intervals_csv)

    frame_df = expand_manual_closed(ear_df=ear_df, intervals_df=intervals_df)

    frame_out = out_dir / "frame_labels_selfrec.csv"
    frame_df.to_csv(frame_out, index=False, encoding="utf-8-sig")

    for video_id, dfv in frame_df.groupby("video_id", sort=True):
        dfv.to_csv(per_video_dir / f"{video_id}_frame_labels.csv", index=False, encoding="utf-8-sig")

    windows_df = build_closed_windows(
        df=frame_df,
        window_size=args.window_size,
        central_size=args.central_size,
        min_closed_in_central=args.min_closed_in_central,
        ear_min=args.ear_min,
        ear_max=args.ear_max,
        max_lr_diff=args.max_lr_diff,
    )

    windows_out = out_dir / "windows_closed_selfrec.csv"
    windows_df.to_csv(windows_out, index=False, encoding="utf-8-sig")

    print(f"[DONE] frame_labels_selfrec.csv -> {frame_out}")
    print(f"[DONE] windows_closed_selfrec.csv -> {windows_out}")
    print_stats(frame_df, windows_df)


if __name__ == "__main__":
    main()