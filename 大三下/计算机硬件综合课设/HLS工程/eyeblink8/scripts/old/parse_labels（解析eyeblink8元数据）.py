from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse Eyeblink8 .tag + .txt into frame-level label CSV."
    )
    parser.add_argument(
        "--raw_dir",
        type=str,
        default="raw",
        help="Folder containing *.tag and *.txt files.",
    )
    parser.add_argument(
        "--out_dir",
        type=str,
        default="work",
        help="Output folder.",
    )
    return parser.parse_args()


def safe_int(x: str) -> Optional[int]:
    try:
        return int(x)
    except Exception:
        return None


def safe_float(x: str) -> Optional[float]:
    try:
        return float(x)
    except Exception:
        return None


def read_timestamp_file(txt_path: Path) -> Dict[int, float]:
    """
    Parse Eyeblink8 timestamp file.
    Expected line style:
        0 0.00198786
        1 0.0496847
        ...
    """
    ts_map: Dict[int, float] = {}

    with txt_path.open("r", encoding="utf-8", errors="ignore") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            parts = re.split(r"\s+", line)
            if len(parts) < 2:
                print(f"[WARN] {txt_path.name}:{line_no} malformed timestamp line: {line}")
                continue

            frame_id = safe_int(parts[0])
            timestamp = safe_float(parts[1])

            if frame_id is None or timestamp is None:
                print(f"[WARN] {txt_path.name}:{line_no} failed to parse: {line}")
                continue

            ts_map[frame_id] = timestamp

    return ts_map


def parse_tag_line(line: str) -> Optional[Tuple[int, int, str, str, str, str, str, List[str]]]:
    """
    Parse one Eyeblink8 tag line.

    Typical line:
    82:1:X:C:X:C:X:229:164:150:147:253:193:286:197:326:198:359:196

    Meaning of the first 7 fields:
    frame_id : blink_id : NF : LE_FC : LE_NV : RE_FC : RE_NV

    Remaining fields are geometry-related annotations. We keep them in `extras`
    but do not rely on them here.
    """
    line = line.strip()
    if not line:
        return None
    if line.startswith("#"):
        return None

    # Eyeblink8 commonly uses ':'
    if ":" in line:
        parts = line.split(":")
    else:
        parts = re.split(r"\s+", line)

    if len(parts) < 7:
        return None

    frame_id = safe_int(parts[0])
    blink_id = safe_int(parts[1])

    if frame_id is None or blink_id is None:
        return None

    nf = parts[2].strip()
    le_fc = parts[3].strip()
    le_nv = parts[4].strip()
    re_fc = parts[5].strip()
    re_nv = parts[6].strip()
    extras = parts[7:]

    return frame_id, blink_id, nf, le_fc, le_nv, re_fc, re_nv, extras


def read_tag_file(tag_path: Path) -> Dict[int, dict]:
    """
    Read Eyeblink8 .tag file into a dict keyed by frame_id.
    """
    frame_map: Dict[int, dict] = {}
    started = False

    with tag_path.open("r", encoding="utf-8", errors="ignore") as f:
        for line_no, raw_line in enumerate(f, start=1):
            line = raw_line.strip()

            if not line:
                continue

            # Eyeblink8 files usually have a header and then '#start'
            if line.startswith("#start"):
                started = True
                continue

            if not started:
                continue

            item = parse_tag_line(line)
            if item is None:
                # ignore malformed/non-data lines
                continue

            frame_id, blink_id, nf, le_fc, le_nv, re_fc, re_nv, extras = item

            # For Eyeblink8, in your sample:
            # - normal state is often 'X'
            # - fully closed is 'C'
            # So here we use a conservative rule:
            is_blink = int(blink_id != -1)
            is_closed = int(le_fc == "C" and re_fc == "C")
            is_valid = int(nf == "X" and le_nv == "X" and re_nv == "X")

            frame_map[frame_id] = {
                "frame_id": frame_id,
                "blink_id": blink_id,
                "nf": nf,
                "le_fc": le_fc,
                "le_nv": le_nv,
                "re_fc": re_fc,
                "re_nv": re_nv,
                "is_blink": is_blink,
                "is_closed": is_closed,
                "is_valid": is_valid,
                "extra_fields_raw": ":".join(extras) if extras else "",
            }

    return frame_map


def collect_video_ids(raw_dir: Path) -> List[str]:
    """
    Collect stems that have both .tag and .txt.
    """
    tag_stems = {p.stem for p in raw_dir.glob("*.tag")}
    txt_stems = {p.stem for p in raw_dir.glob("*.txt")}
    ids = sorted(tag_stems & txt_stems, key=lambda x: str(x))
    return ids


def write_csv(rows: List[dict], out_path: Path) -> None:
    if not rows:
        print(f"[WARN] No rows to write: {out_path}")
        return

    fieldnames = list(rows[0].keys())
    with out_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    raw_dir = Path(args.raw_dir)
    out_dir = Path(args.out_dir)
    per_video_dir = out_dir / "per_video_labels"

    out_dir.mkdir(parents=True, exist_ok=True)
    per_video_dir.mkdir(parents=True, exist_ok=True)

    video_ids = collect_video_ids(raw_dir)
    if not video_ids:
        raise FileNotFoundError(
            f"No matched .tag + .txt pairs found in: {raw_dir.resolve()}"
        )

    all_rows: List[dict] = []

    print(f"[INFO] Found {len(video_ids)} video ids: {video_ids}")

    for video_id in video_ids:
        tag_path = raw_dir / f"{video_id}.tag"
        txt_path = raw_dir / f"{video_id}.txt"

        ts_map = read_timestamp_file(txt_path)
        frame_map = read_tag_file(tag_path)

        if not frame_map:
            print(f"[WARN] No parsed frames in {tag_path.name}")
            continue

        rows: List[dict] = []
        missing_ts = 0

        for frame_id in sorted(frame_map.keys()):
            item = frame_map[frame_id]
            timestamp = ts_map.get(frame_id, None)
            if timestamp is None:
                missing_ts += 1

            row = {
                "video_id": video_id,
                "frame_id": frame_id,
                "timestamp": timestamp,
                "blink_id": item["blink_id"],
                "is_blink": item["is_blink"],
                "is_closed": item["is_closed"],
                "is_valid": item["is_valid"],
                "nf": item["nf"],
                "le_fc": item["le_fc"],
                "le_nv": item["le_nv"],
                "re_fc": item["re_fc"],
                "re_nv": item["re_nv"],
                "extra_fields_raw": item["extra_fields_raw"],
            }
            rows.append(row)

        # save per-video csv
        per_video_out = per_video_dir / f"{video_id}_labels.csv"
        write_csv(rows, per_video_out)

        all_rows.extend(rows)

        blink_frames = sum(r["is_blink"] for r in rows)
        closed_frames = sum(r["is_closed"] for r in rows)
        valid_frames = sum(r["is_valid"] for r in rows)

        print(
            f"[OK] {video_id}: "
            f"frames={len(rows)}, "
            f"blink_frames={blink_frames}, "
            f"closed_frames={closed_frames}, "
            f"valid_frames={valid_frames}, "
            f"missing_timestamps={missing_ts}"
        )

    all_out = out_dir / "frame_labels.csv"
    write_csv(all_rows, all_out)

    print(f"\n[DONE] Wrote merged CSV: {all_out.resolve()}")
    print(f"[DONE] Wrote per-video CSVs: {per_video_dir.resolve()}")


if __name__ == "__main__":
    main()