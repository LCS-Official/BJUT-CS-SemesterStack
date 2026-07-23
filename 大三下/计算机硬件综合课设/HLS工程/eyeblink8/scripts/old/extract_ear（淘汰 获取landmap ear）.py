from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

import cv2
import numpy as np


# 默认按常见 68 点顺序取双眼关键点。
# 如果你的模型顺序不同，可以在命令行里改。
DEFAULT_LEFT_EYE = [36, 37, 38, 39, 40, 41]
DEFAULT_RIGHT_EYE = [42, 43, 44, 45, 46, 47]


def parse_int_list(s: str) -> List[int]:
    return [int(x.strip()) for x in s.split(",") if x.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract frame-level EAR from Eyeblink8 videos using LBP + FacemarkKazemi."
    )
    parser.add_argument("--raw_dir", type=str, default="raw", help="Folder containing *.avi")
    parser.add_argument("--out_dir", type=str, default="work", help="Output folder")
    parser.add_argument(
        "--face_cascade",
        type=str,
        required=True,
        help="Path to LBP face cascade xml, e.g. lbpcascade_frontalface.xml",
    )
    parser.add_argument(
        "--facemark_model",
        type=str,
        required=True,
        help="Path to facemark Kazemi model file",
    )
    parser.add_argument(
        "--video_ids",
        type=str,
        default="",
        help="Optional comma-separated video ids, e.g. 1,2,A . Empty means all avi files",
    )
    parser.add_argument(
        "--left_eye_idx",
        type=str,
        default="36,37,38,39,40,41",
        help="Comma-separated landmark indices for left eye",
    )
    parser.add_argument(
        "--right_eye_idx",
        type=str,
        default="42,43,44,45,46,47",
        help="Comma-separated landmark indices for right eye",
    )
    parser.add_argument(
        "--scale_factor",
        type=float,
        default=1.1,
        help="detectMultiScale scaleFactor",
    )
    parser.add_argument(
        "--min_neighbors",
        type=int,
        default=5,
        help="detectMultiScale minNeighbors",
    )
    parser.add_argument(
        "--min_face",
        type=int,
        default=80,
        help="Minimum face size in pixels for detectMultiScale",
    )
    parser.add_argument(
        "--max_frames",
        type=int,
        default=-1,
        help="Only process first N frames for quick debug; -1 means all",
    )
    parser.add_argument(
        "--save_debug_video",
        action="store_true",
        help="If set, save simple visualization video under work/debug_videos/",
    )
    return parser.parse_args()


def ensure_cv_face_available() -> None:
    if not hasattr(cv2, "face"):
        raise RuntimeError(
            "Your cv2 does not have cv2.face. Please use an OpenCV build that includes the face module."
        )
    if not hasattr(cv2.face, "createFacemarkKazemi"):
        raise RuntimeError(
            "Your cv2.face does not provide createFacemarkKazemi()."
        )


def collect_video_ids(raw_dir: Path, video_ids_arg: str) -> List[str]:
    if video_ids_arg.strip():
        return [x.strip() for x in video_ids_arg.split(",") if x.strip()]
    return sorted([p.stem for p in raw_dir.glob("*.avi")], key=lambda x: str(x))


def dist(p1: np.ndarray, p2: np.ndarray) -> float:
    return float(np.linalg.norm(p1 - p2))


def compute_ear_from_eye_points(eye_pts: np.ndarray) -> Optional[float]:
    """
    eye_pts shape: (6, 2)
    EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
    """
    if eye_pts.shape != (6, 2):
        return None

    p1, p2, p3, p4, p5, p6 = eye_pts

    a = dist(p2, p6)
    b = dist(p3, p5)
    c = dist(p1, p4)

    if c <= 1e-6:
        return None

    ear = (a + b) / (2.0 * c)
    if math.isnan(ear) or math.isinf(ear):
        return None
    return float(ear)


def choose_best_face(faces: Sequence[Tuple[int, int, int, int]]) -> Optional[Tuple[int, int, int, int]]:
    if not faces:
        return None
    # 选面积最大的脸，先追求稳定。
    return max(faces, key=lambda r: int(r[2]) * int(r[3]))


def rect_to_tuple(rect) -> Tuple[int, int, int, int]:
    # 有的版本 detectMultiScale 返回 ndarray
    x, y, w, h = rect
    return int(x), int(y), int(w), int(h)


def draw_debug(
    frame: np.ndarray,
    face: Optional[Tuple[int, int, int, int]],
    landmarks: Optional[np.ndarray],
    ear_l: Optional[float],
    ear_r: Optional[float],
    ear_avg: Optional[float],
    det_ok: int,
    frame_id: int,
) -> np.ndarray:
    vis = frame.copy()

    if face is not None:
        x, y, w, h = face
        cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 255, 0), 2)

    if landmarks is not None:
        pts = np.asarray(landmarks, dtype=np.float32).reshape(-1, 2).astype(int)
        for px, py in pts:
            cv2.circle(vis, (px, py), 1, (0, 0, 255), -1)

    text1 = f"frame={frame_id} det_ok={det_ok}"
    text2 = f"EAR_L={ear_l if ear_l is not None else -1:.4f}  EAR_R={ear_r if ear_r is not None else -1:.4f}"
    text3 = f"EAR_AVG={ear_avg if ear_avg is not None else -1:.4f}"

    cv2.putText(vis, text1, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
    cv2.putText(vis, text2, (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    cv2.putText(vis, text3, (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    return vis


def write_csv(rows: List[dict], out_path: Path) -> None:
    if not rows:
        print(f"[WARN] No rows to write: {out_path}")
        return
    with out_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    ensure_cv_face_available()

    raw_dir = Path(args.raw_dir)
    out_dir = Path(args.out_dir)
    per_video_dir = out_dir / "per_video_ear"
    debug_dir = out_dir / "debug_videos"

    out_dir.mkdir(parents=True, exist_ok=True)
    per_video_dir.mkdir(parents=True, exist_ok=True)
    if args.save_debug_video:
        debug_dir.mkdir(parents=True, exist_ok=True)

    face_cascade_path = Path(args.face_cascade)
    facemark_model_path = Path(args.facemark_model)

    if not face_cascade_path.exists():
        raise FileNotFoundError(f"Face cascade not found: {face_cascade_path}")
    if not facemark_model_path.exists():
        raise FileNotFoundError(f"Facemark model not found: {facemark_model_path}")

    face_detector = cv2.CascadeClassifier(str(face_cascade_path))
    if face_detector.empty():
        raise RuntimeError(f"Failed to load cascade: {face_cascade_path}")

    facemark = cv2.face.createFacemarkKazemi()
    facemark.loadModel(str(facemark_model_path))

    left_eye_idx = parse_int_list(args.left_eye_idx)
    right_eye_idx = parse_int_list(args.right_eye_idx)

    if len(left_eye_idx) != 6 or len(right_eye_idx) != 6:
        raise ValueError("left_eye_idx and right_eye_idx must each contain exactly 6 indices.")

    video_ids = collect_video_ids(raw_dir, args.video_ids)
    if not video_ids:
        raise FileNotFoundError(f"No .avi files found in {raw_dir.resolve()}")

    all_rows: List[dict] = []

    print(f"[INFO] video_ids = {video_ids}")

    for video_id in video_ids:
        video_path = raw_dir / f"{video_id}.avi"
        if not video_path.exists():
            print(f"[WARN] Missing video: {video_path}")
            continue

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            print(f"[WARN] Failed to open video: {video_path}")
            continue

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        print(
            f"[INFO] Processing {video_id}: "
            f"fps={fps:.3f}, total_frames={total_frames}, size=({width}x{height})"
        )

        writer = None
        if args.save_debug_video:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            debug_path = debug_dir / f"{video_id}_debug.mp4"
            writer = cv2.VideoWriter(str(debug_path), fourcc, max(fps, 1.0), (width, height))

        rows: List[dict] = []
        frame_id = 0

        while True:
            ok, frame = cap.read()
            if not ok:
                break

            if args.max_frames > 0 and frame_id >= args.max_frames:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            faces = face_detector.detectMultiScale(
                gray,
                scaleFactor=args.scale_factor,
                minNeighbors=args.min_neighbors,
                minSize=(args.min_face, args.min_face),
            )

            face_count = 0 if faces is None else len(faces)
            best_face = None
            landmarks = None
            ear_l = None
            ear_r = None
            ear_avg = None
            det_ok = 0

            if face_count > 0:
                face_list = [rect_to_tuple(f) for f in faces]
                best_face = choose_best_face(face_list)

                if best_face is not None:
                    x, y, w, h = best_face
                    fit_ok, landmarks_out = facemark.fit(
                        gray, np.array([[x, y, w, h]], dtype=np.int32)
                    )
                    print(f"[DEBUG] frame={frame_id}, landmarks raw shape={np.asarray(landmarks_out[0]).shape}")

                    if fit_ok and len(landmarks_out) > 0:
                        landmarks = np.asarray(landmarks_out[0], dtype=np.float32)
                        landmarks = landmarks.reshape(-1, 2)

                        max_idx = max(max(left_eye_idx), max(right_eye_idx))
                        if landmarks.shape[0] > max_idx:
                            left_eye_pts = landmarks[left_eye_idx]
                            right_eye_pts = landmarks[right_eye_idx]

                            ear_l = compute_ear_from_eye_points(left_eye_pts)
                            ear_r = compute_ear_from_eye_points(right_eye_pts)

                            if ear_l is not None and ear_r is not None:
                                ear_avg = float((ear_l + ear_r) / 2.0)
                                det_ok = 1

            row = {
                "video_id": video_id,
                "frame_id": frame_id,
                "ear_l": "" if ear_l is None else f"{ear_l:.8f}",
                "ear_r": "" if ear_r is None else f"{ear_r:.8f}",
                "ear_avg": "" if ear_avg is None else f"{ear_avg:.8f}",
                "det_ok": det_ok,
                "face_count": face_count,
                "face_x": "" if best_face is None else best_face[0],
                "face_y": "" if best_face is None else best_face[1],
                "face_w": "" if best_face is None else best_face[2],
                "face_h": "" if best_face is None else best_face[3],
            }
            rows.append(row)
            all_rows.append(row)

            if writer is not None:
                dbg = draw_debug(frame, best_face, landmarks, ear_l, ear_r, ear_avg, det_ok, frame_id)
                writer.write(dbg)

            frame_id += 1

        cap.release()
        if writer is not None:
            writer.release()

        per_video_out = per_video_dir / f"{video_id}_ear.csv"
        write_csv(rows, per_video_out)

        ok_count = sum(int(r["det_ok"]) for r in rows)
        ratio = (ok_count / len(rows)) if rows else 0.0
        print(
            f"[OK] {video_id}: rows={len(rows)}, det_ok={ok_count}, "
            f"success_ratio={ratio:.4f}"
        )

    merged_out = out_dir / "frame_ear.csv"
    write_csv(all_rows, merged_out)

    print(f"\n[DONE] Wrote merged EAR CSV: {merged_out.resolve()}")
    print(f"[DONE] Wrote per-video EAR CSVs: {per_video_dir.resolve()}")
    if args.save_debug_video:
        print(f"[DONE] Wrote debug videos: {debug_dir.resolve()}")


if __name__ == "__main__":
    main()