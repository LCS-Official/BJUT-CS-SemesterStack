from __future__ import annotations

"""
Extract frame-level EyeFeature candidates from either Eyeblink8 raw videos or self-recorded videos.

Intended board-side simulation:
  original frame
    -> downscale by --proc_scale for dlib detector + shape predictor
    -> map eye ROI coordinates back to original frame
    -> compute cheap EyeFeature candidates on the original-resolution grayscale ROI

Typical Windows usage:
  cd C:\\Users\\LC\\Desktop\\eyeblink8

  # Eyeblink8 official raw videos, usually *.avi in raw/
  python scripts\\extract_eyefeature_hybrid_all.py ^
    --raw_dir raw ^
    --out_csv work_eyefeature\\frame_eyefeature_eyeblink8.csv ^
    --shape_predictor models\\shape_predictor_68_face_landmarks.dat ^
    --exts .avi ^
    --proc_scale 0.5 ^
    --detect_interval 20 ^
    --reuse_max_age 30

  # self-recorded videos, usually *.mp4 in raw_selfrec/
  python scripts\\extract_eyefeature_hybrid_all.py ^
    --raw_dir raw_selfrec ^
    --out_csv work_eyefeature\\frame_eyefeature_selfrec.csv ^
    --shape_predictor models\\shape_predictor_68_face_landmarks.dat ^
    --exts .mp4,.avi,.mov,.mkv ^
    --proc_scale 0.5 ^
    --detect_interval 20 ^
    --reuse_max_age 30
"""

import argparse
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import dlib
import numpy as np
import pandas as pd

try:
    from tqdm import tqdm
except Exception:  # pragma: no cover
    tqdm = None

ROI = Tuple[int, int, int, int]
LEFT_EYE_IDX = list(range(36, 42))
RIGHT_EYE_IDX = list(range(42, 48))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Extract hybrid low-res-dlib / original-res EyeFeature frame CSV.")
    p.add_argument("--raw_dir", type=str, required=True, help="Folder containing videos")
    p.add_argument("--out_csv", type=str, required=True, help="Output frame-level eyefeature csv")
    p.add_argument("--shape_predictor", type=str, required=True, help="shape_predictor_68_face_landmarks.dat")
    p.add_argument("--video_ids", type=str, default="", help="Optional comma-separated video stems to process")
    p.add_argument("--exts", type=str, default=".mp4,.avi,.mov,.mkv", help="Comma-separated extensions")
    p.add_argument("--start_frame", type=int, default=0)
    p.add_argument("--max_frames", type=int, default=-1, help="-1 means all")
    p.add_argument("--proc_scale", type=float, default=0.5, help="Scale used only for dlib detector+predictor input")
    p.add_argument("--upsample", type=int, default=0)
    p.add_argument("--detect_interval", type=int, default=20, help="Run dlib every N frames")
    p.add_argument("--reuse_max_age", type=int, default=30, help="Max frames to reuse last ROI")
    p.add_argument("--pad_ratio", type=float, default=0.65, help="Eye bbox padding ratio")
    p.add_argument("--dark_thresh", type=int, default=70)
    p.add_argument("--adapt_offset", type=float, default=25.0)
    p.add_argument("--topk_frac", type=float, default=0.25)
    p.add_argument("--row_dark_frac", type=float, default=0.10)
    p.add_argument("--grad_thresh", type=int, default=25)
    p.add_argument("--inner_x0", type=float, default=0.10)
    p.add_argument("--inner_x1", type=float, default=0.90)
    p.add_argument("--inner_y0", type=float, default=0.18)
    p.add_argument("--inner_y1", type=float, default=0.88)
    p.add_argument("--fixed_scale", type=int, default=4096)
    p.add_argument("--save_debug_video", action="store_true")
    p.add_argument("--debug_dir", type=str, default="")
    p.add_argument("--no_progress", action="store_true")
    return p.parse_args()


def parse_list_arg(s: str) -> List[str]:
    return [x.strip() for x in s.split(",") if x.strip()]


def collect_video_paths(raw_dir: Path, exts_arg: str, video_ids_arg: str) -> List[Path]:
    exts = {e.lower().strip() for e in exts_arg.split(",") if e.strip()}
    paths = [p for p in raw_dir.iterdir() if p.is_file() and p.suffix.lower() in exts]
    paths = sorted(paths, key=lambda p: p.stem)
    if video_ids_arg.strip():
        wanted = set(parse_list_arg(video_ids_arg))
        paths = [p for p in paths if p.stem in wanted]
    return paths


def clamp_roi(x: int, y: int, w: int, h: int, img_w: int, img_h: int) -> Optional[ROI]:
    x0 = max(0, int(x))
    y0 = max(0, int(y))
    x1 = min(img_w, int(x + w))
    y1 = min(img_h, int(y + h))
    if x1 <= x0 + 1 or y1 <= y0 + 1:
        return None
    return x0, y0, x1 - x0, y1 - y0


def eye_bbox(points: np.ndarray, pad_ratio: float, img_w: int, img_h: int) -> Optional[ROI]:
    xs = points[:, 0]
    ys = points[:, 1]
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    w = max(1, x1 - x0 + 1)
    h = max(1, y1 - y0 + 1)
    pad_x = int(round(w * pad_ratio))
    pad_y = int(round(h * max(pad_ratio, 0.55)))
    return clamp_roi(x0 - pad_x, y0 - pad_y, w + 2 * pad_x, h + 2 * pad_y, img_w, img_h)


def rect_area(rect: dlib.rectangle) -> int:
    return max(0, rect.right() - rect.left()) * max(0, rect.bottom() - rect.top())


def detect_eye_rois_lowres(gray_orig: np.ndarray, detector, predictor, args: argparse.Namespace) -> Tuple[Optional[ROI], Optional[ROI], int]:
    """Run detector + predictor on downscaled image, then map eye ROIs back to original image."""
    orig_h, orig_w = gray_orig.shape[:2]
    scale = float(args.proc_scale)
    if scale <= 0 or scale > 1.0:
        raise ValueError("--proc_scale should be in (0, 1]")

    if abs(scale - 1.0) < 1e-9:
        gray_proc = gray_orig
    else:
        proc_w = max(1, int(round(orig_w * scale)))
        proc_h = max(1, int(round(orig_h * scale)))
        gray_proc = cv2.resize(gray_orig, (proc_w, proc_h), interpolation=cv2.INTER_AREA)

    proc_h, proc_w = gray_proc.shape[:2]
    rects = detector(gray_proc, int(args.upsample))
    if len(rects) == 0:
        return None, None, 0

    rect = max(rects, key=rect_area)
    rect = dlib.rectangle(
        max(0, rect.left()),
        max(0, rect.top()),
        min(proc_w - 1, rect.right()),
        min(proc_h - 1, rect.bottom()),
    )
    shape = predictor(gray_proc, rect)
    pts_proc = np.array([[shape.part(i).x, shape.part(i).y] for i in range(68)], dtype=np.float32)

    left_proc = eye_bbox(pts_proc[LEFT_EYE_IDX], args.pad_ratio, proc_w, proc_h)
    right_proc = eye_bbox(pts_proc[RIGHT_EYE_IDX], args.pad_ratio, proc_w, proc_h)
    if left_proc is None or right_proc is None:
        return None, None, 0

    inv = 1.0 / scale

    def map_roi(r: ROI) -> Optional[ROI]:
        x, y, w, h = r
        x0 = int(round(x * inv))
        y0 = int(round(y * inv))
        x1 = int(round((x + w) * inv))
        y1 = int(round((y + h) * inv))
        return clamp_roi(x0, y0, x1 - x0, y1 - y0, orig_w, orig_h)

    left = map_roi(left_proc)
    right = map_roi(right_proc)
    return left, right, int(left is not None and right is not None)


def crop_inner(patch: np.ndarray, x0f: float, x1f: float, y0f: float, y1f: float) -> np.ndarray:
    h, w = patch.shape[:2]
    x0 = max(0, min(w - 1, int(round(w * x0f))))
    x1 = max(x0 + 1, min(w, int(round(w * x1f))))
    y0 = max(0, min(h - 1, int(round(h * y0f))))
    y1 = max(y0 + 1, min(h, int(round(h * y1f))))
    return patch[y0:y1, x0:x1]


def max_consecutive_true_1d(arr: np.ndarray) -> int:
    best = 0
    cur = 0
    for v in arr:
        if bool(v):
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def column_max_runs(dark: np.ndarray) -> np.ndarray:
    h, w = dark.shape[:2]
    runs = np.zeros(w, dtype=np.int32)
    cur = np.zeros(w, dtype=np.int32)
    for y in range(h):
        cur = np.where(dark[y, :], cur + 1, 0)
        runs = np.maximum(runs, cur)
    return runs


def row_sigma_from_dark(dark: np.ndarray) -> float:
    h, _ = dark.shape[:2]
    row_counts = dark.sum(axis=1).astype(np.float64)
    total = float(row_counts.sum())
    if total <= 0:
        return 0.0
    ys = np.arange(h, dtype=np.float64)
    cy = float((ys * row_counts).sum() / total)
    var = float(((ys - cy) ** 2 * row_counts).sum() / total)
    return math.sqrt(max(0.0, var)) / max(1.0, float(h))


def feature_one_eye(gray: np.ndarray, roi: Optional[ROI], args: argparse.Namespace) -> Dict[str, float]:
    if roi is None:
        return {}
    x, y, w, h = roi
    patch = gray[y:y + h, x:x + w]
    if patch.size == 0:
        return {}

    center = crop_inner(patch, args.inner_x0, args.inner_x1, args.inner_y0, args.inner_y1)
    upper = crop_inner(patch, args.inner_x0, args.inner_x1, 0.00, 0.28)
    lower = crop_inner(patch, args.inner_x0, args.inner_x1, 0.55, 1.00)

    dark_fixed = patch < int(args.dark_thresh)
    center_dark_fixed = center < int(args.dark_thresh)

    mean_center = float(center.mean()) if center.size else 0.0
    t_adapt = int(max(0, min(255, round(mean_center - float(args.adapt_offset)))))
    dark_adapt = center < t_adapt

    row_counts = dark_fixed.sum(axis=1)
    min_dark_per_row = max(1, int(round(w * float(args.row_dark_frac))))
    active_rows = row_counts >= min_dark_per_row
    max_active_row_run = max_consecutive_true_1d(active_rows) / max(1, h)
    active_row_frac = float(active_rows.sum()) / max(1, h)

    def col_run_stats(dark: np.ndarray) -> Tuple[float, float, float]:
        runs = column_max_runs(dark)
        if runs.size == 0:
            return math.nan, math.nan, math.nan
        k = max(1, int(math.ceil(runs.size * float(args.topk_frac))))
        topk = np.sort(runs)[-k:]
        denom = max(1, dark.shape[0])
        return float(topk.mean()) / denom, float(runs.max()) / denom, float(runs.mean()) / denom

    col_run_topk_fixed, col_run_max_fixed, col_run_mean_fixed = col_run_stats(center_dark_fixed)
    col_run_topk_adapt, col_run_max_adapt, col_run_mean_adapt = col_run_stats(dark_adapt)

    row_sigma_fixed = row_sigma_from_dark(center_dark_fixed)
    row_sigma_adapt = row_sigma_from_dark(dark_adapt)

    center_mean = float(center.mean()) if center.size else math.nan
    upper_mean = float(upper.mean()) if upper.size else math.nan
    lower_mean = float(lower.mean()) if lower.size else math.nan
    vertical_contrast = ((upper_mean + lower_mean) * 0.5 - center_mean) / 255.0 if not math.isnan(upper_mean) and not math.isnan(lower_mean) else math.nan

    p16 = center.astype(np.int16)
    gy = np.abs(np.diff(p16, axis=0)) if center.shape[0] > 1 else np.zeros((0, center.shape[1]), dtype=np.int16)
    gx = np.abs(np.diff(p16, axis=1)) if center.shape[1] > 1 else np.zeros((center.shape[0], 0), dtype=np.int16)
    v_edge_density = float((gy > int(args.grad_thresh)).mean()) if gy.size else math.nan
    h_edge_density = float((gx > int(args.grad_thresh)).mean()) if gx.size else math.nan

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
        "col_run_max_adapt": col_run_max_adapt,
        "col_run_mean_adapt": col_run_mean_adapt,
        "row_sigma_fixed": row_sigma_fixed,
        "row_sigma_adapt": row_sigma_adapt,
        "vertical_contrast": vertical_contrast,
        "v_edge_density": v_edge_density,
        "h_edge_density": h_edge_density,
        "t_adapt": float(t_adapt),
    }


def mean_lr_features(left: Dict[str, float], right: Dict[str, float]) -> Dict[str, float]:
    keys = sorted(set(left.keys()) | set(right.keys()))
    out: Dict[str, float] = {}
    for k in keys:
        vals: List[float] = []
        for d in (left, right):
            if k in d:
                v = float(d[k])
                if not math.isnan(v):
                    vals.append(v)
        out[k] = float(np.mean(vals)) if vals else math.nan
    return out


def draw_debug(frame: np.ndarray, left: Optional[ROI], right: Optional[ROI], frame_id: int, det_ok: int, roi_age: int) -> np.ndarray:
    vis = frame.copy()
    for roi, color in [(left, (0, 255, 0)), (right, (0, 255, 255))]:
        if roi is not None:
            x, y, w, h = roi
            cv2.rectangle(vis, (x, y), (x + w, y + h), color, 2)
    cv2.putText(vis, f"frame={frame_id} det_ok={det_ok} roi_age={roi_age}", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
    return vis


def process_video(video_path: Path, detector, predictor, args: argparse.Namespace, debug_dir: Optional[Path]) -> List[dict]:
    video_id = video_path.stem
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"[WARN] failed to open: {video_path}")
        return []

    if args.start_frame > 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(args.start_frame))

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    print(f"[INFO] {video_id}: fps={fps:.3f}, frames={total_frames}, size={width}x{height}")

    writer = None
    if args.save_debug_video and debug_dir is not None and width > 0 and height > 0:
        debug_dir.mkdir(parents=True, exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(debug_dir / f"{video_id}_eyefeature_debug.mp4"), fourcc, max(fps, 1.0), (width, height))

    target_total = max(0, total_frames - int(args.start_frame))
    if args.max_frames > 0:
        target_total = min(target_total, int(args.max_frames))

    it = range(target_total) if args.no_progress or tqdm is None else tqdm(range(target_total), desc=video_id, unit="frame", ncols=100)

    last_left: Optional[ROI] = None
    last_right: Optional[ROI] = None
    last_update_frame = -10**9
    rows: List[dict] = []

    for i in it:
        ok, frame = cap.read()
        if not ok:
            break
        frame_id = int(args.start_frame) + i
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        need_update = (i % max(1, int(args.detect_interval)) == 0) or last_left is None or last_right is None
        update_ok = 0
        if need_update:
            left, right, det_ok = detect_eye_rois_lowres(gray, detector, predictor, args)
            if det_ok:
                last_left, last_right = left, right
                last_update_frame = frame_id
                update_ok = 1

        roi_age = frame_id - last_update_frame
        reuse_ok = last_left is not None and last_right is not None and roi_age <= int(args.reuse_max_age)
        det_ok = int(reuse_ok)

        row = {
            "video_id": video_id,
            "frame_id": frame_id,
            "timestamp_sec": frame_id / fps if fps > 0 else math.nan,
            "det_ok": det_ok,
            "dlib_update_ok": update_ok,
            "roi_age": roi_age if reuse_ok else -1,
            "frame_w": width,
            "frame_h": height,
        }

        for prefix, roi in [("left", last_left if reuse_ok else None), ("right", last_right if reuse_ok else None)]:
            if roi is None:
                row.update({f"{prefix}_x": -1, f"{prefix}_y": -1, f"{prefix}_w": -1, f"{prefix}_h": -1})
            else:
                x, y, w, h = roi
                row.update({f"{prefix}_x": x, f"{prefix}_y": y, f"{prefix}_w": w, f"{prefix}_h": h})

        if reuse_ok:
            f_left = feature_one_eye(gray, last_left, args)
            f_right = feature_one_eye(gray, last_right, args)
            feats = mean_lr_features(f_left, f_right)
            row.update(feats)
            if "col_run_topk_fixed" in feats and not math.isnan(feats["col_run_topk_fixed"]):
                row["score_q"] = int(round(float(feats["col_run_topk_fixed"]) * int(args.fixed_scale)))
            else:
                row["score_q"] = math.nan
        else:
            row["score_q"] = math.nan

        rows.append(row)

        if writer is not None:
            writer.write(draw_debug(frame, last_left if reuse_ok else None, last_right if reuse_ok else None, frame_id, det_ok, row["roi_age"]))

    cap.release()
    if writer is not None:
        writer.release()
    return rows


def main() -> None:
    args = parse_args()
    raw_dir = Path(args.raw_dir)
    out_csv = Path(args.out_csv)
    predictor_path = Path(args.shape_predictor)
    if not raw_dir.exists():
        raise FileNotFoundError(f"raw_dir not found: {raw_dir}")
    if not predictor_path.exists():
        raise FileNotFoundError(f"shape predictor not found: {predictor_path}")

    video_paths = collect_video_paths(raw_dir, args.exts, args.video_ids)
    if not video_paths:
        raise FileNotFoundError(f"No videos found in {raw_dir} with exts {args.exts}")

    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(str(predictor_path))
    debug_dir = Path(args.debug_dir) if args.debug_dir.strip() else out_csv.parent / "debug_videos"

    all_rows: List[dict] = []
    print(f"[INFO] videos={len(video_paths)}")
    for p in video_paths:
        all_rows.extend(process_video(p, detector, predictor, args, debug_dir))

    if not all_rows:
        raise RuntimeError("No frame rows produced")
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(all_rows)
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"[DONE] {out_csv} rows={len(df)}")
    if "det_ok" in df.columns:
        print(f"[INFO] det_ok_rate={df['det_ok'].mean():.4f}")


if __name__ == "__main__":
    main()
