from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import dlib
import numpy as np
from tqdm import tqdm


LEFT_EYE_IDX = [36, 37, 38, 39, 40, 41]
RIGHT_EYE_IDX = [42, 43, 44, 45, 46, 47]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract frame-level EAR from Eyeblink8 videos using dlib 68 landmarks."
    )
    parser.add_argument("--raw_dir", type=str, default="raw")
    parser.add_argument("--out_dir", type=str, default="work")
    parser.add_argument(
        "--shape_predictor",
        type=str,
        required=True,
        help="Path to dlib shape_predictor_68_face_landmarks.dat",
    )
    parser.add_argument(
        "--video_ids",
        type=str,
        default="",
        help="Optional comma-separated ids, e.g. 1,2,A",
    )
    parser.add_argument(
        "--max_frames",
        type=int,
        default=-1,
        help="Only process first N frames; -1 means all",
    )
    parser.add_argument(
        "--start_frame",
        type=int,
        default=0,
        help="Start from this frame index",
    )
    parser.add_argument(
        "--save_debug_video",
        action="store_true",
        help="Save debug video",
    )
    parser.add_argument(
        "--debug_eye_only",
        action="store_true",
        help="Only draw eye landmarks in debug video",
    )
    parser.add_argument(
        "--no_progress",
        action="store_true",
        help="Disable tqdm progress bar",
    )
    return parser.parse_args()


def collect_video_ids(raw_dir: Path, video_ids_arg: str) -> List[str]:
    if video_ids_arg.strip():
        return [x.strip() for x in video_ids_arg.split(",") if x.strip()]
    return sorted([p.stem for p in raw_dir.glob("*.avi")], key=lambda x: str(x))


def shape_to_np(shape: dlib.full_object_detection) -> np.ndarray:
    coords = np.zeros((68, 2), dtype=np.float32)
    for i in range(68):
        coords[i] = (shape.part(i).x, shape.part(i).y)
    return coords


def dist(p1: np.ndarray, p2: np.ndarray) -> float:
    return float(np.linalg.norm(p1 - p2))


def compute_ear_from_eye_points(eye_pts: np.ndarray) -> Optional[float]:
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


def choose_best_face(rects: List[dlib.rectangle]) -> Optional[dlib.rectangle]:
    if not rects:
        return None
    return max(rects, key=lambda r: r.width() * r.height())


def rect_to_xywh(rect: dlib.rectangle) -> Tuple[int, int, int, int]:
    x = int(rect.left())
    y = int(rect.top())
    w = int(rect.width())
    h = int(rect.height())
    return x, y, w, h


def draw_debug(
    frame: np.ndarray,
    face_rect: Optional[dlib.rectangle],
    landmarks: Optional[np.ndarray],
    ear_l: Optional[float],
    ear_r: Optional[float],
    ear_avg: Optional[float],
    det_ok: int,
    frame_id: int,
    debug_eye_only: bool,
) -> np.ndarray:
    vis = frame.copy()

    if face_rect is not None:
        x, y, w, h = rect_to_xywh(face_rect)
        cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 255, 0), 2)

    if landmarks is not None:
        if debug_eye_only:
            draw_idx = LEFT_EYE_IDX + RIGHT_EYE_IDX
        else:
            draw_idx = list(range(68))

        pts = landmarks.astype(int)
        for i in draw_idx:
            px, py = pts[i]
            cv2.circle(vis, (px, py), 2, (0, 0, 255), -1)
            cv2.putText(
                vis,
                str(i),
                (px + 2, py - 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.35,
                (255, 255, 0),
                1,
            )

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

    raw_dir = Path(args.raw_dir)
    out_dir = Path(args.out_dir)
    per_video_dir = out_dir / "per_video_ear"
    debug_dir = out_dir / "debug_videos"

    out_dir.mkdir(parents=True, exist_ok=True)
    per_video_dir.mkdir(parents=True, exist_ok=True)
    if args.save_debug_video:
        debug_dir.mkdir(parents=True, exist_ok=True)

    predictor_path = Path(args.shape_predictor)
    if not predictor_path.exists():
        raise FileNotFoundError(f"shape predictor not found: {predictor_path}")

    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(str(predictor_path))

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

        if args.start_frame > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, args.start_frame)

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
            debug_path = debug_dir / f"{video_id}_dlib_debug.mp4"
            writer = cv2.VideoWriter(str(debug_path), fourcc, max(fps, 1.0), (width, height))

        rows: List[dict] = []
        frame_id = args.start_frame
        processed_count = 0
        if args.max_frames > 0:
            target_total = min(args.max_frames, max(0, total_frames - args.start_frame))
        else:
            target_total = max(0, total_frames - args.start_frame)

        pbar = None
        if not args.no_progress:
            pbar = tqdm(
                total=target_total,
                desc=f"video {video_id}",
                unit="frame",
                ncols=100,
            )

        det_ok_count_running = 0

        while True:
            ok, frame = cap.read()
            if not ok:
                break

            if args.max_frames > 0 and processed_count >= args.max_frames:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            rects = detector(gray, 0)
            face_count = len(rects)

            best_face = choose_best_face(list(rects))
            landmarks = None
            ear_l = None
            ear_r = None
            ear_avg = None
            det_ok = 0

            if best_face is not None:
                shape = predictor(gray, best_face)
                landmarks = shape_to_np(shape)

                left_eye_pts = landmarks[LEFT_EYE_IDX]
                right_eye_pts = landmarks[RIGHT_EYE_IDX]

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
                "face_x": "" if best_face is None else best_face.left(),
                "face_y": "" if best_face is None else best_face.top(),
                "face_w": "" if best_face is None else best_face.width(),
                "face_h": "" if best_face is None else best_face.height(),
            }
            rows.append(row)
            all_rows.append(row)

            if writer is not None:
                dbg = draw_debug(
                    frame=frame,
                    face_rect=best_face,
                    landmarks=landmarks,
                    ear_l=ear_l,
                    ear_r=ear_r,
                    ear_avg=ear_avg,
                    det_ok=det_ok,
                    frame_id=frame_id,
                    debug_eye_only=args.debug_eye_only,
                )
                writer.write(dbg)

            processed_count += 1
            if det_ok == 1:
                det_ok_count_running += 1

            if pbar is not None:
                current_ratio = det_ok_count_running / processed_count if processed_count > 0 else 0.0
                pbar.update(1)
                pbar.set_postfix({
                    "det_ok": det_ok_count_running,
                    "rate": f"{current_ratio:.3f}"
                })

            frame_id += 1

        cap.release()
        if writer is not None:
            writer.release()
        if pbar is not None:
            pbar.close()

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