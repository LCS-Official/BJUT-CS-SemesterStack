from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Set

import pandas as pd


def parse_list_arg(s: str) -> List[str]:
    return [x.strip() for x in s.split(",") if x.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build mixed dataset: Eyeblink8 provides open/blink, selfrec provides closed."
    )
    parser.add_argument(
        "--openblink_dir",
        type=str,
        default="work_dataset_binary",
        help="Folder containing open/blink-only train.csv val.csv test.csv",
    )
    parser.add_argument(
        "--selfrec_closed_csv",
        type=str,
        default="work_selfrec_labeled/windows_closed_selfrec.csv",
        help="Self-recorded closed windows csv",
    )
    parser.add_argument(
        "--out_dir",
        type=str,
        default="work_dataset_mixed",
        help="Output folder",
    )
    parser.add_argument(
        "--selfrec_train_videos",
        type=str,
        default="",
        help="Comma-separated selfrec video ids to use for TRAIN. "
             "If empty, all selfrec videos not assigned to val/test go to train.",
    )
    parser.add_argument(
        "--selfrec_val_videos",
        type=str,
        default="",
        help="Comma-separated selfrec video ids to use for VAL",
    )
    parser.add_argument(
        "--selfrec_test_videos",
        type=str,
        default="",
        help="Comma-separated selfrec video ids to use for TEST",
    )
    parser.add_argument(
        "--shuffle_train",
        action="store_true",
        help="Shuffle mixed training set after merging",
    )
    parser.add_argument(
        "--random_seed",
        type=int,
        default=42,
        help="Random seed for optional shuffle",
    )
    return parser.parse_args()


def ensure_required(df: pd.DataFrame, name: str) -> None:
    needed = ["video_id", "center_frame", "label_name", "label"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"{name} missing columns: {missing}")

    feat_cols = [c for c in df.columns if c.startswith("ear_")]
    if not feat_cols:
        raise ValueError(f"{name} has no ear_0 ... ear_14 feature columns")


def add_source_col(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    out = df.copy()
    if "source" not in out.columns:
        out["source"] = source_name
    else:
        out["source"] = out["source"].fillna(source_name)
    return out


def align_columns(base_df: pd.DataFrame, new_df: pd.DataFrame) -> pd.DataFrame:
    out = new_df.copy()
    for c in base_df.columns:
        if c not in out.columns:
            out[c] = ""
    out = out[base_df.columns]
    return out


def filter_openblink(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out = out[out["label_name"].isin(["open", "blink"])].copy()
    out = out[out["label"].isin([0, 1])].copy()
    return out.reset_index(drop=True)


def filter_closed(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out = out[out["label_name"] == "closed"].copy()
    out = out[out["label"] == 2].copy()
    return out.reset_index(drop=True)


def check_no_overlap(a: Set[str], b: Set[str], name_a: str, name_b: str) -> None:
    overlap = a & b
    if overlap:
        raise ValueError(f"Overlap between {name_a} and {name_b}: {sorted(overlap)}")


def split_selfrec_closed(
    selfrec_df: pd.DataFrame,
    train_videos_arg: str,
    val_videos_arg: str,
    test_videos_arg: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    all_selfrec_videos = sorted(selfrec_df["video_id"].astype(str).unique().tolist())

    val_videos = set(parse_list_arg(val_videos_arg))
    test_videos = set(parse_list_arg(test_videos_arg))
    train_videos = set(parse_list_arg(train_videos_arg))

    check_no_overlap(train_videos, val_videos, "selfrec_train_videos", "selfrec_val_videos")
    check_no_overlap(train_videos, test_videos, "selfrec_train_videos", "selfrec_test_videos")
    check_no_overlap(val_videos, test_videos, "selfrec_val_videos", "selfrec_test_videos")

    known_video_set = set(all_selfrec_videos)
    for name, vids in [
        ("selfrec_train_videos", train_videos),
        ("selfrec_val_videos", val_videos),
        ("selfrec_test_videos", test_videos),
    ]:
        unknown = vids - known_video_set
        if unknown:
            raise ValueError(f"{name} contains unknown video ids: {sorted(unknown)}")

    # 如果用户没显式指定 train，则默认“所有未进 val/test 的 selfrec 视频都进 train”
    if not train_videos:
        train_videos = known_video_set - val_videos - test_videos

    train_df = selfrec_df[selfrec_df["video_id"].isin(sorted(train_videos))].copy()
    val_df = selfrec_df[selfrec_df["video_id"].isin(sorted(val_videos))].copy()
    test_df = selfrec_df[selfrec_df["video_id"].isin(sorted(test_videos))].copy()

    return train_df, val_df, test_df


def print_stats(name: str, df: pd.DataFrame) -> None:
    print(f"\n[{name}] samples = {len(df)}")
    if len(df) == 0:
        return

    print(df["label_name"].value_counts().to_string())
    if "source" in df.columns:
        print("\nsource counts:")
        print(df["source"].value_counts().to_string())


def main() -> None:
    args = parse_args()

    openblink_dir = Path(args.openblink_dir)
    selfrec_closed_csv = Path(args.selfrec_closed_csv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    train_csv = openblink_dir / "train.csv"
    val_csv = openblink_dir / "val.csv"
    test_csv = openblink_dir / "test.csv"

    if not train_csv.exists():
        raise FileNotFoundError(f"Missing: {train_csv}")
    if not val_csv.exists():
        raise FileNotFoundError(f"Missing: {val_csv}")
    if not test_csv.exists():
        raise FileNotFoundError(f"Missing: {test_csv}")
    if not selfrec_closed_csv.exists():
        raise FileNotFoundError(f"Missing: {selfrec_closed_csv}")

    train_ob = pd.read_csv(train_csv, dtype={"video_id": str})
    val_ob = pd.read_csv(val_csv, dtype={"video_id": str})
    test_ob = pd.read_csv(test_csv, dtype={"video_id": str})
    selfrec_closed = pd.read_csv(selfrec_closed_csv, dtype={"video_id": str})

    ensure_required(train_ob, "openblink train.csv")
    ensure_required(val_ob, "openblink val.csv")
    ensure_required(test_ob, "openblink test.csv")
    ensure_required(selfrec_closed, "selfrec closed csv")

    train_ob = filter_openblink(train_ob)
    val_ob = filter_openblink(val_ob)
    test_ob = filter_openblink(test_ob)
    selfrec_closed = filter_closed(selfrec_closed)

    train_ob = add_source_col(train_ob, "eyeblink8")
    val_ob = add_source_col(val_ob, "eyeblink8")
    test_ob = add_source_col(test_ob, "eyeblink8")
    selfrec_closed = add_source_col(selfrec_closed, "selfrec")

    # selfrec closed split
    selfrec_train, selfrec_val, selfrec_test = split_selfrec_closed(
        selfrec_df=selfrec_closed,
        train_videos_arg=args.selfrec_train_videos,
        val_videos_arg=args.selfrec_val_videos,
        test_videos_arg=args.selfrec_test_videos,
    )

    # 对齐列
    val_ob = align_columns(train_ob, val_ob)
    test_ob = align_columns(train_ob, test_ob)
    selfrec_train = align_columns(train_ob, selfrec_train)
    selfrec_val = align_columns(train_ob, selfrec_val)
    selfrec_test = align_columns(train_ob, selfrec_test)

    # 合并
    train_mixed = pd.concat([train_ob, selfrec_train], axis=0, ignore_index=True)
    val_mixed = pd.concat([val_ob, selfrec_val], axis=0, ignore_index=True)
    test_mixed = pd.concat([test_ob, selfrec_test], axis=0, ignore_index=True)

    if args.shuffle_train:
        train_mixed = train_mixed.sample(frac=1.0, random_state=args.random_seed).reset_index(drop=True)

    all_mixed = pd.concat([train_mixed, val_mixed, test_mixed], axis=0, ignore_index=True)

    # 保存
    train_out = out_dir / "train.csv"
    val_out = out_dir / "val.csv"
    test_out = out_dir / "test.csv"
    all_out = out_dir / "windows_all_mixed.csv"
    summary_out = out_dir / "summary.json"

    train_mixed.to_csv(train_out, index=False, encoding="utf-8-sig")
    val_mixed.to_csv(val_out, index=False, encoding="utf-8-sig")
    test_mixed.to_csv(test_out, index=False, encoding="utf-8-sig")
    all_mixed.to_csv(all_out, index=False, encoding="utf-8-sig")

    summary = {
        "note": (
            "Eyeblink8 contributes only open/blink. "
            "selfrec contributes only closed. "
            "If val/test have no selfrec video ids assigned, they will contain no ground-truth closed."
        ),
        "selfrec_video_ids_all": sorted(selfrec_closed["video_id"].astype(str).unique().tolist()),
        "selfrec_train_videos_used": sorted(selfrec_train["video_id"].astype(str).unique().tolist()),
        "selfrec_val_videos_used": sorted(selfrec_val["video_id"].astype(str).unique().tolist()),
        "selfrec_test_videos_used": sorted(selfrec_test["video_id"].astype(str).unique().tolist()),
        "train_samples": int(len(train_mixed)),
        "val_samples": int(len(val_mixed)),
        "test_samples": int(len(test_mixed)),
        "train_label_counts": train_mixed["label_name"].value_counts().to_dict(),
        "val_label_counts": val_mixed["label_name"].value_counts().to_dict(),
        "test_label_counts": test_mixed["label_name"].value_counts().to_dict(),
    }

    with summary_out.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"[DONE] train.csv -> {train_out}")
    print(f"[DONE] val.csv   -> {val_out}")
    print(f"[DONE] test.csv  -> {test_out}")
    print(f"[DONE] windows_all_mixed.csv -> {all_out}")
    print(f"[DONE] summary.json -> {summary_out}")

    print_stats("TRAIN_OPENBLINK", train_ob)
    print_stats("SELFREC_CLOSED_ALL", selfrec_closed)
    print_stats("SELFREC_CLOSED_TRAIN", selfrec_train)
    print_stats("SELFREC_CLOSED_VAL", selfrec_val)
    print_stats("SELFREC_CLOSED_TEST", selfrec_test)
    print_stats("TRAIN_MIXED", train_mixed)
    print_stats("VAL_MIXED", val_mixed)
    print_stats("TEST_MIXED", test_mixed)

    if len(selfrec_val) == 0:
        print("\n[WARN] VAL currently has no selfrec closed samples.")
    if len(selfrec_test) == 0:
        print("[WARN] TEST currently has no selfrec closed samples.")
    print("[INFO] This is expected for now if only one selfrec video has been labeled.")


if __name__ == "__main__":
    main()