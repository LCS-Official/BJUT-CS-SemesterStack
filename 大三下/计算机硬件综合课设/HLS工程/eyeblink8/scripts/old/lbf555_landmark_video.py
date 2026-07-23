#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
LBF / LBF-555-style 68-point face landmark debug video runner.

Default layout expected by this script:
  C:\Users\LC\Desktop\eyeblink8\scripts\lbf555_landmark_video.py
  C:\Users\LC\Desktop\eyeblink8\raw_selfrec\test2.mp4
  C:\Users\LC\Desktop\eyeblink8\LBF-555_debug_videos\

Notes:
- OpenCV's public lbfmodel.yaml is commonly stages=5, trees=6, depth=5, not strict 5-5-5.
- If you have a true trained LBF-555 model, put it at:
    C:\Users\LC\Desktop\eyeblink8\models\lbf_555.yaml
  or pass --model path\to\lbf_555.yaml.
- If no lbf_555.yaml exists, this script downloads/uses the common OpenCV LBF model
  as a fallback so that the pipeline can run immediately.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import re
import sys
import time
import urllib.request
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

import cv2
import numpy as np

# Common OpenCV FacemarkLBF pretrained model. The header is usually:
# stages_n: 5, tree_n: 6, tree_depth: 5, n_landmarks: 68.
DEFAULT_LBF_URL = "https://raw.githubusercontent.com/kurnianggoro/GSOC2017/master/data/lbfmodel.yaml"

Point = Tuple[int, int]
Rect = Tuple[int, int, int, int]

# 68-point landmark groups: standard iBUG/dlib/OpenCV LBF indexing.
LANDMARK_GROUPS = {
    "jaw": list(range(0, 17)),
    "right_brow": list(range(17, 22)),
    "left_brow": list(range(22, 27)),
    "nose_bridge": list(range(27, 31)),
    "nose_bottom": list(range(31, 36)),
    "right_eye": list(range(36, 42)),
    "left_eye": list(range(42, 48)),
    "outer_mouth": list(range(48, 60)),
    "inner_mouth": list(range(60, 68)),
}

CLOSED_GROUPS = {"right_eye", "left_eye", "outer_mouth", "inner_mouth"}


def project_root_from_script() -> Path:
    """Assume this file is in <project_root>/scripts/."""
    here = Path(__file__).resolve()
    if here.parent.name.lower() == "scripts":
        return here.parent.parent
    return here.parent


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def download_if_missing(url: str, dst: Path, timeout_s: int = 60) -> None:
    if dst.exists() and dst.stat().st_size > 1024 * 1024:
        return
    ensure_dir(dst.parent)
    print(f"[INFO] Downloading LBF model to: {dst}")
    print(f"[INFO] URL: {url}")
    try:
        with urllib.request.urlopen(url, timeout=timeout_s) as response:
            data = response.read()
        dst.write_bytes(data)
    except Exception as exc:
        raise RuntimeError(
            "Failed to download lbfmodel.yaml automatically.\n"
            f"Please download manually:\n  curl -L -o \"{dst}\" {url}\n"
            f"Original error: {exc}"
        ) from exc
    if dst.stat().st_size < 1024 * 1024:
        raise RuntimeError(f"Downloaded file is unexpectedly small: {dst} ({dst.stat().st_size} bytes)")


def parse_lbf_header(model_path: Path) -> dict:
    """Read only the first part of a huge YAML and extract basic LBF params."""
    text = model_path.read_text(encoding="utf-8", errors="ignore")[:4096]
    keys = ["stages_n", "tree_n", "tree_depth", "n_landmarks"]
    info = {}
    for key in keys:
        m = re.search(rf"^\s*{re.escape(key)}\s*:\s*([0-9]+)", text, flags=re.MULTILINE)
        if m:
            info[key] = int(m.group(1))
    return info


def resolve_model_path(args_model: Optional[str], root: Path) -> Path:
    models_dir = root / "models"
    true_555 = models_dir / "lbf_555.yaml"
    fallback = models_dir / "lbfmodel.yaml"

    if args_model:
        model_path = Path(args_model).expanduser().resolve()
        if not model_path.exists():
            raise FileNotFoundError(f"--model does not exist: {model_path}")
        return model_path

    if true_555.exists():
        return true_555

    download_if_missing(DEFAULT_LBF_URL, fallback)
    return fallback


def create_facemark_lbf():
    """Support both OpenCV Python factory spellings across versions."""
    if not hasattr(cv2, "face"):
        raise RuntimeError(
            "cv2.face is missing. Install opencv-contrib-python, not opencv-python only.\n"
            "Try: pip uninstall -y opencv-python opencv-contrib-python opencv-python-headless opencv-contrib-python-headless\n"
            "Then: pip install opencv-contrib-python numpy"
        )

    if hasattr(cv2.face, "createFacemarkLBF"):
        return cv2.face.createFacemarkLBF()
    if hasattr(cv2.face, "FacemarkLBF_create"):
        return cv2.face.FacemarkLBF_create()

    raise RuntimeError(
        "This OpenCV build has cv2.face, but no FacemarkLBF factory. "
        "Please install a recent opencv-contrib-python wheel."
    )


def load_face_detector(cascade_path: Optional[str] = None) -> cv2.CascadeClassifier:
    if cascade_path:
        path = Path(cascade_path).expanduser().resolve()
    else:
        # alt2 is often used by OpenCV Facemark examples; fallback to default if missing.
        alt2 = Path(cv2.data.haarcascades) / "haarcascade_frontalface_alt2.xml"
        default = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        path = alt2 if alt2.exists() else default

    detector = cv2.CascadeClassifier(str(path))
    if detector.empty():
        raise RuntimeError(f"Failed to load Haar face cascade: {path}")
    print(f"[INFO] Haar cascade: {path}")
    return detector


def largest_face(faces: Iterable[Sequence[int]]) -> Optional[Rect]:
    faces = list(faces)
    if not faces:
        return None
    x, y, w, h = max(faces, key=lambda r: int(r[2]) * int(r[3]))
    return int(x), int(y), int(w), int(h)


def clamp_rect(rect: Rect, frame_w: int, frame_h: int, pad: float = 0.08) -> Rect:
    x, y, w, h = rect
    px = int(w * pad)
    py = int(h * pad)
    x0 = max(0, x - px)
    y0 = max(0, y - py)
    x1 = min(frame_w - 1, x + w + px)
    y1 = min(frame_h - 1, y + h + py)
    return x0, y0, max(1, x1 - x0), max(1, y1 - y0)


def rect_from_landmarks(points: np.ndarray, frame_w: int, frame_h: int) -> Rect:
    xs = points[:, 0]
    ys = points[:, 1]
    x0 = int(np.min(xs))
    y0 = int(np.min(ys))
    x1 = int(np.max(xs))
    y1 = int(np.max(ys))
    return clamp_rect((x0, y0, x1 - x0, y1 - y0), frame_w, frame_h, pad=0.20)


def normalize_landmarks(raw_landmarks) -> np.ndarray:
    """Convert OpenCV facemark output for one face to shape (68, 2), float32."""
    arr = np.asarray(raw_landmarks, dtype=np.float32)
    arr = arr.reshape(-1, 2)
    return arr


def dist(p1: np.ndarray, p2: np.ndarray) -> float:
    return float(np.linalg.norm(p1 - p2))


def eye_aspect_ratio(eye: np.ndarray) -> float:
    # eye points should be 6x2: [p1, p2, p3, p4, p5, p6]
    # EAR = (||p2-p6|| + ||p3-p5||) / (2*||p1-p4||)
    denom = 2.0 * dist(eye[0], eye[3])
    if denom <= 1e-6:
        return 0.0
    return (dist(eye[1], eye[5]) + dist(eye[2], eye[4])) / denom


def compute_ear(points: np.ndarray) -> Tuple[float, float, float]:
    right_eye = points[36:42]
    left_eye = points[42:48]
    ear_r = eye_aspect_ratio(right_eye)
    ear_l = eye_aspect_ratio(left_eye)
    return ear_r, ear_l, (ear_r + ear_l) / 2.0


def draw_polyline(frame: np.ndarray, pts: np.ndarray, indices: List[int], closed: bool, color: Tuple[int, int, int], thickness: int) -> None:
    poly = np.round(pts[indices]).astype(np.int32).reshape(-1, 1, 2)
    cv2.polylines(frame, [poly], closed, color, thickness, lineType=cv2.LINE_AA)


def draw_landmarks(frame: np.ndarray, pts: np.ndarray, show_indices: bool = False) -> None:
    # BGR colors chosen for readability on debug videos.
    colors = {
        "jaw": (160, 160, 160),
        "right_brow": (255, 180, 0),
        "left_brow": (255, 180, 0),
        "nose_bridge": (0, 220, 255),
        "nose_bottom": (0, 220, 255),
        "right_eye": (0, 255, 0),
        "left_eye": (0, 255, 0),
        "outer_mouth": (0, 0, 255),
        "inner_mouth": (0, 0, 200),
    }
    for name, idx in LANDMARK_GROUPS.items():
        draw_polyline(frame, pts, idx, name in CLOSED_GROUPS, colors[name], 1)

    for i, (x, y) in enumerate(np.round(pts).astype(np.int32)):
        cv2.circle(frame, (int(x), int(y)), 2, (255, 255, 255), -1, lineType=cv2.LINE_AA)
        if show_indices:
            cv2.putText(frame, str(i), (int(x) + 2, int(y) - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.28, (255, 255, 255), 1, cv2.LINE_AA)


def put_label(frame: np.ndarray, text: str, org: Point, color: Tuple[int, int, int] = (255, 255, 255), scale: float = 0.55) -> None:
    x, y = org
    cv2.putText(frame, text, (x + 1, y + 1), cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, 1, cv2.LINE_AA)


def prepare_output_writer(input_path: Path, out_dir: Path, fps: float, width: int, height: int, suffix: str = "_lbf555_debug"):
    ensure_dir(out_dir)
    stem = input_path.stem
    out_path = out_dir / f"{stem}{suffix}.mp4"

    # mp4v is broadly supported by OpenCV wheels on Windows.
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))
    if not writer.isOpened():
        # Fallback to AVI/XVID if mp4 writer is unavailable.
        out_path = out_dir / f"{stem}{suffix}.avi"
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        writer = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))
    if not writer.isOpened():
        raise RuntimeError(f"Could not create output video writer in: {out_dir}")
    return writer, out_path


def write_csv_header(csv_writer: csv.writer) -> None:
    header = ["frame", "time_sec", "face_x", "face_y", "face_w", "face_h", "ear_right", "ear_left", "ear_avg", "blink"]
    for i in range(68):
        header += [f"x{i}", f"y{i}"]
    csv_writer.writerow(header)


def write_csv_row(csv_writer: csv.writer, frame_idx: int, time_sec: float, face: Optional[Rect], pts: Optional[np.ndarray], ear: Tuple[float, float, float], blink: bool) -> None:
    if face is None:
        face_vals = ["", "", "", ""]
    else:
        face_vals = list(face)
    row = [frame_idx, f"{time_sec:.4f}", *face_vals, f"{ear[0]:.6f}", f"{ear[1]:.6f}", f"{ear[2]:.6f}", int(blink)]
    if pts is None:
        row += [""] * (68 * 2)
    else:
        for x, y in pts:
            row += [f"{float(x):.3f}", f"{float(y):.3f}"]
    csv_writer.writerow(row)


def run(args: argparse.Namespace) -> None:
    root = project_root_from_script()

    video_path = Path(args.video).expanduser().resolve() if args.video else (root / "raw_selfrec" / "WIN_20260414_21_29_13_Pro.mp4")
    out_dir = Path(args.out_dir).expanduser().resolve() if args.out_dir else (root / "LBF-555_debug_videos")
    model_path = resolve_model_path(args.model, root)

    if not video_path.exists():
        raise FileNotFoundError(f"Input video not found: {video_path}")

    header = parse_lbf_header(model_path)
    print(f"[INFO] LBF model: {model_path}")
    if header:
        print(f"[INFO] Model header: {header}")
        if (header.get("stages_n"), header.get("tree_n"), header.get("tree_depth")) != (5, 5, 5):
            print("[WARN] This model is not strict LBF-555. It will still run as an LBF 68-point model.")
    else:
        print("[WARN] Could not parse LBF model header; continuing.")

    face_detector = load_face_detector(args.cascade)
    facemark = create_facemark_lbf()
    print("[INFO] Loading facemark model; this may take a few seconds...")
    facemark.loadModel(str(model_path))

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    if not math.isfinite(fps) or fps <= 1e-3:
        fps = args.fallback_fps
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    writer, out_video = prepare_output_writer(video_path, out_dir, fps, width, height)
    csv_file = None
    csv_writer = None
    csv_path = None
    if args.save_csv:
        csv_path = out_dir / f"{video_path.stem}_lbf555_landmarks.csv"
        csv_file = csv_path.open("w", newline="", encoding="utf-8")
        csv_writer = csv.writer(csv_file)
        write_csv_header(csv_writer)

    print(f"[INFO] Input : {video_path}")
    print(f"[INFO] Output: {out_video}")
    if csv_path:
        print(f"[INFO] CSV   : {csv_path}")
    print(f"[INFO] Video : {width}x{height}, fps={fps:.3f}, frames={total_frames}")

    last_face: Optional[Rect] = None
    last_success_frame = -10_000
    blink_frames = 0
    blink_count = 0
    prev_blink_state = False
    frame_idx = 0
    t0 = time.perf_counter()

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        do_detect = (
            last_face is None
            or frame_idx % max(1, args.detect_every) == 0
            or (frame_idx - last_success_frame) > args.redetect_after
        )

        face: Optional[Rect] = None
        faces_for_fit: List[Rect] = []

        if do_detect:
            faces = face_detector.detectMultiScale(
                gray,
                scaleFactor=args.det_scale,
                minNeighbors=args.det_neighbors,
                minSize=(args.min_face, args.min_face),
                flags=cv2.CASCADE_SCALE_IMAGE,
            )
            if args.all_faces:
                faces_for_fit = [tuple(map(int, f)) for f in faces]
                face = largest_face(faces_for_fit)
            else:
                face = largest_face(faces)
                faces_for_fit = [face] if face else []
        elif last_face is not None:
            face = last_face
            faces_for_fit = [last_face]

        pts: Optional[np.ndarray] = None
        ear = (0.0, 0.0, 0.0)
        blink_now = False

        if faces_for_fit:
            np_faces = np.array(faces_for_fit, dtype=np.int32)
            fit_ok, landmarks = facemark.fit(frame, np_faces)
            if fit_ok and landmarks is not None and len(landmarks) > 0:
                # For self-recording, use the largest/current first face in single-face mode.
                pts = normalize_landmarks(landmarks[0])
                if pts.shape[0] >= 68:
                    pts = pts[:68]
                    ear = compute_ear(pts)
                    blink_now = ear[2] < args.ear_thresh

                    if blink_now:
                        blink_frames += 1
                    else:
                        if prev_blink_state and blink_frames >= args.blink_consec:
                            blink_count += 1
                        blink_frames = 0
                    prev_blink_state = blink_now

                    last_face = rect_from_landmarks(pts, width, height)
                    last_success_frame = frame_idx
                else:
                    pts = None

        # Draw overlays.
        if last_face is not None:
            x, y, w, h = last_face
            cv2.rectangle(frame, (x, y), (x + w, y + h), (60, 180, 255), 2, lineType=cv2.LINE_AA)

        if pts is not None:
            draw_landmarks(frame, pts, show_indices=args.show_indices)
            # Highlight eyes used for EAR.
            for idx in list(range(36, 42)) + list(range(42, 48)):
                x, y = np.round(pts[idx]).astype(int)
                cv2.circle(frame, (int(x), int(y)), 3, (0, 255, 255), -1, lineType=cv2.LINE_AA)

        status_color = (0, 0, 255) if blink_now else (0, 255, 0)
        put_label(frame, f"frame={frame_idx}/{total_frames if total_frames > 0 else '?'}", (12, 24))
        put_label(frame, f"LBF model: {model_path.name}", (12, 48))
        put_label(frame, f"EAR R/L/avg: {ear[0]:.3f}/{ear[1]:.3f}/{ear[2]:.3f}", (12, 72))
        put_label(frame, f"blink_now={int(blink_now)}  blink_count={blink_count}", (12, 96), color=status_color)
        put_label(frame, f"detect_every={args.detect_every}  face={'yes' if pts is not None else 'no'}", (12, 120))

        writer.write(frame)

        if csv_writer is not None:
            write_csv_row(csv_writer, frame_idx, frame_idx / fps, last_face, pts, ear, blink_now)

        frame_idx += 1
        if args.max_frames > 0 and frame_idx >= args.max_frames:
            break

        if args.preview:
            cv2.imshow("LBF-555 debug", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord("q"):
                break

        if frame_idx % 100 == 0:
            elapsed = time.perf_counter() - t0
            proc_fps = frame_idx / max(elapsed, 1e-6)
            print(f"[INFO] processed {frame_idx} frames, speed={proc_fps:.2f} FPS")

    # Count a blink if video ends while in blink state.
    if prev_blink_state and blink_frames >= args.blink_consec:
        blink_count += 1

    cap.release()
    writer.release()
    if csv_file is not None:
        csv_file.close()
    if args.preview:
        cv2.destroyAllWindows()

    elapsed = time.perf_counter() - t0
    print("[DONE]")
    print(f"[DONE] Frames processed: {frame_idx}")
    print(f"[DONE] Average speed   : {frame_idx / max(elapsed, 1e-6):.2f} FPS")
    print(f"[DONE] Blink count     : {blink_count}")
    print(f"[DONE] Debug video     : {out_video}")
    if csv_path:
        print(f"[DONE] Landmarks CSV   : {csv_path}")


def build_arg_parser() -> argparse.ArgumentParser:
    root = project_root_from_script()
    parser = argparse.ArgumentParser(description="Run OpenCV FacemarkLBF 68-point landmarks on a video and save debug output.")
    parser.add_argument("--video", default=str(root / "raw_selfrec" / "WIN_20260414_21_29_13_Pro.mp4"), help="Input video path.")
    parser.add_argument("--out_dir", default=str(root / "LBF-555_debug_videos"), help="Output directory for debug video/CSV.")
    parser.add_argument("--model", default=None, help="Path to lbf_555.yaml or another LBF model. Defaults to models/lbf_555.yaml, then fallback models/lbfmodel.yaml.")
    parser.add_argument("--cascade", default=None, help="Optional Haar cascade XML path. Defaults to cv2.data.haarcascades alt2/default.")
    parser.add_argument("--detect_every", type=int, default=3, help="Run Haar detection every N frames; reuse last landmark-derived box between detections.")
    parser.add_argument("--redetect_after", type=int, default=12, help="Force face redetection if facemark has failed for this many frames.")
    parser.add_argument("--det_scale", type=float, default=1.12, help="Haar detectMultiScale scaleFactor.")
    parser.add_argument("--det_neighbors", type=int, default=5, help="Haar detectMultiScale minNeighbors.")
    parser.add_argument("--min_face", type=int, default=60, help="Minimum face size in pixels.")
    parser.add_argument("--ear_thresh", type=float, default=0.21, help="Blink threshold for average Eye Aspect Ratio.")
    parser.add_argument("--blink_consec", type=int, default=2, help="Minimum consecutive low-EAR frames counted as a blink.")
    parser.add_argument("--fallback_fps", type=float, default=25.0, help="FPS used if the input video reports 0/NaN.")
    parser.add_argument("--max_frames", type=int, default=-1, help="For quick testing; <=0 means process all frames.")
    parser.add_argument("--preview", action="store_true", help="Show a live preview window; press q/ESC to stop.")
    parser.add_argument("--show_indices", action="store_true", help="Draw landmark indices 0..67 on the debug video.")
    parser.add_argument("--save_csv", action="store_true", help="Save per-frame landmark coordinates and EAR to CSV.")
    parser.add_argument("--all_faces", action="store_true", help="Fit all detected faces; debug CSV/video still tracks the first fitted face.")
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()
    try:
        run(args)
        return 0
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
