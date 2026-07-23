from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser(
        description="Review self-recorded video with frame id, timestamp and EAR overlay."
    )
    parser.add_argument("--video_path", type=str, required=True, help="Path to self-recorded video")
    parser.add_argument("--labelview_csv", type=str, required=True, help="Path to xxx_labelview.csv")
    parser.add_argument("--start_frame", type=int, default=0, help="Initial frame")
    return parser.parse_args()


def main():
    args = parse_args()

    video_path = Path(args.video_path)
    labelview_csv = Path(args.labelview_csv)

    if not video_path.exists():
        raise FileNotFoundError(f"video not found: {video_path}")
    if not labelview_csv.exists():
        raise FileNotFoundError(f"labelview csv not found: {labelview_csv}")

    df = pd.read_csv(labelview_csv)
    if "frame_id" not in df.columns:
        raise ValueError("labelview csv must contain frame_id column")

    df = df.set_index("frame_id")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"failed to open video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30.0

    frame_id = max(0, args.start_frame)

    print("=" * 60)
    print("Keyboard controls:")
    print("  d / Right Arrow : next frame")
    print("  a / Left Arrow  : previous frame")
    print("  j               : jump backward 30 frames")
    print("  l               : jump forward 30 frames")
    print("  s               : print current frame_id")
    print("  q / ESC         : quit")
    print("=" * 60)

    while True:
        frame_id = max(0, min(frame_id, total_frames - 1))
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        ok, frame = cap.read()
        if not ok:
            break

        if frame_id in df.index:
            row = df.loc[frame_id]
            timestamp = row.get("timestamp_sec", frame_id / fps)
            ear_avg = row.get("ear_avg", float("nan"))
            ear_smooth = row.get("ear_smooth", float("nan"))
            det_ok = row.get("det_ok", -1)
        else:
            timestamp = frame_id / fps
            ear_avg = float("nan")
            ear_smooth = float("nan")
            det_ok = -1

        text1 = f"frame_id={frame_id} / {total_frames-1}"
        text2 = f"time={timestamp:.3f}s  det_ok={det_ok}"
        text3 = f"ear_avg={ear_avg:.4f}  ear_smooth={ear_smooth:.4f}"

        show = frame.copy()
        cv2.putText(show, text1, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(show, text2, (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(show, text3, (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("review_selfrec_video", show)
        key = cv2.waitKeyEx(0)

        # ESC
        if key == 27 or key == ord("q"):
            break
        # Right arrow or d
        elif key == 2555904 or key == ord("d"):
            frame_id += 1
        # Left arrow or a
        elif key == 2424832 or key == ord("a"):
            frame_id -= 1
        elif key == ord("l"):
            frame_id += 30
        elif key == ord("j"):
            frame_id -= 30
        elif key == ord("s"):
            print(f"[MARK] current frame_id = {frame_id}")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()