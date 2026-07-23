from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import dlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm


LEFT_EYE_IDX = [36, 37, 38, 39, 40, 41]
RIGHT_EYE_IDX = [42, 43, 44, 45, 46, 47]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch extract frame-level EAR from self-recorded videos for later manual closed labeling."
    )
    parser.add_argument("--raw_dir", type=str, default="raw_selfrec", help="Folder containing self-recorded videos")
    parser.add_argument("--out_dir", type=str, default="work_selfrec", help="Output folder")
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
        help="Optional comma-separated stems, e.g. 1,2,testA ; empty means all videos in raw_dir",
    )
    parser.add_argument(
        "--exts",
        type=str,
        default=".mp4,.avi,.mov,.mkv",
        help="Comma-separated video extensions to scan",
    )
    parser.add_argument("--start_frame", type=int, default=0, help="Start from this frame index")
    parser.add_argument("--max_frames", type=int, default=-1, help="Only process first N frames after start; -1 means all")
    parser.add_argument("--upsample", type=int, default=0, help="dlib face detector upsample times, usually 0 or 1")
    parser.add_argument("--smooth_window", type=int, default=5, help="Rolling window size for ear_smooth")
    parser.add_argument("--plot_dpi", type=int, default=150, help="DPI for EAR plots")
    parser.add_argument("--save_debug_video", action="store_true", help="Save debug video with face box and eye landmarks")
    parser.add_argument("--debug_eye_only", action="store_true", help="Only draw eye landmarks in debug video")
    parser.add_argument("--no_progress", action="store_true", help="Disable tqdm progress bar")
    return parser.parse_args()


def parse_list_arg(s: str) -> List[str]:
    return [x.strip() for x in s.split(",") if x.strip()]


def collect_video_paths(raw_dir: Path, exts_arg: str, video_ids_arg: str) -> List[Path]:
    exts = {e.lower().strip() for e in exts_arg.split(",") if e.strip()}
    all_paths: List[Path] = []
    for p in raw_dir.iterdir():
        if p.is_file() and p.suffix.lower() in exts:
            all_paths.append(p)

    all_paths = sorted(all_paths, key=lambda p: p.stem)

    if video_ids_arg.strip():
        wanted = set(parse_list_arg(video_ids_arg))
        all_paths = [p for p in all_paths if p.stem in wanted]

    return all_paths


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
        draw_idx = LEFT_EYE_IDX + RIGHT_EYE_IDX if debug_eye_only else list(range(68))
        pts = landmarks.astype(int)
        for i in draw_idx:
            px, py = pts[i]
            cv2.circle(vis, (px, py), 2, (0, 0, 255), -1)

    text1 = f"frame={frame_id} det_ok={det_ok}"
    text2 = f"EAR_L={ear_l if ear_l is not None else -1:.4f}  EAR_R={ear_r if ear_r is not None else -1:.4f}"
    text3 = f"EAR_AVG={ear_avg if ear_avg is not None else -1:.4f}"

    cv2.putText(vis, text1, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
    cv2.putText(vis, text2, (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    cv2.putText(vis, text3, (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

    return vis


def save_ear_plot(df: pd.DataFrame, out_path: Path, video_id: str, fps: float, dpi: int) -> None:
    valid = df["det_ok"] == 1

    plt.figure(figsize=(14, 4))
    plt.plot(df["frame_id"], df["ear_avg"], linewidth=0.8, alpha=0.7, label="ear_avg")
    plt.plot(df["frame_id"], df["ear_smooth"], linewidth=1.5, label="ear_smooth")

    if (~valid).any():
        bad_x = df.loc[~valid, "frame_id"]
        bad_y = np.full(len(bad_x), np.nanmin(df["ear_smooth"].fillna(0).to_numpy()) if valid.any() else 0.0)
        plt.scatter(bad_x, bad_y, s=5, label="det_fail")

    plt.title(f"{video_id} | fps={fps:.2f}")
    plt.xlabel("frame_id")
    plt.ylabel("EAR")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=dpi)
    plt.close()


def main() -> None:
    args = parse_args()

    raw_dir = Path(args.raw_dir)
    out_dir = Path(args.out_dir)
    per_video_ear_dir = out_dir / "per_video_ear"
    labelview_dir = out_dir / "per_video_labelview"
    plots_dir = out_dir / "ear_plots"
    debug_dir = out_dir / "debug_videos"

    for d in [out_dir, per_video_ear_dir, labelview_dir, plots_dir]:
        d.mkdir(parents=True, exist_ok=True)
    if args.save_debug_video:
        debug_dir.mkdir(parents=True, exist_ok=True)

    predictor_path = Path(args.shape_predictor)
    if not predictor_path.exists():
        raise FileNotFoundError(f"shape predictor not found: {predictor_path}")
    if not raw_dir.exists():
        raise FileNotFoundError(f"raw_dir not found: {raw_dir}")

    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(str(predictor_path))

    video_paths = collect_video_paths(raw_dir, args.exts, args.video_ids)
    if not video_paths:
        raise FileNotFoundError(f"No video files found in: {raw_dir.resolve()}")

    print("[INFO] videos:")
    for p in video_paths:
        print("  ", p.name)

    all_rows: List[dict] = []
    summary_rows: List[dict] = []

    for video_path in video_paths:
        video_id = video_path.stem

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            print(f"[WARN] Failed to open: {video_path}")
            continue

        if args.start_frame > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, args.start_frame)

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30.0

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        print(f"\n[INFO] Processing {video_id}: fps={fps:.3f}, total_frames={total_frames}, size=({width}x{height})")

        writer = None
        if args.save_debug_video:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            debug_path = debug_dir / f"{video_id}_debug.mp4"
            writer = cv2.VideoWriter(str(debug_path), fourcc, max(fps, 1.0), (width, height))

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

        frame_rows: List[dict] = []
        frame_id = args.start_frame
        processed_count = 0
        det_ok_count = 0

        while True:
            ok, frame = cap.read()
            if not ok:
                break

            if args.max_frames > 0 and processed_count >= args.max_frames:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            rects = detector(gray, args.upsample)
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

            timestamp_sec = frame_id / fps

            row = {
                "video_id": video_id,
                "frame_id": frame_id,
                "timestamp_sec": float(timestamp_sec),
                "ear_l": np.nan if ear_l is None else float(ear_l),
                "ear_r": np.nan if ear_r is None else float(ear_r),
                "ear_avg": np.nan if ear_avg is None else float(ear_avg),
                "det_ok": int(det_ok),
                "face_count": int(face_count),
                "face_x": np.nan if best_face is None else int(best_face.left()),
                "face_y": np.nan if best_face is None else int(best_face.top()),
                "face_w": np.nan if best_face is None else int(best_face.width()),
                "face_h": np.nan if best_face is None else int(best_face.height()),
            }
            frame_rows.append(row)
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
                det_ok_count += 1

            if pbar is not None:
                ratio = det_ok_count / processed_count if processed_count > 0 else 0.0
                pbar.update(1)
                pbar.set_postfix({
                    "det_ok": det_ok_count,
                    "rate": f"{ratio:.3f}"
                })

            frame_id += 1

        cap.release()
        if writer is not None:
            writer.release()
        if pbar is not None:
            pbar.close()

        if not frame_rows:
            print(f"[WARN] No frames extracted from {video_id}")
            continue

        df = pd.DataFrame(frame_rows)
        df["ear_smooth"] = (
            df["ear_avg"]
            .interpolate(limit_direction="both")
            .rolling(window=max(1, args.smooth_window), center=True, min_periods=1)
            .mean()
        )

        per_video_ear_path = per_video_ear_dir / f"{video_id}_ear.csv"
        df.to_csv(per_video_ear_path, index=False, encoding="utf-8-sig")

        labelview_df = df[["video_id", "frame_id", "timestamp_sec", "ear_avg", "ear_smooth", "det_ok"]].copy()
        labelview_path = labelview_dir / f"{video_id}_labelview.csv"
        labelview_df.to_csv(labelview_path, index=False, encoding="utf-8-sig")

        plot_path = plots_dir / f"{video_id}_ear_plot.png"
        save_ear_plot(df, plot_path, video_id, fps, args.plot_dpi)

        valid_df = df[df["det_ok"] == 1].copy()
        summary_rows.append({
            "video_id": video_id,
            "video_file": video_path.name,
            "fps": fps,
            "total_frames_in_file": total_frames,
            "processed_frames": len(df),
            "det_ok_frames": int((df["det_ok"] == 1).sum()),
            "success_ratio": float((df["det_ok"] == 1).mean()),
            "ear_avg_min_valid": float(valid_df["ear_avg"].min()) if len(valid_df) > 0 else np.nan,
            "ear_avg_max_valid": float(valid_df["ear_avg"].max()) if len(valid_df) > 0 else np.nan,
            "duration_sec_processed": float(len(df) / fps),
        })

        print(
            f"[OK] {video_id}: frames={len(df)}, det_ok={int((df['det_ok'] == 1).sum())}, "
            f"success_ratio={(df['det_ok'] == 1).mean():.4f}"
        )

    if not all_rows:
        raise RuntimeError("No usable rows extracted from any self-recorded video.")

    merged_df = pd.DataFrame(all_rows)
    merged_path = out_dir / "frame_ear_selfrec.csv"
    merged_df.to_csv(merged_path, index=False, encoding="utf-8-sig")

    summary_df = pd.DataFrame(summary_rows)
    summary_path = out_dir / "video_summary.csv"
    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")

    print(f"\n[DONE] merged EAR csv -> {merged_path.resolve()}")
    print(f"[DONE] video summary -> {summary_path.resolve()}")
    print(f"[DONE] per-video EAR -> {per_video_ear_dir.resolve()}")
    print(f"[DONE] labelview csv -> {labelview_dir.resolve()}")
    print(f"[DONE] EAR plots -> {plots_dir.resolve()}")
    if args.save_debug_video:
        print(f"[DONE] debug videos -> {debug_dir.resolve()}")


if __name__ == "__main__":
    main()