from __future__ import annotations

"""
Extract frame-level robust EyeFeature values that match the robust HLS IP.

Typical usage:
  cd C:\\Users\\LC\\Desktop\\eyeblink8

  python scripts\\extract_eyefeature_robust_all.py ^
    --raw_dir raw_robust_dataset ^
    --out_csv work_eyefeature_robust\\frame_robust.csv ^
    --shape_predictor models\\shape_predictor_68_face_landmarks.dat ^
    --recursive ^
    --proc_scale 0.5 ^
    --detect_interval 20 ^
    --reuse_max_age 30

The normalized columns robust_f0 and robust_f1 are exactly feature_q / 4096.
With a 15-frame window and feature_names=robust_f0,robust_f1, the exported SVM
will receive the same x_q values as the board-side SVM path.
"""

import argparse
import json
import math
from collections import deque
from pathlib import Path
from typing import Deque, Dict, Iterable, List, Optional, Sequence, Tuple

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

MAX_CENTER_W = 128
MAX_CENTER_H = 64
INNER_X0_NUM = 10
INNER_X1_NUM = 90
INNER_Y0_NUM = 18
INNER_Y1_NUM = 88
INNER_DEN = 100
HIST_BINS = 64
HIST_SHIFT = 2
LOW_PCT_DEFAULT = 10
HIGH_PCT_DEFAULT = 60
MIN_CONTRAST = 12
LABEL_MAP = {"non_closed": 0, "open": 0, "opened": 0, "closed": 1}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Extract robust HLS-matched EyeFeature frame CSV.")
    p.add_argument("--raw_dir", type=str, required=True, help="Folder containing videos")
    p.add_argument("--out_csv", type=str, required=True, help="Output frame-level robust eyefeature csv")
    p.add_argument("--shape_predictor", type=str, required=True, help="shape_predictor_68_face_landmarks.dat")
    p.add_argument("--video_ids", type=str, default="", help="Optional comma-separated video stems to process")
    p.add_argument("--exts", type=str, default=".mp4,.avi,.mov,.mkv", help="Comma-separated extensions")
    p.add_argument("--recursive", action="store_true", help="Search videos recursively under raw_dir")
    p.add_argument("--start_frame", type=int, default=0)
    p.add_argument("--max_frames", type=int, default=-1, help="-1 means all")
    p.add_argument("--proc_scale", type=float, default=0.5, help="Scale used only for dlib detector+predictor input when --dlib_decimate <= 1")
    p.add_argument("--dlib_decimate", type=int, default=3, help="Board-style dlib decimation. 3 is the current local/board training choice; 0 uses --proc_scale.")
    p.add_argument("--dlib_width", type=int, default=0, help="Optional board-style dlib resized width after decimation; 0 disables.")
    p.add_argument("--upsample", type=int, default=0)
    p.add_argument("--detect_interval", type=int, default=20, help="Run dlib every N frames")
    p.add_argument("--reuse_max_age", type=int, default=30, help="Max frames to reuse last ROI")
    p.add_argument("--pad_ratio", type=float, default=0.65, help="Eye bbox padding ratio")
    p.add_argument("--pad_x", type=float, default=-1.0, help="Override horizontal eye padding ratio. 0.35 matches current board script.")
    p.add_argument("--pad_y", type=float, default=-1.0, help="Override vertical eye padding ratio. 0.65 matches current board script.")

    p.add_argument("--fixed_thresh", type=int, default=10, help="Robust low percentile. Legacy 70 maps to 10.")
    p.add_argument("--adapt_offset", type=int, default=60, help="Robust high/reference percentile. Legacy 25 maps to 60.")
    p.add_argument("--fixed_scale", type=int, default=4096)
    p.add_argument("--eye_roi_max_w", type=int, default=160, help="Pre-HLS ROI max width. 0 disables.")
    p.add_argument("--eye_roi_max_h", type=int, default=90, help="Pre-HLS ROI max height. 0 disables.")
    p.add_argument("--eye_frame_orientation", type=str, default="upright", choices=["upright", "board_raw"],
                   help="upright: compute features on decoded video frame; board_raw: invert rawfast rotate/flip and compute features like board EyeFeature raw mode.")
    p.add_argument("--saved_rotate", type=str, default="ccw", choices=["none", "cw", "ccw", "180"],
                   help="Rotate used by record_camera_rawfast.py when writing the video.")
    p.add_argument("--saved_flip", type=str, default="none", choices=["none", "h", "v", "hv"],
                   help="Flip used by record_camera_rawfast.py when writing the video.")

    p.add_argument("--label_name", type=str, default="", help="Optional label for every frame: open/non_closed/closed")
    p.add_argument("--no_label_infer", action="store_true", help="Do not infer label from parent directory name")

    p.add_argument("--svm_json", type=str, default="", help="Optional robust 30D SVM export json for offline prediction")
    p.add_argument("--svm_feature_names", type=str, default="robust_f0,robust_f1")
    p.add_argument("--svm_window_size", type=int, default=15)

    p.add_argument("--save_debug_video", action="store_true")
    p.add_argument("--debug_dir", type=str, default="")
    p.add_argument("--no_progress", action="store_true")
    return p.parse_args()


def parse_list_arg(s: str) -> List[str]:
    return [x.strip() for x in str(s).split(",") if x.strip()]


def collect_video_paths(raw_dir: Path, exts_arg: str, video_ids_arg: str, recursive: bool) -> List[Path]:
    exts = {e.lower().strip() for e in exts_arg.split(",") if e.strip()}
    iterator = raw_dir.rglob("*") if recursive else raw_dir.iterdir()
    paths = [p for p in iterator if p.is_file() and p.suffix.lower() in exts]
    paths = sorted(paths, key=lambda p: (str(p.parent).lower(), p.stem.lower()))
    if video_ids_arg.strip():
        wanted = set(parse_list_arg(video_ids_arg))
        paths = [p for p in paths if p.stem in wanted]
    return paths


def clamp_int(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, int(v)))


def round_ratio(value: int, num: int, den: int) -> int:
    return (int(value) * int(num) + int(den) // 2) // int(den)


def div_round_pos(num: int, den: int) -> int:
    if den <= 0:
        return 0
    return (int(num) + int(den) // 2) // int(den)


def clamp_roi(x: float, y: float, w: float, h: float, img_w: int, img_h: int) -> Optional[ROI]:
    x0 = max(0, int(round(x)))
    y0 = max(0, int(round(y)))
    x1 = min(int(img_w), int(round(x + w)))
    y1 = min(int(img_h), int(round(y + h)))
    if x1 <= x0 + 1 or y1 <= y0 + 1:
        return None
    return x0, y0, x1 - x0, y1 - y0


def shrink_roi_for_eye_ip(roi: Optional[ROI], frame_w: int, frame_h: int, max_w: int, max_h: int) -> Tuple[Optional[ROI], int]:
    if roi is None:
        return None, 0
    x, y, w, h = roi
    r = clamp_roi(x, y, w, h, frame_w, frame_h)
    if r is None:
        return None, 0
    x, y, w, h = r
    new_w = w if int(max_w) <= 0 else min(w, int(max_w))
    new_h = h if int(max_h) <= 0 else min(h, int(max_h))
    if new_w == w and new_h == h:
        return r, 0
    cx = x + (w - 1) / 2.0
    cy = y + (h - 1) / 2.0
    shrunk = clamp_roi(cx - (new_w - 1) / 2.0, cy - (new_h - 1) / 2.0, new_w, new_h, frame_w, frame_h)
    return shrunk, 1


def eye_bbox(points: np.ndarray, pad_x: float, pad_y: float, img_w: int, img_h: int) -> Optional[ROI]:
    xs = points[:, 0]
    ys = points[:, 1]
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    w = max(1, x1 - x0 + 1)
    h = max(1, y1 - y0 + 1)
    px = int(round(w * float(pad_x)))
    py = int(round(h * float(pad_y)))
    return clamp_roi(x0 - px, y0 - py, w + 2 * px, h + 2 * py, img_w, img_h)


def rect_area(rect: dlib.rectangle) -> int:
    return max(0, rect.right() - rect.left()) * max(0, rect.bottom() - rect.top())


def detect_eye_rois_lowres(gray_orig: np.ndarray, detector, predictor, args: argparse.Namespace) -> Tuple[Optional[ROI], Optional[ROI], int]:
    orig_h, orig_w = gray_orig.shape[:2]
    dec = max(0, int(args.dlib_decimate))
    if dec > 1:
        gray_proc = gray_orig[::dec, ::dec]
        sx = float(orig_w) / float(max(1, gray_proc.shape[1]))
        sy = float(orig_h) / float(max(1, gray_proc.shape[0]))
    else:
        scale = float(args.proc_scale)
        if scale <= 0 or scale > 1.0:
            raise ValueError("--proc_scale should be in (0, 1]")
        if abs(scale - 1.0) < 1e-9:
            gray_proc = gray_orig
        else:
            proc_w = max(1, int(round(orig_w * scale)))
            proc_h = max(1, int(round(orig_h * scale)))
            gray_proc = cv2.resize(gray_orig, (proc_w, proc_h), interpolation=cv2.INTER_AREA)
        sx = float(orig_w) / float(max(1, gray_proc.shape[1]))
        sy = float(orig_h) / float(max(1, gray_proc.shape[0]))

    if int(args.dlib_width) > 0 and gray_proc.shape[1] != int(args.dlib_width):
        old_h, old_w = gray_proc.shape[:2]
        new_w = int(args.dlib_width)
        new_h = max(1, int(round(old_h * (float(new_w) / float(max(1, old_w))))))
        gray_proc = cv2.resize(gray_proc, (new_w, new_h), interpolation=cv2.INTER_AREA)
        sx = float(orig_w) / float(max(1, gray_proc.shape[1]))
        sy = float(orig_h) / float(max(1, gray_proc.shape[0]))

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

    pad_x = float(args.pad_x) if float(args.pad_x) >= 0 else float(args.pad_ratio)
    pad_y = float(args.pad_y) if float(args.pad_y) >= 0 else max(float(args.pad_ratio), 0.55)
    left_proc = eye_bbox(pts_proc[LEFT_EYE_IDX], pad_x, pad_y, proc_w, proc_h)
    right_proc = eye_bbox(pts_proc[RIGHT_EYE_IDX], pad_x, pad_y, proc_w, proc_h)
    if left_proc is None or right_proc is None:
        return None, None, 0

    def map_roi(r: ROI) -> Optional[ROI]:
        x, y, w, h = r
        x0 = int(round(x * sx))
        y0 = int(round(y * sy))
        x1 = int(round((x + w) * sx))
        y1 = int(round((y + h) * sy))
        return clamp_roi(x0, y0, x1 - x0, y1 - y0, orig_w, orig_h)

    left = map_roi(left_proc)
    right = map_roi(right_proc)
    return left, right, int(left is not None and right is not None)


def hls_gray_from_bgr(frame: np.ndarray) -> np.ndarray:
    if frame.ndim == 2:
        return frame.astype(np.uint8, copy=False)
    b = frame[:, :, 0].astype(np.uint16)
    g = frame[:, :, 1].astype(np.uint16)
    r = frame[:, :, 2].astype(np.uint16)
    y = (77 * r + 150 * g + 29 * b + 128) >> 8
    return y.astype(np.uint8)


def inverse_saved_rotate_flip(frame: np.ndarray, saved_rotate: str, saved_flip: str) -> np.ndarray:
    """Invert record_camera_rawfast.py rotate_flip_bgr()."""
    out = frame
    flip = str(saved_flip).lower()
    if flip == "h":
        out = np.fliplr(out)
    elif flip == "v":
        out = np.flipud(out)
    elif flip == "hv":
        out = np.flipud(np.fliplr(out))
    elif flip in ("none", ""):
        pass
    else:
        raise ValueError("--saved_flip must be none/h/v/hv")

    rotate = str(saved_rotate).lower()
    if rotate == "cw":
        out = np.rot90(out, k=1)
    elif rotate == "ccw":
        out = np.rot90(out, k=3)
    elif rotate == "180":
        out = np.rot90(out, k=2)
    elif rotate in ("none", "0", ""):
        pass
    else:
        raise ValueError("--saved_rotate must be none/cw/ccw/180")
    return np.ascontiguousarray(out)


def apply_saved_rotate_flip(frame: np.ndarray, saved_rotate: str, saved_flip: str) -> np.ndarray:
    """Apply record_camera_rawfast.py rotate_flip_bgr() to a raw-oriented frame."""
    out = frame
    rotate = str(saved_rotate).lower()
    if rotate == "cw":
        out = np.rot90(out, k=3)
    elif rotate == "ccw":
        out = np.rot90(out, k=1)
    elif rotate == "180":
        out = np.rot90(out, k=2)
    elif rotate in ("none", "0", ""):
        pass
    else:
        raise ValueError("--saved_rotate must be none/cw/ccw/180")

    flip = str(saved_flip).lower()
    if flip == "h":
        out = np.fliplr(out)
    elif flip == "v":
        out = np.flipud(out)
    elif flip == "hv":
        out = np.flipud(np.fliplr(out))
    elif flip in ("none", ""):
        pass
    else:
        raise ValueError("--saved_flip must be none/h/v/hv")
    return np.ascontiguousarray(out)


def transform_point_raw_to_upright(xr: float, yr: float, raw_w: int, raw_h: int, rotate: str, flip: str) -> Tuple[float, float]:
    rotate = str(rotate).lower()
    if rotate == "ccw":
        xu, yu = yr, raw_w - 1 - xr
        up_w, up_h = raw_h, raw_w
    elif rotate == "cw":
        xu, yu = raw_h - 1 - yr, xr
        up_w, up_h = raw_h, raw_w
    elif rotate == "180":
        xu, yu = raw_w - 1 - xr, raw_h - 1 - yr
        up_w, up_h = raw_w, raw_h
    elif rotate in ("none", "0", ""):
        xu, yu = xr, yr
        up_w, up_h = raw_w, raw_h
    else:
        raise ValueError("--saved_rotate must be none/cw/ccw/180")

    flip = str(flip).lower()
    if "h" in flip:
        xu = (up_w - 1) - xu
    if "v" in flip:
        yu = (up_h - 1) - yu
    return xu, yu


def transform_point_upright_to_raw(xu: float, yu: float, raw_w: int, raw_h: int, rotate: str, flip: str) -> Tuple[float, float]:
    rotate = str(rotate).lower()
    up_w = raw_h if rotate in ("cw", "ccw") else raw_w
    up_h = raw_w if rotate in ("cw", "ccw") else raw_h

    flip = str(flip).lower()
    if "h" in flip:
        xu = (up_w - 1) - xu
    if "v" in flip:
        yu = (up_h - 1) - yu

    if rotate == "ccw":
        xr, yr = raw_w - 1 - yu, xu
    elif rotate == "cw":
        xr, yr = yu, raw_h - 1 - xu
    elif rotate == "180":
        xr, yr = raw_w - 1 - xu, raw_h - 1 - yu
    elif rotate in ("none", "0", ""):
        xr, yr = xu, yu
    else:
        raise ValueError("--saved_rotate must be none/cw/ccw/180")
    return xr, yr


def transform_roi_upright_to_raw(roi: Optional[ROI], raw_w: int, raw_h: int, rotate: str, flip: str) -> Optional[ROI]:
    if roi is None:
        return None
    x, y, w, h = roi
    pts = [
        transform_point_upright_to_raw(x, y, raw_w, raw_h, rotate, flip),
        transform_point_upright_to_raw(x + w - 1, y, raw_w, raw_h, rotate, flip),
        transform_point_upright_to_raw(x, y + h - 1, raw_w, raw_h, rotate, flip),
        transform_point_upright_to_raw(x + w - 1, y + h - 1, raw_w, raw_h, rotate, flip),
    ]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return clamp_roi(min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1, raw_w, raw_h)


def transform_roi_raw_to_upright(roi: Optional[ROI], raw_w: int, raw_h: int, rotate: str, flip: str) -> Optional[ROI]:
    if roi is None:
        return None
    x, y, w, h = roi
    pts = [
        transform_point_raw_to_upright(x, y, raw_w, raw_h, rotate, flip),
        transform_point_raw_to_upright(x + w - 1, y, raw_w, raw_h, rotate, flip),
        transform_point_raw_to_upright(x, y + h - 1, raw_w, raw_h, rotate, flip),
        transform_point_raw_to_upright(x + w - 1, y + h - 1, raw_w, raw_h, rotate, flip),
    ]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    up_w = raw_h if str(rotate).lower() in ("cw", "ccw") else raw_w
    up_h = raw_w if str(rotate).lower() in ("cw", "ccw") else raw_h
    return clamp_roi(min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1, up_w, up_h)


def sanitize_low_percent(v: int) -> int:
    if 1 <= int(v) <= 40:
        return int(v)
    return LOW_PCT_DEFAULT


def sanitize_high_percent(v: int, low_pct: int) -> int:
    v = int(v)
    if v > int(low_pct) and v <= 95:
        return v
    fallback = int(low_pct) + 50
    if fallback < HIGH_PCT_DEFAULT:
        fallback = HIGH_PCT_DEFAULT
    if fallback > 90:
        fallback = 90
    return fallback


def robust_percent_params(fixed_thresh: int, adapt_offset: int) -> Tuple[int, int]:
    if int(fixed_thresh) == 70 and int(adapt_offset) == 25:
        return LOW_PCT_DEFAULT, HIGH_PCT_DEFAULT
    low_pct = sanitize_low_percent(int(fixed_thresh))
    high_pct = sanitize_high_percent(int(adapt_offset), low_pct)
    return low_pct, high_pct


def make_eye_cfg(frame_w: int, frame_h: int, roi: Optional[ROI]) -> Dict[str, int]:
    out = {"valid": 0, "cx0": 0, "cy0": 0, "cw": 0, "ch": 0}
    if roi is None:
        return out
    x, y, w, h = roi
    if frame_w <= 0 or frame_h <= 0 or w <= 0 or h <= 0:
        return out

    rx0 = clamp_int(x, 0, frame_w - 1)
    ry0 = clamp_int(y, 0, frame_h - 1)
    rx1 = clamp_int(x + w, rx0 + 1, frame_w)
    ry1 = clamp_int(y + h, ry0 + 1, frame_h)
    rw = rx1 - rx0
    rh = ry1 - ry0

    ix0 = round_ratio(rw, INNER_X0_NUM, INNER_DEN)
    ix1 = round_ratio(rw, INNER_X1_NUM, INNER_DEN)
    iy0 = round_ratio(rh, INNER_Y0_NUM, INNER_DEN)
    iy1 = round_ratio(rh, INNER_Y1_NUM, INNER_DEN)

    ix0 = clamp_int(ix0, 0, rw - 1)
    ix1 = clamp_int(ix1, ix0 + 1, rw)
    iy0 = clamp_int(iy0, 0, rh - 1)
    iy1 = clamp_int(iy1, iy0 + 1, rh)

    cw = ix1 - ix0
    ch = iy1 - iy0
    if cw <= 0 or ch <= 0 or cw > MAX_CENTER_W or ch > MAX_CENTER_H:
        return out

    out.update({"valid": 1, "cx0": rx0 + ix0, "cy0": ry0 + iy0, "cw": cw, "ch": ch})
    return out


def percentile_threshold(hist: np.ndarray, count: int, percent: int) -> int:
    if count <= 0:
        return 0
    target = div_round_pos(count * int(percent), 100)
    target = max(1, target)
    cumulative = 0
    selected = HIST_BINS - 1
    for i in range(HIST_BINS):
        cumulative += int(hist[i])
        if cumulative >= target:
            selected = i
            break
    return clamp_int((selected << HIST_SHIFT) + ((1 << HIST_SHIFT) - 1), 0, 255)


def column_run_max(dark: np.ndarray) -> np.ndarray:
    h, w = dark.shape[:2]
    cur = np.zeros((w,), dtype=np.int32)
    best = np.zeros((w,), dtype=np.int32)
    for y in range(h):
        cur = np.where(dark[y, :], cur + 1, 0)
        best = np.maximum(best, cur)
    return best


def max_consecutive_true(arr: np.ndarray) -> int:
    best = 0
    cur = 0
    for v in arr:
        if bool(v):
            cur += 1
            if cur > best:
                best = cur
        else:
            cur = 0
    return best


def q_ratio(num: int, den: int, fixed_scale: int) -> int:
    return div_round_pos(int(num) * int(fixed_scale), max(1, int(den)))


def robust_one_eye(gray: np.ndarray, roi: Optional[ROI], low_pct: int, high_pct: int, fixed_scale: int) -> Dict[str, int]:
    h, w = gray.shape[:2]
    cfg = make_eye_cfg(w, h, roi)
    if not cfg["valid"]:
        return {
            "valid": 0,
            "feature0_q": 0,
            "feature1_q": 0,
            "t_low": 0,
            "t_high": 0,
            "q_dark": 0,
            "q_ref": 0,
            "contrast": 0,
            "cw": int(cfg["cw"]),
            "ch": int(cfg["ch"]),
            "dark_low_q": 0,
            "dark_high_q": 0,
            "col_frac_low_q": 0,
            "col_frac_high_q": 0,
            "row_frac_low_q": 0,
            "row_frac_high_q": 0,
            "row_run_low_q": 0,
            "row_run_high_q": 0,
            "contrast_q": 0,
            "q_dark_q": 0,
            "q_ref_q": 0,
            "mean_q": 0,
            "std_q": 0,
        }

    cx0 = int(cfg["cx0"])
    cy0 = int(cfg["cy0"])
    cw = int(cfg["cw"])
    ch = int(cfg["ch"])
    patch = gray[cy0:cy0 + ch, cx0:cx0 + cw].astype(np.uint8, copy=False)
    vals = patch.reshape(-1)
    hist = np.bincount((vals >> HIST_SHIFT).astype(np.int32), minlength=HIST_BINS)[:HIST_BINS]

    q_dark = percentile_threshold(hist, cw * ch, low_pct)
    q_ref = percentile_threshold(hist, cw * ch, high_pct)
    if q_ref < q_dark:
        q_ref = q_dark
    contrast = q_ref - q_dark
    t_low = q_dark
    t_high = q_dark
    if contrast >= MIN_CONTRAST:
        t_low = q_dark + div_round_pos(contrast, 4)
        t_high = q_dark + div_round_pos(contrast, 2)

    if contrast >= MIN_CONTRAST:
        dark_low = patch <= t_low
        dark_high = patch <= t_high
        run_low = column_run_max(dark_low)
        run_high = column_run_max(dark_high)
        max_low = int(run_low.max()) if run_low.size else 0
        k = max(1, (cw + 3) // 4)
        topk_high = int(np.sort(run_high)[-k:].sum()) if run_high.size else 0
        dark_low_count = int(dark_low.sum())
        dark_high_count = int(dark_high.sum())
        col_frac_low = int((run_low > 0).sum())
        col_frac_high = int((run_high > 0).sum())
        min_dark_per_row = max(1, div_round_pos(cw, 10))
        row_active_low = dark_low.sum(axis=1) >= min_dark_per_row
        row_active_high = dark_high.sum(axis=1) >= min_dark_per_row
        row_frac_low = int(row_active_low.sum())
        row_frac_high = int(row_active_high.sum())
        row_run_low = max_consecutive_true(row_active_low)
        row_run_high = max_consecutive_true(row_active_high)
    else:
        max_low = 0
        k = max(1, (cw + 3) // 4)
        topk_high = 0
        dark_low_count = 0
        dark_high_count = 0
        col_frac_low = 0
        col_frac_high = 0
        row_frac_low = 0
        row_frac_high = 0
        row_run_low = 0
        row_run_high = 0

    f0 = div_round_pos(max_low * int(fixed_scale), ch)
    f1 = div_round_pos(topk_high * int(fixed_scale), k * ch)
    count = cw * ch
    mean_q = q_ratio(int(round(float(patch.mean()))), 255, fixed_scale)
    std_q = q_ratio(int(round(float(patch.std()))), 255, fixed_scale)
    return {
        "valid": 1,
        "feature0_q": int(f0),
        "feature1_q": int(f1),
        "t_low": int(t_low),
        "t_high": int(t_high),
        "q_dark": int(q_dark),
        "q_ref": int(q_ref),
        "contrast": int(contrast),
        "cw": cw,
        "ch": ch,
        "max_run_low": int(max_low),
        "topk_sum_high": int(topk_high),
        "topk_k": int(k),
        "dark_low_q": q_ratio(dark_low_count, count, fixed_scale),
        "dark_high_q": q_ratio(dark_high_count, count, fixed_scale),
        "col_frac_low_q": q_ratio(col_frac_low, cw, fixed_scale),
        "col_frac_high_q": q_ratio(col_frac_high, cw, fixed_scale),
        "row_frac_low_q": q_ratio(row_frac_low, ch, fixed_scale),
        "row_frac_high_q": q_ratio(row_frac_high, ch, fixed_scale),
        "row_run_low_q": q_ratio(row_run_low, ch, fixed_scale),
        "row_run_high_q": q_ratio(row_run_high, ch, fixed_scale),
        "contrast_q": q_ratio(contrast, 255, fixed_scale),
        "q_dark_q": q_ratio(q_dark, 255, fixed_scale),
        "q_ref_q": q_ratio(q_ref, 255, fixed_scale),
        "mean_q": int(mean_q),
        "std_q": int(std_q),
    }


def combine_two_eyes(qa: int, va: int, qb: int, vb: int) -> int:
    if va and vb:
        return (int(qa) + int(qb) + 1) >> 1
    if va:
        return int(qa)
    if vb:
        return int(qb)
    return 0


def pack_debug(left: Dict[str, int], right: Dict[str, int]) -> int:
    l = ((int(left["t_high"]) & 0xFF) << 8) | (int(left["t_low"]) & 0xFF)
    r = ((int(right["t_high"]) & 0xFF) << 8) | (int(right["t_low"]) & 0xFF)
    return ((r & 0xFFFF) << 16) | (l & 0xFFFF)


EYE_STAT_Q_KEYS = [
    ("f0", "feature0_q"),
    ("f1", "feature1_q"),
    ("dark_low", "dark_low_q"),
    ("dark_high", "dark_high_q"),
    ("col_frac_low", "col_frac_low_q"),
    ("col_frac_high", "col_frac_high_q"),
    ("row_frac_low", "row_frac_low_q"),
    ("row_frac_high", "row_frac_high_q"),
    ("row_run_low", "row_run_low_q"),
    ("row_run_high", "row_run_high_q"),
    ("contrast", "contrast_q"),
    ("q_dark", "q_dark_q"),
    ("q_ref", "q_ref_q"),
    ("mean_gray", "mean_q"),
    ("std_gray", "std_q"),
]


def combine_stat_q(left: Dict[str, int], right: Dict[str, int], q_key: str) -> int:
    return combine_two_eyes(int(left.get(q_key, 0)), int(left.get("valid", 0)), int(right.get(q_key, 0)), int(right.get("valid", 0)))


def robust_features_lr(gray: np.ndarray, left_roi: Optional[ROI], right_roi: Optional[ROI], args: argparse.Namespace) -> Dict[str, int]:
    low_pct, high_pct = robust_percent_params(int(args.fixed_thresh), int(args.adapt_offset))
    fixed_scale = int(args.fixed_scale) if int(args.fixed_scale) > 0 else 4096
    left = robust_one_eye(gray, left_roi, low_pct, high_pct, fixed_scale)
    right = robust_one_eye(gray, right_roi, low_pct, high_pct, fixed_scale)
    lv = int(left["valid"])
    rv = int(right["valid"])
    out_valid = int(bool(lv or rv))
    f0 = combine_two_eyes(left["feature0_q"], lv, right["feature0_q"], rv)
    f1 = combine_two_eyes(left["feature1_q"], lv, right["feature1_q"], rv)
    debug = pack_debug(left, right) if out_valid else 0
    if not out_valid:
        f0 = 0
        f1 = 0

    out = {
        "eye_valid": out_valid,
        "feature0_q": int(f0),
        "feature1_q": int(f1),
        "eye_debug": int(debug),
        "low_pct": int(low_pct),
        "high_pct": int(high_pct),
        "left_t_low": int(left["t_low"]),
        "left_t_high": int(left["t_high"]),
        "right_t_low": int(right["t_low"]),
        "right_t_high": int(right["t_high"]),
        "left_q_dark": int(left["q_dark"]),
        "left_q_ref": int(left["q_ref"]),
        "right_q_dark": int(right["q_dark"]),
        "right_q_ref": int(right["q_ref"]),
        "left_contrast": int(left["contrast"]),
        "right_contrast": int(right["contrast"]),
        "left_center_w": int(left["cw"]),
        "left_center_h": int(left["ch"]),
        "right_center_w": int(right["cw"]),
        "right_center_h": int(right["ch"]),
    }
    for name, q_key in EYE_STAT_Q_KEYS:
        lq = int(left.get(q_key, 0))
        rq = int(right.get(q_key, 0))
        aq = combine_stat_q(left, right, q_key) if out_valid else 0
        dq = abs(lq - rq) if out_valid and lv and rv else 0
        out[f"left_{name}_q"] = lq
        out[f"right_{name}_q"] = rq
        out[f"avg_{name}_q"] = aq
        out[f"diff_{name}_q"] = dq
        out[f"left_{name}"] = float(lq) / float(fixed_scale)
        out[f"right_{name}"] = float(rq) / float(fixed_scale)
        out[f"avg_{name}"] = float(aq) / float(fixed_scale)
        out[f"diff_{name}"] = float(dq) / float(fixed_scale)
    out["lr_valid_both"] = int(bool(lv and rv))
    return out


def infer_label(video_path: Path, explicit: str, no_infer: bool) -> Tuple[str, Optional[int]]:
    name = explicit.strip().lower()
    if not name and not no_infer:
        parent = video_path.parent.name.strip().lower()
        if parent in LABEL_MAP:
            name = parent
    if not name:
        return "", None
    if name not in LABEL_MAP:
        raise ValueError(f"Unknown label_name '{name}'. Use open/non_closed/closed.")
    normalized = "closed" if LABEL_MAP[name] == 1 else "non_closed"
    return normalized, int(LABEL_MAP[name])


def roi_to_row(row: dict, prefix: str, roi: Optional[ROI]) -> None:
    if roi is None:
        row.update({f"{prefix}_x": -1, f"{prefix}_y": -1, f"{prefix}_w": -1, f"{prefix}_h": -1})
    else:
        x, y, w, h = roi
        row.update({f"{prefix}_x": int(x), f"{prefix}_y": int(y), f"{prefix}_w": int(w), f"{prefix}_h": int(h)})


def load_svm_json(path: str) -> Optional[Dict[str, object]]:
    if not str(path).strip():
        return None
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"svm_json not found: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    w_q = data.get("w_q")
    feature_cols = data.get("feature_cols")
    if not isinstance(w_q, list) or not isinstance(feature_cols, list):
        raise ValueError("svm_json must contain w_q and feature_cols")
    b_q = data.get("b_q_practical", data.get("b_q", data.get("b_q_zero_threshold")))
    if b_q is None:
        raise ValueError("svm_json must contain b_q_practical, b_q, or b_q_zero_threshold")
    if len(w_q) != len(feature_cols):
        raise ValueError("svm_json w_q length does not match feature_cols")
    input_scale = int(data.get("fixed_scale_for_input_x_q", data.get("input_scale", 4096)))
    return {
        "w_q": [int(x) for x in w_q],
        "b_q": int(b_q),
        "feature_cols": [str(x) for x in feature_cols],
        "input_scale": input_scale,
    }


def column_value_from_window(win: Sequence[Dict[str, float]], col: str, input_scale: int) -> int:
    base, idx_s = col.rsplit("_", 1)
    idx = int(idx_s)
    if idx < 0 or idx >= len(win):
        raise IndexError(f"SVM feature column index out of window: {col}")
    if base not in win[idx]:
        raise KeyError(f"SVM feature column '{col}' expects frame feature '{base}', but it is missing")
    return int(round(float(win[idx][base]) * float(input_scale)))


def maybe_predict_svm(row: dict, window: Deque[Dict[str, float]], svm: Optional[Dict[str, object]]) -> None:
    row["svm_ready"] = 0
    row["svm_pred"] = -1
    row["svm_score_q"] = 0
    if svm is None:
        return
    feature_cols = svm["feature_cols"]
    if len(window) < max((int(str(c).rsplit("_", 1)[1]) for c in feature_cols), default=-1) + 1:
        return
    try:
        input_scale = int(svm.get("input_scale", 4096))
        x_q = [column_value_from_window(list(window), str(c), input_scale) for c in feature_cols]
    except (KeyError, IndexError, ValueError) as exc:
        row["svm_error"] = str(exc)
        return
    score_q = int(svm["b_q"])
    for w, x in zip(svm["w_q"], x_q):
        score_q += int(w) * int(x)
    row["svm_ready"] = 1
    row["svm_pred"] = int(score_q > 0)
    row["svm_score_q"] = int(score_q)


def draw_debug(
    frame: np.ndarray,
    left_pre: Optional[ROI],
    right_pre: Optional[ROI],
    left: Optional[ROI],
    right: Optional[ROI],
    row: dict,
) -> np.ndarray:
    vis = frame.copy()
    for roi, color, label, thickness in [
        (left_pre, (0, 180, 0), "Lpre", 1),
        (right_pre, (0, 180, 0), "Rpre", 1),
        (left, (255, 255, 0), "L", 2),
        (right, (255, 255, 0), "R", 2),
    ]:
        if roi is None:
            continue
        x, y, w, h = roi
        cv2.rectangle(vis, (x, y), (x + w - 1, y + h - 1), color, thickness)
        cv2.putText(vis, label, (x, max(15, y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
    lines = [
        f"frame={row.get('frame_id')} det={row.get('det_ok')} eye={row.get('eye_valid')} age={row.get('roi_age')}",
        f"f=({row.get('feature0_q')},{row.get('feature1_q')}) pred={row.get('svm_pred', -1)}",
        f"thr L=({row.get('left_t_low')},{row.get('left_t_high')}) R=({row.get('right_t_low')},{row.get('right_t_high')})",
    ]
    y = 24
    for line in lines:
        cv2.putText(vis, line, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 3)
        cv2.putText(vis, line, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        y += 22
    return vis


def process_video(
    video_path: Path,
    detector,
    predictor,
    args: argparse.Namespace,
    debug_dir: Optional[Path],
    svm: Optional[Dict[str, object]],
) -> List[dict]:
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
    label_name, label = infer_label(video_path, args.label_name, bool(args.no_label_infer))
    print(f"[INFO] {video_id}: fps={fps:.3f}, frames={total_frames}, size={width}x{height}, label={label_name or 'none'}")

    writer = None
    if args.save_debug_video and debug_dir is not None and width > 0 and height > 0:
        debug_dir.mkdir(parents=True, exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(debug_dir / f"{video_id}_robust_debug.mp4"), fourcc, max(fps, 1.0), (width, height))

    frame_limit = int(args.max_frames) if int(args.max_frames) > 0 else None
    if total_frames > 0:
        target_total = max(0, total_frames - int(args.start_frame))
        if frame_limit is not None:
            target_total = min(target_total, frame_limit)
        iterator: Iterable[int] = range(target_total)
        if not args.no_progress and tqdm is not None:
            iterator = tqdm(iterator, desc=video_id, unit="frame", ncols=100)
    else:
        target_total = frame_limit if frame_limit is not None else 10**12
        iterator = range(target_total)

    last_left_pre: Optional[ROI] = None
    last_right_pre: Optional[ROI] = None
    last_update_frame = -10**9
    rows: List[dict] = []
    svm_window: Deque[Dict[str, float]] = deque(maxlen=max(1, int(args.svm_window_size)))

    for i in iterator:
        ok, frame = cap.read()
        if not ok:
            break
        frame_id = int(args.start_frame) + int(i)
        gray_upright = hls_gray_from_bgr(frame)
        if args.eye_frame_orientation == "board_raw":
            eye_frame = inverse_saved_rotate_flip(frame, args.saved_rotate, args.saved_flip)
            eye_gray = hls_gray_from_bgr(eye_frame)
        else:
            eye_gray = gray_upright
        eye_h, eye_w = eye_gray.shape[:2]

        need_update = (i % max(1, int(args.detect_interval)) == 0) or last_left_pre is None or last_right_pre is None
        update_ok = 0
        if need_update:
            left_pre, right_pre, det_ok = detect_eye_rois_lowres(gray_upright, detector, predictor, args)
            if det_ok:
                last_left_pre, last_right_pre = left_pre, right_pre
                last_update_frame = frame_id
                update_ok = 1

        roi_age = frame_id - last_update_frame
        reuse_ok = last_left_pre is not None and last_right_pre is not None and roi_age <= int(args.reuse_max_age)
        left_pre_use = last_left_pre if reuse_ok else None
        right_pre_use = last_right_pre if reuse_ok else None
        if args.eye_frame_orientation == "board_raw":
            left_pre_eye = transform_roi_upright_to_raw(left_pre_use, eye_w, eye_h, args.saved_rotate, args.saved_flip)
            right_pre_eye = transform_roi_upright_to_raw(right_pre_use, eye_w, eye_h, args.saved_rotate, args.saved_flip)
        else:
            left_pre_eye = left_pre_use
            right_pre_eye = right_pre_use
        left_sent, left_shrink = shrink_roi_for_eye_ip(left_pre_eye, eye_w, eye_h, args.eye_roi_max_w, args.eye_roi_max_h)
        right_sent, right_shrink = shrink_roi_for_eye_ip(right_pre_eye, eye_w, eye_h, args.eye_roi_max_w, args.eye_roi_max_h)
        det_ok = int(reuse_ok and left_sent is not None and right_sent is not None)
        if args.eye_frame_orientation == "board_raw":
            left_sent_draw = transform_roi_raw_to_upright(left_sent, eye_w, eye_h, args.saved_rotate, args.saved_flip)
            right_sent_draw = transform_roi_raw_to_upright(right_sent, eye_w, eye_h, args.saved_rotate, args.saved_flip)
        else:
            left_sent_draw = left_sent
            right_sent_draw = right_sent

        row = {
            "video_id": video_id,
            "source_path": str(video_path),
            "frame_id": frame_id,
            "timestamp_sec": frame_id / fps if fps > 0 else math.nan,
            "det_ok": det_ok,
            "dlib_update_ok": update_ok,
            "roi_age": roi_age if reuse_ok else -1,
            "frame_w": width,
            "frame_h": height,
            "eye_frame_w": eye_w,
            "eye_frame_h": eye_h,
            "eye_frame_orientation": args.eye_frame_orientation,
            "dlib_decimate": int(args.dlib_decimate),
            "eye_roi_shrink": int(bool(left_shrink or right_shrink)),
            "fixed_thresh": int(args.fixed_thresh),
            "adapt_offset": int(args.adapt_offset),
            "fixed_scale": int(args.fixed_scale),
        }
        if label_name:
            row["label_name"] = label_name
            row["label"] = int(label)

        roi_to_row(row, "left_pre", left_pre_use)
        roi_to_row(row, "right_pre", right_pre_use)
        roi_to_row(row, "left", left_sent)
        roi_to_row(row, "right", right_sent)

        if det_ok:
            feats = robust_features_lr(eye_gray, left_sent, right_sent, args)
            row.update(feats)
            row["robust_f0"] = float(row["feature0_q"]) / float(max(1, int(args.fixed_scale)))
            row["robust_f1"] = float(row["feature1_q"]) / float(max(1, int(args.fixed_scale)))
        else:
            row.update({
                "eye_valid": 0,
                "feature0_q": 0,
                "feature1_q": 0,
                "robust_f0": math.nan,
                "robust_f1": math.nan,
                "eye_debug": 0,
                "low_pct": math.nan,
                "high_pct": math.nan,
            })
            svm_window.clear()

        if int(row.get("eye_valid", 0)) == 1:
            svm_window.append({"robust_f0": float(row["robust_f0"]), "robust_f1": float(row["robust_f1"])})
        else:
            svm_window.clear()
        maybe_predict_svm(row, svm_window, svm)

        rows.append(row)
        if writer is not None:
            writer.write(draw_debug(frame, left_pre_use, right_pre_use, left_sent_draw, right_sent_draw, row))

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

    video_paths = collect_video_paths(raw_dir, args.exts, args.video_ids, bool(args.recursive))
    if not video_paths:
        raise RuntimeError(f"No videos found under {raw_dir}")

    svm = load_svm_json(args.svm_json)
    if svm is not None:
        allowed_prefixes = tuple(parse_list_arg(args.svm_feature_names))
        bad = [c for c in svm["feature_cols"] if not any(str(c).startswith(prefix + "_") for prefix in allowed_prefixes)]
        if bad:
            print(f"[WARN] svm_json feature columns do not match robust features; offline prediction disabled. First bad column: {bad[0]}")
            svm = None

    print(f"[INFO] loading dlib detector + predictor: {predictor_path}")
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(str(predictor_path))
    debug_dir = Path(args.debug_dir) if args.debug_dir else (out_csv.parent / "debug_robust")

    all_rows: List[dict] = []
    for path in video_paths:
        all_rows.extend(process_video(path, detector, predictor, args, debug_dir, svm))

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(all_rows)
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"[DONE] wrote {len(df)} rows -> {out_csv}")
    if len(df):
        print(f"[INFO] det_ok={int(df['det_ok'].sum())}/{len(df)} eye_valid={int(df.get('eye_valid', pd.Series(dtype=int)).sum())}/{len(df)}")
        if "label_name" in df.columns:
            print(df["label_name"].value_counts(dropna=False).to_string())


if __name__ == "__main__":
    main()
