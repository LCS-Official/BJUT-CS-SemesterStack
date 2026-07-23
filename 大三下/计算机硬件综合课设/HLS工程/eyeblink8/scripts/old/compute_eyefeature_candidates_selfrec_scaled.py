"""
Compute and compare multiple hardware-friendly EyeFeature candidates for self-recorded eye-blink videos.

Default Windows layout expected:
  C:\\Users\\LC\\Desktop\\eyeblink8\\raw_selfrec
  C:\\Users\\LC\\Desktop\\eyeblink8\\models\\shape_predictor_68_face_landmarks.dat
  C:\\Users\\LC\\Desktop\\eyeblink8\\work_selfrec\\manual_closed_intervals.csv

Recommended first run:
  cd C:\\Users\\LC\\Desktop\\eyeblink8
  python scripts\\compute_eyefeature_candidates_selfrec.py --roi_mode each_frame --exclude_glasses

Outputs:
  work_selfrec_candidates_scaled/frame_eyefeature_candidates.csv
  work_selfrec_candidates/feature_summary_candidates.csv
  work_selfrec_candidates/per_video_feature_summary.csv
  work_selfrec_candidates/candidate_plots/<video_id>_candidates.png

Frame indices are 0-based and closed intervals are inclusive.
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

ROI = Tuple[int, int, int, int]
GLASSES_VIDEO_IDS = {
    "test1",
    "test2",
    "test3",
    "test4",
    "WIN_20260414_20_41_42_Pro",
}


def clamp_roi(x: int, y: int, w: int, h: int, img_w: int, img_h: int) -> Optional[ROI]:
    x0 = max(0, int(x)); y0 = max(0, int(y))
    x1 = min(img_w, int(x + w)); y1 = min(img_h, int(y + h))
    if x1 <= x0 + 1 or y1 <= y0 + 1:
        return None
    return x0, y0, x1 - x0, y1 - y0


def eye_bbox(points: np.ndarray, pad_ratio: float, img_w: int, img_h: int) -> Optional[ROI]:
    xs = points[:, 0]; ys = points[:, 1]
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    w = max(1, x1 - x0 + 1); h = max(1, y1 - y0 + 1)
    pad_x = int(round(w * pad_ratio))
    pad_y = int(round(h * max(pad_ratio, 0.55)))
    return clamp_roi(x0 - pad_x, y0 - pad_y, w + 2 * pad_x, h + 2 * pad_y, img_w, img_h)


def rect_area(rect: dlib.rectangle) -> int:
    return max(0, rect.right() - rect.left()) * max(0, rect.bottom() - rect.top())


def detect_eye_rois(gray: np.ndarray, detector, predictor, detect_width: int, upsample: int, pad_ratio: float):
    img_h, img_w = gray.shape[:2]
    detect_img = gray; scale = 1.0
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
        r = dlib.rectangle(int(round(r_small.left()*inv)), int(round(r_small.top()*inv)),
                           int(round(r_small.right()*inv)), int(round(r_small.bottom()*inv)))
    else:
        r = r_small
    r = dlib.rectangle(max(0, r.left()), max(0, r.top()), min(img_w-1, r.right()), min(img_h-1, r.bottom()))
    shape = predictor(gray, r)
    pts = np.array([[shape.part(i).x, shape.part(i).y] for i in range(68)], dtype=np.int32)
    left = eye_bbox(pts[36:42], pad_ratio, img_w, img_h)
    right = eye_bbox(pts[42:48], pad_ratio, img_w, img_h)
    return left, right, (left is not None and right is not None)


def crop_inner(patch: np.ndarray, x0f: float, x1f: float, y0f: float, y1f: float) -> np.ndarray:
    h, w = patch.shape[:2]
    x0 = max(0, min(w-1, int(round(w * x0f))))
    x1 = max(x0+1, min(w, int(round(w * x1f))))
    y0 = max(0, min(h-1, int(round(h * y0f))))
    y1 = max(y0+1, min(h, int(round(h * y1f))))
    return patch[y0:y1, x0:x1]


def max_consecutive_true_1d(arr: np.ndarray) -> int:
    best = 0; cur = 0
    for v in arr:
        if bool(v):
            cur += 1
            if cur > best: best = cur
        else:
            cur = 0
    return best


def column_max_runs(dark: np.ndarray) -> np.ndarray:
    """For each column, max vertical run length of dark pixels."""
    h, w = dark.shape[:2]
    runs = np.zeros(w, dtype=np.int32)
    cur = np.zeros(w, dtype=np.int32)
    for y in range(h):
        cur = np.where(dark[y, :], cur + 1, 0)
        runs = np.maximum(runs, cur)
    return runs


def row_sigma_from_dark(dark: np.ndarray) -> float:
    h, w = dark.shape[:2]
    row_counts = dark.sum(axis=1).astype(np.float64)
    total = float(row_counts.sum())
    if total <= 0:
        return 0.0
    ys = np.arange(h, dtype=np.float64)
    cy = float((ys * row_counts).sum() / total)
    var = float(((ys - cy) ** 2 * row_counts).sum() / total)
    return math.sqrt(max(0.0, var)) / max(1.0, float(h))


def feature_one_eye(gray: np.ndarray, roi: Optional[ROI], args) -> Dict[str, float]:
    if roi is None:
        return {}
    x, y, w, h = roi
    patch = gray[y:y+h, x:x+w]
    if patch.size == 0:
        return {}

    # Use a centered sub-ROI to reduce eyebrow/skin/glasses-frame influence.
    center = crop_inner(patch, args.inner_x0, args.inner_x1, args.inner_y0, args.inner_y1)
    upper = crop_inner(patch, args.inner_x0, args.inner_x1, 0.00, 0.28)
    lower = crop_inner(patch, args.inner_x0, args.inner_x1, 0.55, 1.00)

    # Fixed threshold candidate: easiest to implement in HLS.
    dark_fixed = patch < int(args.dark_thresh)
    center_dark_fixed = center < int(args.dark_thresh)

    # Adaptive threshold candidate: software exploration; HLS can approximate with mean - offset.
    mean_center = float(center.mean())
    t_adapt = int(max(0, min(255, round(mean_center - args.adapt_offset))))
    dark_adapt = center < t_adapt

    # Current style, but replaced with max contiguous active rows rather than total active rows.
    row_counts = dark_fixed.sum(axis=1)
    min_dark_per_row = max(1, int(round(w * args.row_dark_frac)))
    active_rows = row_counts >= min_dark_per_row
    max_active_row_run = max_consecutive_true_1d(active_rows) / max(1, h)
    active_row_frac = float(active_rows.sum()) / max(1, h)

    # New key candidate: vertical thickness per column, robust to diagonal eyelid lines.
    runs_fixed = column_max_runs(center_dark_fixed)
    if runs_fixed.size:
        k = max(1, int(math.ceil(runs_fixed.size * args.topk_frac)))
        topk = np.sort(runs_fixed)[-k:]
        col_run_topk_fixed = float(topk.mean()) / max(1, center.shape[0])
        col_run_max_fixed = float(runs_fixed.max()) / max(1, center.shape[0])
        col_run_mean_fixed = float(runs_fixed.mean()) / max(1, center.shape[0])
    else:
        col_run_topk_fixed = col_run_max_fixed = col_run_mean_fixed = math.nan

    runs_adapt = column_max_runs(dark_adapt)
    if runs_adapt.size:
        k = max(1, int(math.ceil(runs_adapt.size * args.topk_frac)))
        topk = np.sort(runs_adapt)[-k:]
        col_run_topk_adapt = float(topk.mean()) / max(1, center.shape[0])
    else:
        col_run_topk_adapt = math.nan

    # Projection spread: open iris/pupil tends to occupy a thicker vertical band than closed eyelid line.
    row_sigma_fixed = row_sigma_from_dark(center_dark_fixed)
    row_sigma_adapt = row_sigma_from_dark(dark_adapt)

    # Bright/dark contrast around eye center. Open eye often has larger iris/skin or iris/sclera contrast.
    center_mean = float(center.mean())
    upper_mean = float(upper.mean()) if upper.size else math.nan
    lower_mean = float(lower.mean()) if lower.size else math.nan
    vertical_contrast = ((upper_mean + lower_mean) * 0.5 - center_mean) / 255.0 if not math.isnan(upper_mean) and not math.isnan(lower_mean) else math.nan

    # Simple gradient features.
    p16 = center.astype(np.int16)
    gy = np.abs(np.diff(p16, axis=0)) if center.shape[0] > 1 else np.zeros((0, center.shape[1]), dtype=np.int16)
    gx = np.abs(np.diff(p16, axis=1)) if center.shape[1] > 1 else np.zeros((center.shape[0], 0), dtype=np.int16)
    v_edge_density = float((gy > args.grad_thresh).mean()) if gy.size else math.nan
    h_edge_density = float((gx > args.grad_thresh).mean()) if gx.size else math.nan

    # Largest dark connected component height, not the first HLS target, but useful as a software upper-bound.
    num, labels, stats, _ = cv2.connectedComponentsWithStats(center_dark_fixed.astype(np.uint8), connectivity=8)
    if num > 1:
        areas = stats[1:, cv2.CC_STAT_AREA]
        idx = int(np.argmax(areas)) + 1
        blob_h = float(stats[idx, cv2.CC_STAT_HEIGHT]) / max(1, center.shape[0])
        blob_area = float(stats[idx, cv2.CC_STAT_AREA]) / max(1, center.size)
    else:
        blob_h = 0.0; blob_area = 0.0

    return {
        "dark_ratio_fixed": float(dark_fixed.mean()),
        "center_dark_ratio_fixed": float(center_dark_fixed.mean()),
        "center_dark_ratio_adapt": float(dark_adapt.mean()),
        "active_row_frac_fixed": active_row_frac,
        "max_active_row_run_fixed": max_active_row_run,
        "col_run_topk_fixed": col_run_topk_fixed,
        "col_run_max_fixed": col_run_max_fixed,
        "col_run_mean_fixed": col_run_mean_fixed,
        "col_run_topk_adapt": col_run_topk_adapt,
        "row_sigma_fixed": row_sigma_fixed,
        "row_sigma_adapt": row_sigma_adapt,
        "vertical_contrast": vertical_contrast,
        "v_edge_density": v_edge_density,
        "h_edge_density": h_edge_density,
        "largest_blob_h_fixed": blob_h,
        "largest_blob_area_fixed": blob_area,
        "t_adapt": float(t_adapt),
    }


def mean_lr_features(left: Dict[str, float], right: Dict[str, float]) -> Dict[str, float]:
    keys = sorted(set(left.keys()) | set(right.keys()))
    out = {}
    for k in keys:
        vals = []
        if k in left and not math.isnan(float(left[k])): vals.append(float(left[k]))
        if k in right and not math.isnan(float(right[k])): vals.append(float(right[k]))
        out[k] = float(np.mean(vals)) if vals else math.nan
    return out


def build_closed_mask(video_id: str, frame_count: int, intervals_df: pd.DataFrame) -> np.ndarray:
    mask = np.zeros(frame_count, dtype=np.int8)
    if intervals_df.empty:
        return mask
    cur = intervals_df[intervals_df["video_id"].astype(str) == str(video_id)]
    for _, row in cur.iterrows():
        s = max(0, int(row["start_frame"])); e = min(frame_count - 1, int(row["end_frame"]))
        if s <= e:
            mask[s:e+1] = 1
    return mask



def resize_frame_for_processing(frame: np.ndarray, args) -> Tuple[np.ndarray, float, float]:
    """
    Resize the whole frame before dlib ROI detection and feature extraction.

    Returns:
      proc_frame, sx, sy
    where sx = proc_width / original_width, sy = proc_height / original_height.
    ROI coordinates in CSV are in processed-frame coordinates.
    """
    h, w = frame.shape[:2]

    if args.proc_width > 0 or args.proc_height > 0:
        if args.proc_width > 0 and args.proc_height > 0:
            new_w, new_h = int(args.proc_width), int(args.proc_height)
        elif args.proc_width > 0:
            new_w = int(args.proc_width)
            new_h = max(1, int(round(h * (new_w / float(w)))))
        else:
            new_h = int(args.proc_height)
            new_w = max(1, int(round(w * (new_h / float(h)))))
    elif abs(float(args.proc_scale) - 1.0) > 1e-9:
        new_w = max(1, int(round(w * float(args.proc_scale))))
        new_h = max(1, int(round(h * float(args.proc_scale))))
    else:
        return frame, 1.0, 1.0

    if new_w == w and new_h == h:
        return frame, 1.0, 1.0

    interp_name = str(args.resize_interpolation).lower()
    if interp_name == "area":
        interp = cv2.INTER_AREA
    elif interp_name == "linear":
        interp = cv2.INTER_LINEAR
    elif interp_name == "nearest":
        interp = cv2.INTER_NEAREST
    elif interp_name == "cubic":
        interp = cv2.INTER_CUBIC
    else:
        raise ValueError(f"Unknown --resize_interpolation {args.resize_interpolation}")

    proc = cv2.resize(frame, (new_w, new_h), interpolation=interp)
    return proc, new_w / float(w), new_h / float(h)


def process_video(video_path: Path, args, detector, predictor, intervals_df) -> pd.DataFrame:
    video_id = video_path.stem
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"[WARN] cannot open {video_path}")
        return pd.DataFrame()
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    orig_frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); orig_frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if args.max_frames > 0:
        frame_count_for_mask = min(frame_count, args.max_frames)
    else:
        frame_count_for_mask = frame_count
    closed_mask = build_closed_mask(video_id, max(1, frame_count_for_mask), intervals_df)

    last_left = None; last_right = None; last_update_idx = -10**9
    rows: List[Dict[str, object]] = []
    iterator: Iterable[int] = tqdm(range(frame_count), desc=video_id, unit="frame") if tqdm else range(frame_count)

    for frame_idx in iterator:
        ok, frame = cap.read()
        if not ok: break
        if args.max_frames > 0 and frame_idx >= args.max_frames: break
        if args.frame_stride > 1 and (frame_idx % args.frame_stride != 0): continue
        proc_frame, sx, sy = resize_frame_for_processing(frame, args)
        proc_h, proc_w = proc_frame.shape[:2]
        gray = cv2.cvtColor(proc_frame, cv2.COLOR_BGR2GRAY)

        need_update = args.roi_mode == "each_frame" or last_left is None or last_right is None or (frame_idx - last_update_idx) >= args.detect_interval or (frame_idx - last_update_idx) > args.reuse_max_age
        face_ok = False; roi_updated = False
        if need_update:
            left, right, face_ok = detect_eye_rois(gray, detector, predictor, args.detect_width, args.upsample, args.pad_ratio)
            if face_ok:
                last_left, last_right = left, right
                last_update_idx = frame_idx
                roi_updated = True

        roi_valid = last_left is not None and last_right is not None and (frame_idx - last_update_idx) <= args.reuse_max_age
        left_roi = last_left if roi_valid else None
        right_roi = last_right if roi_valid else None
        lf = feature_one_eye(gray, left_roi, args)
        rf = feature_one_eye(gray, right_roi, args)
        feats = mean_lr_features(lf, rf)

        row = {
            "video_id": video_id,
            "frame_idx": frame_idx,
            "time_sec": frame_idx / fps if fps > 0 else math.nan,
            "orig_frame_w": orig_frame_w,
            "orig_frame_h": orig_frame_h,
            "proc_frame_w": proc_w,
            "proc_frame_h": proc_h,
            "proc_scale_x": sx,
            "proc_scale_y": sy,
            "label_closed": int(closed_mask[frame_idx]) if frame_idx < len(closed_mask) else 0,
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
        }
        row.update(feats)
        rows.append(row)
    cap.release()
    return pd.DataFrame(rows)


def feature_columns(df: pd.DataFrame) -> List[str]:
    skip = {"video_id","frame_idx","time_sec","orig_frame_w","orig_frame_h","proc_frame_w","proc_frame_h","proc_scale_x","proc_scale_y","label_closed","face_ok_on_update","roi_updated","roi_valid","roi_age","left_x","left_y","left_w","left_h","right_x","right_y","right_w","right_h"}
    return [c for c in df.columns if c not in skip and pd.api.types.is_numeric_dtype(df[c])]


def threshold_acc(values: np.ndarray, labels: np.ndarray, open_high: bool):
    open_vals = values[labels == 0]; closed_vals = values[labels == 1]
    if len(open_vals) == 0 or len(closed_vals) == 0:
        return math.nan, math.nan
    thr = 0.5 * (float(np.nanmean(open_vals)) + float(np.nanmean(closed_vals)))
    if open_high:
        pred_closed = values < thr
    else:
        pred_closed = values > thr
    acc = float((pred_closed.astype(np.int8) == labels).mean())
    return thr, acc


def summarize_features(frame_df: pd.DataFrame, exclude_glasses: bool) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df = frame_df.copy()
    if exclude_glasses:
        df = df[~df["video_id"].astype(str).isin(GLASSES_VIDEO_IDS)].copy()
    df = df[df["roi_valid"] == 1].copy()
    feats = feature_columns(df)
    overall_rows = []
    per_video_rows = []
    for f in feats:
        sub = df[["video_id", "label_closed", f]].dropna()
        sub = sub[np.isfinite(sub[f])]
        if sub.empty or sub["label_closed"].nunique() < 2:
            continue
        vals = sub[f].to_numpy(dtype=float)
        labels = sub["label_closed"].to_numpy(dtype=np.int8)
        open_mean = float(vals[labels == 0].mean())
        closed_mean = float(vals[labels == 1].mean())
        open_std = float(vals[labels == 0].std())
        closed_std = float(vals[labels == 1].std())
        gap = open_mean - closed_mean
        sep = gap / (0.5 * (open_std + closed_std) + 1e-12)
        thr_pos, acc_pos = threshold_acc(vals, labels, open_high=True)
        thr_neg, acc_neg = threshold_acc(vals, labels, open_high=False)
        overall_rows.append({
            "feature": f,
            "n_frames": len(sub),
            "open_mean": open_mean,
            "closed_mean": closed_mean,
            "gap_open_minus_closed": gap,
            "separation_rough": sep,
            "acc_if_open_high": acc_pos,
            "acc_if_closed_high": acc_neg,
            "best_acc_allow_flip": max(acc_pos, acc_neg),
            "best_direction": "open_high" if acc_pos >= acc_neg else "closed_high",
            "threshold_if_open_high": thr_pos,
        })
        for vid, g in sub.groupby("video_id"):
            if g["label_closed"].nunique() < 2:
                continue
            vv = g[f].to_numpy(dtype=float); ll = g["label_closed"].to_numpy(dtype=np.int8)
            om = float(vv[ll == 0].mean()); cm = float(vv[ll == 1].mean())
            os = float(vv[ll == 0].std()); cs = float(vv[ll == 1].std())
            gapv = om - cm; sepv = gapv / (0.5 * (os + cs) + 1e-12)
            _, ap = threshold_acc(vv, ll, open_high=True)
            _, an = threshold_acc(vv, ll, open_high=False)
            per_video_rows.append({
                "video_id": vid, "feature": f, "n_frames": len(g),
                "open_mean": om, "closed_mean": cm, "gap_open_minus_closed": gapv,
                "separation_rough": sepv, "acc_if_open_high": ap,
                "best_acc_allow_flip": max(ap, an),
                "direction": "open_high" if gapv >= 0 else "closed_high",
            })
    overall = pd.DataFrame(overall_rows).sort_values(["acc_if_open_high", "best_acc_allow_flip", "separation_rough"], ascending=False)
    per_video = pd.DataFrame(per_video_rows)
    return overall, per_video


def plot_candidates(frame_df: pd.DataFrame, out_dir: Path, features: List[str], max_videos: int = 999):
    plot_dir = out_dir / "candidate_plots"
    plot_dir.mkdir(parents=True, exist_ok=True)
    for i, (vid, g) in enumerate(frame_df.groupby("video_id")):
        if i >= max_videos: break
        g = g.sort_values("frame_idx")
        fig, ax = plt.subplots(figsize=(13, 5))
        x = g["frame_idx"].to_numpy()
        for f in features:
            if f in g.columns:
                y = g[f].astype(float).to_numpy()
                ax.plot(x, y, label=f, linewidth=1)
        closed = g["label_closed"].to_numpy().astype(int)
        if closed.any():
            # draw closed spans
            starts = []
            in_span = False; s = 0
            for idx, v in zip(x, closed):
                if v and not in_span:
                    s = idx; in_span = True
                if (not v) and in_span:
                    ax.axvspan(s, idx, alpha=0.18)
                    in_span = False
            if in_span:
                ax.axvspan(s, x[-1], alpha=0.18)
        ax.set_title(f"{vid} candidate features")
        ax.set_xlabel("frame")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best")
        fig.tight_layout()
        fig.savefig(plot_dir / f"{vid}_candidates.png", dpi=140)
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video_dir", default=r"C:\Users\LC\Desktop\eyeblink8\raw_selfrec")
    parser.add_argument("--shape_predictor", default=r"C:\Users\LC\Desktop\eyeblink8\models\shape_predictor_68_face_landmarks.dat")
    parser.add_argument("--intervals_csv", default=r"C:\Users\LC\Desktop\eyeblink8\work_selfrec\manual_closed_intervals.csv")
    parser.add_argument("--out_dir", default=r"C:\Users\LC\Desktop\eyeblink8\work_selfrec_candidates_scaled")
    parser.add_argument("--proc_scale", type=float, default=1.0, help="Resize whole frame before dlib and EyeFeature. 0.5 means half width and half height.")
    parser.add_argument("--proc_width", type=int, default=0, help="Optional processed-frame width. Keeps aspect ratio if height is 0.")
    parser.add_argument("--proc_height", type=int, default=0, help="Optional processed-frame height. Keeps aspect ratio if width is 0.")
    parser.add_argument("--resize_interpolation", choices=["area","linear","nearest","cubic"], default="area")
    parser.add_argument("--roi_mode", choices=["each_frame","lowfreq"], default="each_frame")
    parser.add_argument("--detect_interval", type=int, default=20)
    parser.add_argument("--reuse_max_age", type=int, default=30)
    parser.add_argument("--detect_width", type=int, default=240)
    parser.add_argument("--upsample", type=int, default=0)
    parser.add_argument("--pad_ratio", type=float, default=0.35)
    parser.add_argument("--dark_thresh", type=int, default=70)
    parser.add_argument("--adapt_offset", type=float, default=25.0)
    parser.add_argument("--row_dark_frac", type=float, default=0.08)
    parser.add_argument("--grad_thresh", type=int, default=25)
    parser.add_argument("--inner_x0", type=float, default=0.12)
    parser.add_argument("--inner_x1", type=float, default=0.88)
    parser.add_argument("--inner_y0", type=float, default=0.20)
    parser.add_argument("--inner_y1", type=float, default=0.85)
    parser.add_argument("--topk_frac", type=float, default=0.25)
    parser.add_argument("--frame_stride", type=int, default=1)
    parser.add_argument("--max_frames", type=int, default=-1)
    parser.add_argument("--exclude_glasses", action="store_true", help="Only affects summary ranking, not frame CSV generation.")
    parser.add_argument("--plot", action="store_true")
    args = parser.parse_args()

    video_dir = Path(args.video_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    intervals_df = pd.read_csv(args.intervals_csv)

    print("[Info] Loading dlib detector and predictor...")
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(args.shape_predictor)

    video_paths = sorted(list(video_dir.glob("*.mp4")) + list(video_dir.glob("*.avi")) + list(video_dir.glob("*.mov")))
    if not video_paths:
        raise FileNotFoundError(f"No videos found in {video_dir}")
    print(f"[Info] Found {len(video_paths)} videos")
    print(f"[Info] proc_scale={args.proc_scale}, proc_width={args.proc_width}, proc_height={args.proc_height}, interpolation={args.resize_interpolation}")

    all_frames = []
    for vp in video_paths:
        df = process_video(vp, args, detector, predictor, intervals_df)
        if not df.empty:
            all_frames.append(df)
    if not all_frames:
        raise RuntimeError("No frames processed")
    frame_df = pd.concat(all_frames, ignore_index=True)
    frame_csv = out_dir / "frame_eyefeature_candidates.csv"
    frame_df.to_csv(frame_csv, index=False, encoding="utf-8-sig")
    print(f"[OK] Wrote {frame_csv}")

    overall, per_video = summarize_features(frame_df, exclude_glasses=args.exclude_glasses)
    overall_csv = out_dir / "feature_summary_candidates.csv"
    per_video_csv = out_dir / "per_video_feature_summary.csv"
    overall.to_csv(overall_csv, index=False, encoding="utf-8-sig")
    per_video.to_csv(per_video_csv, index=False, encoding="utf-8-sig")
    print(f"[OK] Wrote {overall_csv}")
    print(f"[OK] Wrote {per_video_csv}")

    print("\nTop candidates by fixed direction open_high accuracy:")
    cols = ["feature","open_mean","closed_mean","gap_open_minus_closed","separation_rough","acc_if_open_high","best_acc_allow_flip","best_direction"]
    print(overall[cols].head(12).to_string(index=False))

    if args.plot:
        top_feats = overall["feature"].head(5).tolist()
        # force include the most relevant experimental candidates if present
        for f in ["col_run_topk_fixed", "center_dark_ratio_fixed", "row_sigma_fixed", "dark_ratio_fixed"]:
            if f in frame_df.columns and f not in top_feats:
                top_feats.append(f)
        plot_candidates(frame_df, out_dir, top_feats[:7])
        print(f"[OK] Wrote plots under {out_dir / 'candidate_plots'}")


if __name__ == "__main__":
    main()
