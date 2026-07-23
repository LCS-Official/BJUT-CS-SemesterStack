import argparse
import csv
import json
import re
import time
from collections import Counter, defaultdict
from pathlib import Path

from collect_responses import ApiCallError, call_model, compact_text


ANNOTATION_SYSTEM_PROMPT = """你是数据挖掘课程项目的标注员。你的任务是阅读一个大语言模型对“电动轮椅在楼梯间/转角处能否通过”的回答，并把回答转成结构化标签。

只输出一个 JSON 对象，不要输出 Markdown，不要解释额外内容。

字段要求：
- final_judgment: 必须是 pass、blocked、uncertain、no_answer 之一。根据被标注模型的最终结论判断，而不是你自己的几何判断。
- reasoning_step_count: 非负整数。粗略统计显式推理步骤或主要推理段落数量。
- uses_formula: 0 或 1。出现公式、代数表达、明确数值计算则为 1。
- uses_coordinate_system: 0 或 1。出现坐标系、可行域、扫掠空间、包络、二维建模、多边形/矩形刚体约束等则为 1。
- spatial_modeling_depth: 0、1、2、3。0=纯直觉；1=提到空间因素；2=使用尺寸/半径/余量等半形式化推理；3=明确几何建模或坐标/可行域/扫掠空间。
- failure_mode: 必须是 no_error、concept_confusion、motion_constraint_ignorance、calculation_error、unsupported_assumption、boundary_neglect、obstacle_ignorance、false_obstacle_removal、irrelevant_noise_distraction、self_contradiction、over_refusal、other 之一。
- error_note: 中文短句。无明显错误时填空字符串。
- confidence: 0 到 1 的小数，表示你对标签的置信度。

标注原则：
1. 只评价被标注模型的回答内容，不重新解题。
2. 如果回答最终说“能过”，final_judgment=pass；“不能过”，final_judgment=blocked；“信息不足/无法判断/取决于条件”，final_judgment=uncertain。
3. 如果过程和结论矛盾，按最终结论标 final_judgment，failure_mode 标 self_contradiction。
4. 如果参考答案是 unknown 或 borderline，不要因为模型不确定而视为错误；failure_mode 主要看回答自身有没有明显逻辑问题。
"""


REQUIRED_LABELS = {
    "final_judgment": {"pass", "blocked", "uncertain", "no_answer"},
    "failure_mode": {
        "no_error",
        "concept_confusion",
        "motion_constraint_ignorance",
        "calculation_error",
        "unsupported_assumption",
        "boundary_neglect",
        "obstacle_ignorance",
        "false_obstacle_removal",
        "irrelevant_noise_distraction",
        "self_contradiction",
        "over_refusal",
        "other",
    },
}

AUTO_FIELDS = [
    "auto_annotator_model",
    "auto_label_confidence",
    "auto_label_raw",
    "review_required",
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader), reader.fieldnames or []


def write_csv(path, rows, fieldnames):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_json_object(text):
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def build_user_prompt(row):
    metadata = {
        "run_id": row.get("run_id", ""),
        "prompt_id": row.get("prompt_id", ""),
        "scenario_id": row.get("scenario_id", ""),
        "geometry_type": row.get("geometry_type", ""),
        "obstacle_type": row.get("obstacle_type", ""),
        "level": row.get("level", ""),
        "perturbation_type": row.get("perturbation_type", ""),
        "motion_constraint": row.get("motion_constraint", ""),
        "image_path": row.get("image_path", ""),
        "image_role": row.get("image_role", ""),
        "model_key": row.get("model_key", ""),
        "model": row.get("model", ""),
        "reference_judgment": row.get("reference_judgment", ""),
    }
    return (
        "请标注下面这条模型回复。\n\n"
        f"元数据：{json.dumps(metadata, ensure_ascii=False)}\n\n"
        "被标注模型的回复：\n"
        f"{row.get('response_text', '')}"
    )


def normalize_int(value, default=0):
    try:
        return str(int(value))
    except (TypeError, ValueError):
        return str(default)


def normalize_binary(value):
    if isinstance(value, str):
        value = value.strip().lower()
        if value in {"1", "true", "yes", "有", "是"}:
            return "1"
        if value in {"0", "false", "no", "无", "否"}:
            return "0"
    return "1" if bool(value) else "0"


def normalize_depth(value):
    try:
        depth = int(value)
    except (TypeError, ValueError):
        depth = 0
    return str(min(3, max(0, depth)))


def normalize_confidence(value):
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        confidence = 0.0
    return str(min(1.0, max(0.0, confidence)))


def is_correct(reference_judgment, final_judgment):
    if reference_judgment in {"borderline", "unknown", ""}:
        return ""
    return "1" if reference_judgment == final_judgment else "0"


def should_review(row):
    confidence = float(row.get("auto_label_confidence") or 0)
    if confidence < 0.8:
        return "1"
    if row.get("failure_mode") and row.get("failure_mode") != "no_error":
        return "1"
    if row.get("final_judgment") == "no_answer":
        return "1"
    if row.get("reference_judgment") in {"pass", "blocked"} and row.get("is_correct") == "0":
        return "1"
    return "0"


def apply_annotation(row, label, annotator_model, raw_text):
    final_judgment = str(label.get("final_judgment", "")).strip()
    if final_judgment not in REQUIRED_LABELS["final_judgment"]:
        final_judgment = "uncertain"

    failure_mode = str(label.get("failure_mode", "")).strip()
    if failure_mode not in REQUIRED_LABELS["failure_mode"]:
        failure_mode = "other"

    row["final_judgment"] = final_judgment
    row["reasoning_step_count"] = normalize_int(label.get("reasoning_step_count"), default=0)
    row["uses_formula"] = normalize_binary(label.get("uses_formula"))
    row["uses_coordinate_system"] = normalize_binary(label.get("uses_coordinate_system"))
    row["spatial_modeling_depth"] = normalize_depth(label.get("spatial_modeling_depth"))
    row["failure_mode"] = failure_mode
    row["error_note"] = str(label.get("error_note", "") or "").strip()
    row["is_correct"] = is_correct(row.get("reference_judgment", ""), final_judgment)
    row["auto_annotator_model"] = annotator_model
    row["auto_label_confidence"] = normalize_confidence(label.get("confidence"))
    row["auto_label_raw"] = compact_text(raw_text, limit=2000)
    row["review_required"] = should_review(row)
    return row


def fill_judgment_flip(rows):
    grouped = defaultdict(list)
    for row in rows:
        key = (row.get("model_key", ""), row.get("scenario_id", ""), row.get("level", ""))
        grouped[key].append(row)

    baselines = {}
    for key, group in grouped.items():
        baseline_judgments = [
            row.get("final_judgment", "")
            for row in group
            if row.get("perturbation_type") == "none" and row.get("final_judgment")
        ]
        if baseline_judgments:
            baselines[key] = Counter(baseline_judgments).most_common(1)[0][0]

    for row in rows:
        if not row.get("final_judgment"):
            row["judgment_flip"] = ""
            continue
        if row.get("perturbation_type") == "none":
            row["judgment_flip"] = "0"
            continue
        key = (row.get("model_key", ""), row.get("scenario_id", ""), row.get("level", ""))
        baseline = baselines.get(key)
        row["judgment_flip"] = "" if not baseline else ("1" if row["final_judgment"] != baseline else "0")


def main():
    parser = argparse.ArgumentParser(description="Auto-annotate model responses with a strong LLM.")
    parser.add_argument("--input", default="data/processed/annotated_responses.csv")
    parser.add_argument("--out", default="data/processed/annotated_responses_auto.csv")
    parser.add_argument("--config", default="configs/annotator.json")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sleep", type=float, default=0.5)
    parser.add_argument("--force", action="store_true", help="Re-annotate rows that already have final_judgment.")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    out_path = Path(args.out)
    if out_path.exists() and not args.overwrite:
        raise SystemExit(f"{args.out} already exists. Use --overwrite to replace it.")

    rows, fieldnames = load_csv(args.input)
    config = load_json(args.config)
    config["system_prompt"] = ANNOTATION_SYSTEM_PROMPT

    if args.limit is None:
        indices = list(range(len(rows)))
    else:
        indices = list(range(min(args.limit, len(rows))))

    completed = 0
    errors = 0
    for index in indices:
        row = rows[index]
        if row.get("final_judgment") and not args.force:
            continue
        print(f"[{index + 1}/{len(rows)}] {row.get('prompt_id')} -> {row.get('model_key')}")
        try:
            raw_text, _raw_json, _attempt_count, _api_url = call_model(
                config, build_user_prompt(row)
            )
            label = parse_json_object(raw_text)
            rows[index] = apply_annotation(row, label, config["model"], raw_text)
            completed += 1
        except (ApiCallError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            row["review_required"] = "1"
            row["auto_annotator_model"] = config.get("model", "")
            row["auto_label_confidence"] = "0"
            row["auto_label_raw"] = compact_text(str(exc), limit=2000)
            errors += 1
            print(f"  auto annotation failed: {exc}")
        time.sleep(args.sleep)

    fill_judgment_flip(rows)
    output_fields = list(fieldnames)
    for field in AUTO_FIELDS:
        if field not in output_fields:
            output_fields.append(field)
    write_csv(args.out, rows, output_fields)

    print(f"Auto-annotated {completed} rows.")
    print(f"Rows needing manual attention due to annotator errors: {errors}.")
    print(f"Saved to {args.out}.")


if __name__ == "__main__":
    main()
