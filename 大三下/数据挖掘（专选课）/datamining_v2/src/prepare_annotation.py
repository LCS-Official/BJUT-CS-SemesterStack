import argparse
import csv
from pathlib import Path


ANNOTATION_FIELDS = [
    "run_id",
    "prompt_id",
    "scenario_id",
    "geometry_type",
    "obstacle_type",
    "level",
    "perturbation_type",
    "motion_constraint",
    "image_path",
    "image_role",
    "model_key",
    "model",
    "temperature",
    "reference_judgment",
    "final_judgment",
    "is_correct",
    "judgment_flip",
    "reasoning_step_count",
    "uses_formula",
    "uses_coordinate_system",
    "spatial_modeling_depth",
    "failure_mode",
    "error_note",
    "response_text",
]


EMPTY_ANNOTATION_VALUES = {
    "final_judgment": "",
    "is_correct": "",
    "judgment_flip": "",
    "reasoning_step_count": "",
    "uses_formula": "",
    "uses_coordinate_system": "",
    "spatial_modeling_depth": "",
    "failure_mode": "",
    "error_note": "",
}


def load_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ANNOTATION_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def is_valid_response(row):
    return row.get("request_status") == "ok" and bool(row.get("response_text", "").strip())


def build_annotation_row(row):
    annotation_row = {field: row.get(field, "") for field in ANNOTATION_FIELDS}
    annotation_row.update(EMPTY_ANNOTATION_VALUES)
    return annotation_row


def main():
    parser = argparse.ArgumentParser(description="Prepare a human annotation CSV from raw model responses.")
    parser.add_argument("--input", default="data/raw/responses.csv")
    parser.add_argument("--out", default="data/processed/annotated_responses.csv")
    parser.add_argument("--include-invalid", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    out_path = Path(args.out)
    if out_path.exists() and not args.overwrite:
        raise SystemExit(f"{args.out} already exists. Use --overwrite to replace it.")

    raw_rows = load_csv(args.input)
    if args.include_invalid:
        kept_rows = raw_rows
    else:
        kept_rows = [row for row in raw_rows if is_valid_response(row)]

    annotation_rows = [build_annotation_row(row) for row in kept_rows]
    write_csv(args.out, annotation_rows)

    skipped = len(raw_rows) - len(kept_rows)
    print(f"Loaded {len(raw_rows)} raw rows.")
    print(f"Wrote {len(annotation_rows)} rows to {args.out}.")
    if skipped:
        print(f"Skipped {skipped} invalid rows without usable response_text.")


if __name__ == "__main__":
    main()
