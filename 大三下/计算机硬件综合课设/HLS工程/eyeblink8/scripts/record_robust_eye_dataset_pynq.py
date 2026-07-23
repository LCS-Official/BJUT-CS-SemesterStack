#!/usr/bin/env python3
from __future__ import annotations

"""
Board-side wrapper for recording constant open/closed eye videos.

Run on the PYNQ board after sourcing the PYNQ environment, for example:
  source /etc/profile.d/xrt_setup.sh
  source /etc/profile.d/pynq_venv.sh

  sudo -E python3 /home/xilinx/LC_SVM/scripts/record_robust_eye_dataset.py --label open --seconds 20
  sudo -E python3 /home/xilinx/LC_SVM/scripts/record_robust_eye_dataset.py --label closed --seconds 20

The script calls record_camera_rawfast.py, saving a clean video plus small
metadata JSON. It does not run dlib, EyeFeature, or SVM.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Record a robust EyeFeature open/closed dataset video on PYNQ.")
    p.add_argument("--label", required=True, choices=["open", "closed", "non_closed"], help="State held during this recording")
    p.add_argument("--session", default="", help="Session folder name. Default timestamped session.")
    p.add_argument("--subject", default="", help="Optional subject/person identifier for metadata")
    p.add_argument("--note", default="", help="Optional free-form note for metadata")
    p.add_argument("--seconds", type=float, default=15.0)
    p.add_argument("--capture-fps", type=float, default=15.0)
    p.add_argument("--output-fps", type=float, default=15.0)
    p.add_argument("--out-root", default="/home/xilinx/LC_SVM/data/robust_eye_dataset")
    p.add_argument("--recorder", default="/home/xilinx/LC_SVM/scripts/record_camera_rawfast.py")

    p.add_argument("--bit", default="/home/xilinx/LC_SVM/final.bit")
    p.add_argument("--width", type=int, default=640)
    p.add_argument("--height", type=int, default=480)
    p.add_argument("--pixel-bytes", type=int, default=4)
    p.add_argument("--num-buffers", type=int, default=16)
    p.add_argument("--num-fstores", type=int, default=16)
    p.add_argument("--warmup", type=float, default=1.0)

    p.add_argument("--color-mode", default="grb", choices=["rgb", "rbg", "grb", "gbr", "brg", "bgr"])
    p.add_argument("--byteswap", action="store_true")
    p.add_argument("--rotate", default="ccw", choices=["none", "cw", "ccw", "180"])
    p.add_argument("--flip", default="none", choices=["none", "h", "v", "hv"])
    p.add_argument("--fourcc", default="MJPG")
    p.add_argument("--keep-raw-npy", action="store_true", help="Also keep raw uint16 RGB565 .npy frames")
    p.add_argument("--dry-run", action="store_true", help="Print the command and metadata path, but do not record")
    return p.parse_args()


def normalized_label(label: str) -> str:
    return "open" if label in {"open", "non_closed"} else "closed"


def build_command(args: argparse.Namespace, video_path: Path, first_png: Path, last_png: Path, raw_npy: Path) -> List[str]:
    cmd = [
        sys.executable,
        str(args.recorder),
        "--bit", str(args.bit),
        "--width", str(int(args.width)),
        "--height", str(int(args.height)),
        "--pixel-bytes", str(int(args.pixel_bytes)),
        "--num-buffers", str(int(args.num_buffers)),
        "--num-fstores", str(int(args.num_fstores)),
        "--seconds", str(float(args.seconds)),
        "--capture-fps", str(float(args.capture_fps)),
        "--output-fps", str(float(args.output_fps)),
        "--warmup", str(float(args.warmup)),
        "--out", str(video_path),
        "--fourcc", str(args.fourcc),
        "--color-mode", str(args.color_mode),
        "--rotate", str(args.rotate),
        "--flip", str(args.flip),
        "--save-first-png", str(first_png),
        "--save-last-png", str(last_png),
    ]
    if bool(args.byteswap):
        cmd.append("--byteswap")
    if bool(args.keep_raw_npy):
        cmd.extend(["--keep-raw-npy", str(raw_npy)])
    return cmd


def main() -> None:
    args = parse_args()
    ts = time.strftime("%Y%m%d_%H%M%S")
    session = args.session.strip() or f"session_{ts}"
    label = normalized_label(args.label)
    out_dir = Path(args.out_root) / session / label
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = f"{label}_{ts}"
    video_path = out_dir / f"{stem}.avi"
    first_png = out_dir / f"{stem}_first.png"
    last_png = out_dir / f"{stem}_last.png"
    raw_npy = out_dir / f"{stem}_raw565.npy"
    meta_path = out_dir / f"{stem}_metadata.json"

    cmd = build_command(args, video_path, first_png, last_png, raw_npy)
    metadata = {
        "timestamp": ts,
        "session": session,
        "label": label,
        "label_binary": 1 if label == "closed" else 0,
        "subject": args.subject,
        "note": args.note,
        "video_path": str(video_path),
        "first_png": str(first_png),
        "last_png": str(last_png),
        "raw_npy": str(raw_npy) if args.keep_raw_npy else "",
        "record_seconds": float(args.seconds),
        "capture_fps": float(args.capture_fps),
        "output_fps": float(args.output_fps),
        "color_mode": args.color_mode,
        "rotate": args.rotate,
        "flip": args.flip,
        "fourcc": args.fourcc,
        "command": cmd,
        "cwd": os.getcwd(),
    }

    print("[ROBUST_REC] output_dir:", out_dir, flush=True)
    print("[ROBUST_REC] video:", video_path, flush=True)
    print("[ROBUST_REC] label:", label, flush=True)
    print("[ROBUST_REC] command:", " ".join(cmd), flush=True)

    if args.dry_run:
        metadata["dry_run"] = True
        meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
        print("[ROBUST_REC] dry-run metadata:", meta_path, flush=True)
        return

    subprocess.run(cmd, check=True)
    metadata["dry_run"] = False
    metadata["video_size_bytes"] = int(video_path.stat().st_size) if video_path.exists() else 0
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print("[ROBUST_REC] metadata:", meta_path, flush=True)


if __name__ == "__main__":
    main()
