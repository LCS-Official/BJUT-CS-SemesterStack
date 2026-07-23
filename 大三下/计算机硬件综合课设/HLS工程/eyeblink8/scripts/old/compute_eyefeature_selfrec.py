"""
Compute simple EyeFeature curves for self-recorded eye-blink videos.

Default Windows layout expected by this script:
  C:\\Users\\LC\\Desktop\\eyeblink8\\raw_selfrec
  C:\\Users\\LC\\Desktop\\eyeblink8\\models\\shape_predictor_68_face_landmarks.dat
  C:\\Users\\LC\\Desktop\\eyeblink8\\work_selfrec\\manual_closed_intervals.csv

Outputs:
  work_selfrec/frame_eyefeature_selfrec.csv
  work_selfrec/video_summary_eyefeature.csv
  work_selfrec/eyefeature_plots/<video_id>_score.png
  work_selfrec/debug_videos/<video_id>_debug.mp4   (optional, with --save_debug_video)

Frame indices are 0-based and closed intervals are inclusive: start_frame <= frame_idx <= end_frame.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import cv2
import dlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    from tqdm import tqdm
except Exception:  # pragma: no cover
    tqdm = None


ROI = Tuple[int, int, int, int]  # x, y, w, h


@dataclass
class FeatureResult:
    dark_ratio: float
    v_extent: float
    edge_density: float
    dark_count: int
    total_count: int
    active_rows: int


def clamp_roi(x: int, y: int, w: int, h: int, img_w: int, img_h: int) -> Optional[ROI]:
    x0 = max(0, int(x))
    y0 = max(0, int(y))
    x1 = min(img_w, int(x + w))
    y1 = min(img_h, int(y + h))
    if x1 <= x0 + 1 or y1 <= y0 + 1:
        return None
    return x0, y0, x1 - x0, y1 - y0


def eye_bbox(points: np.ndarray, pad_ratio: float, img_w: int, img_h: int) -> Optional[ROI]:
    """Build a padded ROI from six eye landmarks."""
    xs = points[:, 0]
    ys = points[:, 1]
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    w = max(1, x1 - x0 + 1)
    h = max(1, y1 - y0 + 1)

    # Eye landmarks are tight vertically, so use a little extra vertical padding.
    pad_x = int(round(w * pad_ratio))
    pad_y = int(round(h * max(pad_ratio, 0.55)))
    return clamp_roi(x0 - pad_x, y0 - pad_y, w + 2 * pad_x, h + 2 * pad_y, img_w, img_h)


def rect_area(rect: dlib.rectangle) -> int:
    return max(0, rect.right() - rect.left()) * max(0, rect.bottom() - rect.top())


def detect_eye_rois(
    gray: np.ndarray,
    detector: dlib.fhog_object_detector,
    predictor: dlib.shape_predictor,
    detect_width: int,
    upsample: int,
    pad_ratio: float,
) -> Tuple[Optional[ROI], Optional[ROI], bool]:
    """Detect face and 68 landmarks, then return left/right eye ROIs in original-frame coords."""
    img_h, img_w = gray.shape[:2]
    scale = 1.0
    detect_img = gray

    if detect_width > 0 and img_w > detect_width:
        scale = detect_width / float(img_w)
        detect_h = max(1, int(round(img_h * scale)))
        detect_img = cv2.resize(gray, (detect_width, detect_h), interpolation=cv2.INTER_AREA)

    rects = detector(detect_img, upsample)
    if len(rects) == 0:
        return None, None, False

    r_small = max(rects, key=rect_area)
    if scale != 1.0:
        inv = 1.0 / scale
        r = dlib.rectangle(
            int(round(r_small.left() * inv)),
            int(round(r_small.top() * inv)),
            int(round(r_small.right() * inv)),
            int(round(r_small.bottom() * inv)),
        )
    else:
        r = r_small

    r = dlib.rectangle(
        max(0, r.left()),
        max(0, r.top()),
        min(img_w - 1, r.right()),
        min(img_h - 1, r.bottom()),
    )
    shape = predictor(gray, r)
    pts = np.array([[shape.part(i).x, shape.part(i).y] for i in range(68)], dtype=np.int32)

    left = eye_bbox(pts[36:42], pad_ratio, img_w, img_h)
    right = eye_bbox(pts[42:48], pad_ratio, img_w, img_h)
    ok = left is not None and right is not None
    return left, right, ok


def compute_roi_feature(
    gray: np.ndarray,
    roi: Optional[ROI],
    dark_thresh: int,
    row_dark_frac: float,
    grad_thresh: int,
) -> FeatureResult:
    """Hardware-friendly ROI statistics: dark ratio, vertical dark extent, edge density."""
    if roi is None:
        return FeatureResult(math.nan, math.nan, math.nan, 0, 0, 0)

    x, y, w, h = roi
    patch = gray[y : y + h, x : x + w]
    if patch.size == 0:
        return FeatureResult(math.nan, math.nan, math.nan, 0, 0, 0)

    dark = patch < int(dark_thresh)
    dark_count = int(dark.sum())
    total_count = int(patch.size)
    dark_ratio = float(dark_count) / float(total_count) if total_count else math.nan

    # Vertical extent: how many rows contain enough dark pixels.
    # This often separates open eyes, where iris/pupil spans multiple rows,
    # from closed eyes, where the dark region is a thin eyelid line.
    min_dark_per_row = max(1, int(round(w * row_dark_frac)))
    row_counts = dark.sum(axis=1)
    active_rows = int((row_counts >= min_dark_per_row).sum())
    v_extent = float(active_rows) / float(h) if h else math.nan

    # Simple edge density. Use absolute horizontal/vertical differences, no Sobel kernel.
    patch_i = patch.astype(np.int16)
    gx = np.abs(np.diff(patch_i, axis=1)) if w > 1 else np.zeros((h, 0), dtype=np.int16)
    gy = np.abs(np.diff(patch_i, axis=0)) if h > 1 else np.zeros((0, w), dtype=np.int16)
    edge_count = int((gx > grad_thresh).sum() + (gy > grad_thresh).sum())
    edge_total = int(gx.size + gy.size)
    edge_density = float(edge_count) / float(edge_total) if edge_total else math.nan

    return FeatureResult(dark_ratio, v_extent, edge_density, dark_count, total_count, active_rows)


def build_closed_mask(video_id: str, frame_count: int, intervals_df: pd.DataFrame) -> np.ndarray:
    mask = np.zeros(frame_count, dtype=np.int8)
    if intervals_df.empty:
        return mask
    cur = intervals_df[intervals_df["video_id"].astype(str) == str(video_id)]
    for _, row in cur.iterrows():
        s = int(row["start_frame"])
        e = int(row["end_frame"])
        s = max(0, s)
        e = min(frame_count - 1, e)
        if s <= e:
            mask[s : e + 1] = 1
    return mask


def intervals_for_video(video_id: str, intervals_df: pd.DataFrame) -> List[Tuple[int, int]]:
    cur = intervals_df[intervals_df["video_id"].astype(str) == str(video_id)]
    return [(int(r["start_frame"]), int(r["end_frame"])) for _, r in cur.iterrows()]


def draw_roi(frame: np.ndarray, roi: Optional[ROI], text: str) -> None:
    if roi is None:
        return
    x, y, w, h = roi
    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
    cv2.putText(frame, text, (x, max(15, y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)


def process_video(
    video_path: Path,
    args: argparse.Namespace,
    detector: dlib.fhog_object_detector,
    predictor: dlib.shape_predictor,
    intervals_df: pd.DataFrame,
) -> pd.DataFrame:
    video_id = video_path.stem
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"[WARN] Cannot open video: {video_path}")
        return pd.DataFrame()

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if args.max_frames > 0:
        frame_count_for_mask = min(frame_count, args.max_frames)
    else:
        frame_count_for_mask = frame_count
    closed_mask = build_closed_mask(video_id, max(1, frame_count_for_mask), intervals_df)

    debug_writer = None
    if args.save_debug_video:
        debug_dir = Path(args.out_dir) / "debug_videos"
        debug_dir.mkdir(parents=True, exist_ok=True)
        out_path = debug_dir / f"{video_id}_debug.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out_fps = fps if fps > 0 else 30.0
        debug_writer = cv2.VideoWriter(str(out_path), fourcc, out_fps, (frame_w, frame_h))

    last_left: Optional[ROI] = None
    last_right: Optional[ROI] = None
    last_update_idx = -10**9
    rows: List[Dict[str, object]] = []

    iterator: Iterable[int]
    if tqdm is not None:
        iterator = tqdm(range(frame_count), desc=video_id, unit="frame")
    else:
        iterator = range(frame_count)

    for frame_idx in iterator:
        ok, frame = cap.read()
        if not ok:
            break
        if args.max_frames > 0 and frame_idx >= args.max_frames:
            break
        if args.frame_stride > 1 and (frame_idx % args.frame_stride != 0):
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        need_update = False
        if args.roi_mode == "each_frame":
            need_update = True
        else:
            if last_left is None or last_right is None:
                need_update = True
            elif (frame_idx - last_update_idx) >= args.detect_interval:
                need_update = True
            elif (frame_idx - last_update_idx) > args.reuse_max_age:
                need_update = True

        face_ok = False
        roi_updated = False
        if need_update:
            left, right, face_ok = detect_eye_rois(
                gray,
                detector,
                predictor,
                detect_width=args.detect_width,
                upsample=args.upsample,
                pad_ratio=args.pad_ratio,
            )
            if face_ok and left is not None and right is not None:
                last_left, last_right = left, right
                last_update_idx = frame_idx
                roi_updated = True

        roi_valid = last_left is not None and last_right is not None and (frame_idx - last_update_idx) <= args.reuse_max_age
        left_roi = last_left if roi_valid else None
        right_roi = last_right if roi_valid else None

        lf = compute_roi_feature(gray, left_roi, args.dark_thresh, args.row_dark_frac, args.grad_thresh)
        rf = compute_roi_feature(gray, right_roi, args.dark_thresh, args.row_dark_frac, args.grad_thresh)

        # Main scalar for the new 15-frame SVM input.
        # Prefer vertical dark extent because it is simple and less sensitive to ROI size than raw dark count.
        eye_open_score = np.nanmean([lf.v_extent, rf.v_extent])
        dark_ratio_mean = np.nanmean([lf.dark_ratio, rf.dark_ratio])
        edge_density_mean = np.nanmean([lf.edge_density, rf.edge_density])
        score_q = int(round(float(eye_open_score) * args.fixed_scale)) if not math.isnan(float(eye_open_score)) else -1

        label_closed = int(closed_mask[frame_idx]) if frame_idx < len(closed_mask) else 0

        row: Dict[str, object] = {
            "video_id": video_id,
            "video_file": video_path.name,
            "frame_idx": frame_idx,
            "time_sec": frame_idx / fps if fps > 0 else math.nan,
            "label_closed": label_closed,
            "face_ok_on_update": int(face_ok),
            "roi_updated": int(roi_updated),
            "roi_valid": int(roi_valid),
            "roi_age": int(frame_idx - last_update_idx) if last_update_idx > -10**8 else -1,
            "left_x": left_roi[0] if left_roi else -1,
            "left_y": left_roi[1] if left_roi else -1,
            "left_w": left_roi[2] if left_roi else -1,
            "left_h": left_roi[3] if left_roi else -1,
            "right_x": right_roi[0] if right_roi else -1,
            "right_y": right_roi[1] if right_roi else -1,
            "right_w": right_roi[2] if right_roi else -1,
            "right_h": right_roi[3] if right_roi else -1,
            "left_dark_ratio": lf.dark_ratio,
            "right_dark_ratio": rf.dark_ratio,
            "dark_ratio_mean": dark_ratio_mean,
            "left_v_extent": lf.v_extent,
            "right_v_extent": rf.v_extent,
            "eye_open_score": eye_open_score,
            "score_q": score_q,
            "left_edge_density": lf.edge_density,
            "right_edge_density": rf.edge_density,
            "edge_density_mean": edge_density_mean,
            "dark_thresh": int(args.dark_thresh),
        }
        rows.append(row)

        if debug_writer is not None:
            draw_roi(frame, left_roi, "L")
            draw_roi(frame, right_roi, "R")
            txt = f"f={frame_idx} closed={label_closed} score={eye_open_score:.3f} roi_age={row['roi_age']}"
            cv2.putText(frame, txt, (15, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            debug_writer.write(frame)

    cap.release()
    if debug_writer is not None:
        debug_writer.release()

    return pd.DataFrame(rows)


def plot_video_curve(video_df: pd.DataFrame, intervals: List[Tuple[int, int]], out_path: Path) -> None:
    if video_df.empty:
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    x = video_df["frame_idx"].to_numpy()

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(x, video_df["eye_open_score"].to_numpy(), linewidth=1.2, label="eye_open_score = mean(v_extent)")
    ax.plot(x, video_df["dark_ratio_mean"].to_numpy(), linewidth=0.9, label="dark_ratio_mean", alpha=0.75)
    ax.plot(x, video_df["edge_density_mean"].to_numpy(), linewidth=0.9, label="edge_density_mean", alpha=0.75)

    first_span = True
    for s, e in intervals:
        ax.axvspan(s, e, alpha=0.18, label="manual closed" if first_span else None)
        first_span = False

    ax.set_title(str(video_df["video_id"].iloc[0]))
    ax.set_xlabel("frame_idx")
    ax.set_ylabel("feature value")
    ax.grid(True, linewidth=0.3)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def summarize_video(video_df: pd.DataFrame) -> Dict[str, object]:
    video_id = video_df["video_id"].iloc[0] if not video_df.empty else ""
    valid = video_df[video_df["roi_valid"] == 1]
    closed = valid[valid["label_closed"] == 1]
    open_ = valid[valid["label_closed"] == 0]

    def mean_col(df: pd.DataFrame, col: str) -> float:
        return float(df[col].mean()) if len(df) else math.nan

    open_mean = mean_col(open_, "eye_open_score")
    closed_mean = mean_col(closed, "eye_open_score")
    open_std = float(open_["eye_open_score"].std()) if len(open_) > 1 else math.nan
    closed_std = float(closed["eye_open_score"].std()) if len(closed) > 1 else math.nan
    pooled = math.sqrt(np.nanmean([open_std ** 2, closed_std ** 2])) if not math.isnan(open_std) and not math.isnan(closed_std) else math.nan
    sep = (open_mean - closed_mean) / pooled if pooled and not math.isnan(pooled) and pooled > 1e-12 else math.nan

    # A simple threshold report. Assumes larger score means more open.
    thr = np.nanmean([open_mean, closed_mean]) if not math.isnan(open_mean) and not math.isnan(closed_mean) else math.nan
    if not math.isnan(thr) and len(valid):
        pred_closed = (valid["eye_open_score"] < thr).astype(int)
        acc = float((pred_closed.to_numpy() == valid["label_closed"].to_numpy()).mean())
    else:
        acc = math.nan

    return {
        "video_id": video_id,
        "frames_valid": int(len(valid)),
        "roi_valid_rate": float(video_df["roi_valid"].mean()) if len(video_df) else math.nan,
        "roi_update_count": int(video_df["roi_updated"].sum()) if len(video_df) else 0,
        "manual_closed_frames": int(video_df["label_closed"].sum()) if len(video_df) else 0,
        "open_score_mean_open": open_mean,
        "open_score_mean_closed": closed_mean,
        "open_score_gap_open_minus_closed": open_mean - closed_mean if not math.isnan(open_mean) and not math.isnan(closed_mean) else math.nan,
        "separation_rough": sep,
        "simple_threshold": thr,
        "simple_threshold_acc": acc,
        "dark_ratio_mean_open": mean_col(open_, "dark_ratio_mean"),
        "dark_ratio_mean_closed": mean_col(closed, "dark_ratio_mean"),
        "edge_density_mean_open": mean_col(open_, "edge_density_mean"),
        "edge_density_mean_closed": mean_col(closed, "edge_density_mean"),
    }


def parse_args() -> argparse.Namespace:
    base = Path(r"C:\Users\LC\Desktop\eyeblink8")
    parser = argparse.ArgumentParser(description="Compute hardware-friendly EyeFeature curves for self-recorded videos.")
    parser.add_argument("--raw_dir", type=Path, default=base / "raw_selfrec", help="Directory containing mp4 videos.")
    parser.add_argument("--predictor", type=Path, default=base / "models" / "shape_predictor_68_face_landmarks.dat")
    parser.add_argument("--manual_csv", type=Path, default=base / "work_selfrec" / "manual_closed_intervals.csv")
    parser.add_argument("--out_dir", type=Path, default=base / "work_selfrec")

    parser.add_argument("--roi_mode", choices=["lowfreq", "each_frame"], default="lowfreq", help="lowfreq mimics the new scheme; each_frame is an upper-bound reference.")
    parser.add_argument("--detect_interval", type=int, default=20, help="Update dlib ROI every N frames in lowfreq mode.")
    parser.add_argument("--reuse_max_age", type=int, default=30, help="Max frames to reuse ROI after last successful dlib update.")
    parser.add_argument("--detect_width", type=int, default=320, help="Resize width for dlib face detection; <=0 means original size.")
    parser.add_argument("--upsample", type=int, default=0)
    parser.add_argument("--pad_ratio", type=float, default=0.35)

    parser.add_argument("--dark_thresh", type=int, default=70, help="Dark-pixel threshold, hardware register candidate.")
    parser.add_argument("--row_dark_frac", type=float, default=0.06, help="A row is active if dark_count >= ROI_width * this value.")
    parser.add_argument("--grad_thresh", type=int, default=25, help="Simple absolute gradient threshold.")
    parser.add_argument("--fixed_scale", type=int, default=4096)

    parser.add_argument("--max_frames", type=int, default=-1)
    parser.add_argument("--frame_stride", type=int, default=1)
    parser.add_argument("--save_debug_video", action="store_true")
    parser.add_argument("--video_glob", default="*.mp4")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "eyefeature_plots").mkdir(parents=True, exist_ok=True)

    if not args.raw_dir.exists():
        raise FileNotFoundError(f"raw_dir not found: {args.raw_dir}")
    if not args.predictor.exists():
        raise FileNotFoundError(f"shape predictor not found: {args.predictor}")
    if not args.manual_csv.exists():
        raise FileNotFoundError(f"manual csv not found: {args.manual_csv}")

    intervals_df = pd.read_csv(args.manual_csv)
    required_cols = {"video_id", "start_frame", "end_frame"}
    missing = required_cols - set(intervals_df.columns)
    if missing:
        raise ValueError(f"manual_csv missing columns: {sorted(missing)}")
    intervals_df["video_id"] = intervals_df["video_id"].astype(str)

    video_paths = sorted(args.raw_dir.glob(args.video_glob))
    if not video_paths:
        raise FileNotFoundError(f"No videos found by {args.raw_dir / args.video_glob}")

    print(f"[Info] videos: {len(video_paths)}")
    print(f"[Info] loading dlib predictor: {args.predictor}")
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(str(args.predictor))

    all_frames: List[pd.DataFrame] = []
    summaries: List[Dict[str, object]] = []

    for vp in video_paths:
        print(f"\n[Video] {vp.name}")
        df = process_video(vp, args, detector, predictor, intervals_df)
        if df.empty:
            continue
        all_frames.append(df)
        summaries.append(summarize_video(df))
        plot_video_curve(df, intervals_for_video(vp.stem, intervals_df), args.out_dir / "eyefeature_plots" / f"{vp.stem}_score.png")

        # Also save per-video CSV for easier checking.
        per_video_dir = args.out_dir / "per_video_eyefeature"
        per_video_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(per_video_dir / f"{vp.stem}_eyefeature.csv", index=False, encoding="utf-8-sig")

    if all_frames:
        frame_df = pd.concat(all_frames, ignore_index=True)
    else:
        frame_df = pd.DataFrame()
    summary_df = pd.DataFrame(summaries)

    frame_csv = args.out_dir / "frame_eyefeature_selfrec.csv"
    summary_csv = args.out_dir / "video_summary_eyefeature.csv"
    frame_df.to_csv(frame_csv, index=False, encoding="utf-8-sig")
    summary_df.to_csv(summary_csv, index=False, encoding="utf-8-sig")

    print("\n[Done]")
    print(f"frame csv   : {frame_csv}")
    print(f"summary csv : {summary_csv}")
    print(f"plots dir   : {args.out_dir / 'eyefeature_plots'}")
    if not summary_df.empty:
        cols = [
            "video_id",
            "roi_valid_rate",
            "open_score_mean_open",
            "open_score_mean_closed",
            "open_score_gap_open_minus_closed",
            "simple_threshold_acc",
        ]
        print("\n[Summary preview]")
        print(summary_df[cols].to_string(index=False))


if __name__ == "__main__":
    main()
