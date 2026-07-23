import argparse
import base64
import csv
import json
import mimetypes
import os
import random
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import requests


SYSTEM_PROMPT = (
    "你正在回答一个空间推理实验问题。请先给出清晰推理过程，"
    "最后用单独一行写出：最终判断：能过 / 不能过 / 信息不足。"
)

TRANSIENT_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}


class ApiCallError(RuntimeError):
    def __init__(self, message, status_code=None, response_text="", url=""):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text
        self.url = url


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_prompts(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader), reader.fieldnames or []


def ensure_parent(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def build_chat_completions_url(model_config):
    if "chat_completions_url" in model_config:
        return model_config["chat_completions_url"].rstrip("/")

    base_url = model_config["base_url"].rstrip("/")
    if base_url.endswith("/chat/completions"):
        return base_url
    if base_url.endswith("/v1") or base_url.endswith("/openai"):
        return f"{base_url}/chat/completions"
    return f"{base_url}/v1/chat/completions"


def compact_text(text, limit=1000):
    text = (text or "").replace("\r", " ").replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "...[truncated]"


def resolve_workspace_path(path_text):
    if not path_text:
        return None
    path = Path(path_text)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def image_to_data_url(image_path):
    path = resolve_workspace_path(image_path)
    if path is None:
        return None
    if not path.exists():
        raise FileNotFoundError(f"Image file does not exist: {path}")
    if "题目示意图" in path.name:
        raise ValueError("Refusing to send the annotated schematic image to the model.")

    mime_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{data}"


def build_user_content(prompt_text, image_path=""):
    if not image_path:
        return prompt_text

    data_url = image_to_data_url(image_path)
    return [
        {"type": "text", "text": prompt_text},
        {"type": "image_url", "image_url": {"url": data_url}},
    ]


def sleep_before_retry(attempt, base_delay):
    delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, base_delay)
    time.sleep(delay)


def extract_finish_reason(raw_json_text_or_obj):
    try:
        if isinstance(raw_json_text_or_obj, str):
            data = json.loads(raw_json_text_or_obj or "{}")
        else:
            data = raw_json_text_or_obj or {}
        return data.get("choices", [{}])[0].get("finish_reason", "")
    except Exception:
        return ""


def is_complete_ok(row, rerun_truncated=False):
    if row.get("request_status") != "ok":
        return False
    if not (row.get("response_text", "") or "").strip():
        return False
    if rerun_truncated and extract_finish_reason(row.get("raw_json", "{}")) == "length":
        return False
    return True


def load_existing_complete_counts(path, rerun_truncated=False):
    counts = Counter()
    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        return counts

    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Existing output rows: {len(rows)}")
    status_counts = Counter(row.get("request_status", "") for row in rows)
    print(f"Existing request_status counts: {dict(status_counts)}")
    ok_finish_counts = Counter(
        extract_finish_reason(row.get("raw_json", "{}"))
        for row in rows
        if row.get("request_status") == "ok"
    )
    print(f"Existing ok finish_reason counts: {dict(ok_finish_counts)}")

    for row in rows:
        if is_complete_ok(row, rerun_truncated=rerun_truncated):
            key = (row.get("prompt_id", ""), row.get("model_key", ""))
            counts[key] += 1
    return counts


def call_openai_compatible(model_config, prompt_text, image_path=""):
    api_key = os.getenv(model_config["api_key_env"])
    if not api_key:
        raise RuntimeError(f"Missing environment variable: {model_config['api_key_env']}")

    url = build_chat_completions_url(model_config)
    payload = {
        "model": model_config["model"],
        "temperature": model_config.get("temperature", 0),
        "messages": [
            {"role": "system", "content": model_config.get("system_prompt", SYSTEM_PROMPT)},
            {"role": "user", "content": build_user_content(prompt_text, image_path)},
        ],
    }
    if "max_tokens" in model_config:
        payload["max_tokens"] = model_config["max_tokens"]
    for optional_key in ["reasoning_effort", "top_p", "response_format"]:
        if optional_key in model_config:
            payload[optional_key] = model_config[optional_key]
    if "extra_payload" in model_config:
        payload.update(model_config["extra_payload"])

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if "extra_headers" in model_config:
        headers.update(model_config["extra_headers"])

    max_retries = int(model_config.get("max_retries", 3))
    retry_base_delay = float(model_config.get("retry_base_delay", 2))
    timeout_seconds = model_config.get("timeout_seconds", 120)
    last_error = None

    # IMPORTANT: local LM Studio is often affected by Windows/system proxy variables.
    # trust_env=false disables requests' use of HTTP_PROXY/HTTPS_PROXY/etc.
    session = requests.Session()
    session.trust_env = bool(model_config.get("trust_env", True))

    for attempt in range(1, max_retries + 2):
        try:
            response = session.post(
                url,
                headers=headers,
                json=payload,
                timeout=timeout_seconds,
            )
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_error = ApiCallError(str(exc), url=url)
            if attempt <= max_retries:
                print(f"  transient network error, retry {attempt}/{max_retries}: {exc}")
                sleep_before_retry(attempt, retry_base_delay)
                continue
            raise last_error from exc

        if response.status_code in TRANSIENT_STATUS_CODES and attempt <= max_retries:
            message = compact_text(response.text)
            print(
                f"  HTTP {response.status_code}, retry {attempt}/{max_retries}: "
                f"{message or response.reason}"
            )
            sleep_before_retry(attempt, retry_base_delay)
            continue

        if not response.ok:
            message = compact_text(response.text)
            raise ApiCallError(
                f"HTTP {response.status_code}: {message or response.reason}",
                status_code=response.status_code,
                response_text=message,
                url=url,
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise ApiCallError(
                f"Invalid JSON response: {compact_text(response.text)}",
                status_code=response.status_code,
                response_text=compact_text(response.text),
                url=url,
            ) from exc

        if not data.get("choices"):
            raise ApiCallError(
                f"Response has no choices: {compact_text(json.dumps(data, ensure_ascii=False))}",
                status_code=response.status_code,
                response_text=compact_text(json.dumps(data, ensure_ascii=False)),
                url=url,
            )

        text = data["choices"][0]["message"].get("content", "")
        finish_reason = data["choices"][0].get("finish_reason", "")
        if not text.strip():
            message = f"Empty assistant content, finish_reason={finish_reason}"
            if attempt <= max_retries:
                print(f"  {message}, retry {attempt}/{max_retries}")
                sleep_before_retry(attempt, retry_base_delay)
                continue
            raise ApiCallError(
                message,
                status_code=response.status_code,
                response_text=compact_text(json.dumps(data, ensure_ascii=False)),
                url=url,
            )

        return text, data, attempt, url

    if last_error:
        raise last_error
    raise ApiCallError("Request failed without a response", url=url)


def call_model(model_config, prompt_text, image_path=""):
    provider = model_config.get("provider", "openai_compatible")
    if provider == "openai_compatible":
        return call_openai_compatible(model_config, prompt_text, image_path=image_path)
    raise ValueError(f"Unsupported provider: {provider}")


def output_fieldnames(prompt_fieldnames):
    fixed_prefix = [
        "run_id",
        "timestamp_utc",
    ]
    fixed_suffix = [
        "input_modality",
        "source_image_path",
        "model_key",
        "provider",
        "model",
        "temperature",
        "request_status",
        "attempt_count",
        "http_status",
        "api_url",
        "error_message",
        "response_text",
        "raw_json",
    ]
    preferred_prompt_order = [
        "prompt_id",
        "scenario_id",
        "geometry_type",
        "obstacle_type",
        "level",
        "perturbation_type",
        "parameter_shift_cm",
        "motion_constraint",
        "image_path",
        "image_role",
        "reference_judgment",
    ]
    prompt_cols = [col for col in preferred_prompt_order if col in prompt_fieldnames]
    prompt_cols.extend(
        col
        for col in prompt_fieldnames
        if col not in prompt_cols and col not in {"prompt_text", "design_note", "target_model_key"}
    )
    return fixed_prefix + prompt_cols + fixed_suffix


def append_rows(path, rows, fieldnames):
    ensure_parent(path)
    file_exists = Path(path).exists()
    if file_exists and Path(path).stat().st_size > 0:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            existing_fieldnames = csv.reader(f).__next__()
        if existing_fieldnames != fieldnames:
            raise RuntimeError(
                "Output CSV header does not match the current schema. "
                "Use a new --out path, or move/delete the old output file first."
            )

    with open(path, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if not file_exists or Path(path).stat().st_size == 0:
            writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Collect LLM responses for wheelchair-turning prompts.")
    parser.add_argument("--prompts", default="data/prompt_matrix_seed.csv")
    parser.add_argument("--models", default="configs/models.json")
    parser.add_argument("--out", default="data/raw/responses.csv")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sleep", type=float, default=0.5)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Skip prompt-model pairs that already have enough complete successful rows.")
    parser.add_argument("--rerun-truncated", action="store_true", help="With --resume, treat finish_reason=length as incomplete and rerun it.")
    parser.add_argument("--disable-images", action="store_true", help="Do not send image_path images. Useful for local text-only models.")
    parser.add_argument(
        "--text-only-prefix",
        default="本轮是本地文本-only消融实验：不会向你发送图片。请只依据题面文字、尺寸和约束进行判断；如果题面提到照片或实地图，不要声称你看到了图片。",
        help="Prefix added to prompt_text when --disable-images is used. Use empty string to disable.",
    )
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop immediately when a model call fails. By default, failures are recorded and the batch continues.",
    )
    args = parser.parse_args()

    prompts, prompt_fieldnames = load_prompts(args.prompts)
    if args.limit:
        prompts = prompts[: args.limit]

    models = load_json(args.models)
    fieldnames = output_fieldnames(prompt_fieldnames)
    existing_complete_counts = load_existing_complete_counts(args.out, rerun_truncated=args.rerun_truncated) if args.resume else Counter()
    new_rows_written = 0
    skipped_rows = 0

    for repeat_index in range(args.repeat):
        for prompt in prompts:
            for model_config in models:
                target_model_key = prompt.get("target_model_key", "").strip()
                if target_model_key and model_config["model_key"] != target_model_key:
                    continue

                resume_key = (prompt["prompt_id"], model_config["model_key"])
                if args.resume and existing_complete_counts[resume_key] >= args.repeat:
                    skipped_rows += 1
                    print(
                        f"[skip] {prompt['prompt_id']} -> {model_config['model_key']} "
                        f"already has {existing_complete_counts[resume_key]} complete row(s)"
                    )
                    continue

                run_id = str(uuid.uuid4())
                print(
                    f"[{repeat_index + 1}/{args.repeat}] "
                    f"{prompt['prompt_id']} -> {model_config['model_key']}"
                )

                source_image_path = prompt.get("image_path", "").strip()
                model_disables_images = bool(model_config.get("disable_images", False))
                disable_images = args.disable_images or model_disables_images
                send_image_path = "" if disable_images else source_image_path
                input_modality = "text_only" if disable_images or not send_image_path else "image_text"

                prompt_text = prompt["prompt_text"]
                if disable_images and args.text_only_prefix:
                    prompt_text = args.text_only_prefix.strip() + "\n\n" + prompt_text

                if args.dry_run:
                    response_text = ""
                    raw_json = {}
                    request_status = "dry_run"
                    attempt_count = 0
                    http_status = ""
                    api_url = build_chat_completions_url(model_config)
                    error_message = ""
                else:
                    try:
                        response_text, raw_json, attempt_count, api_url = call_model(
                            model_config,
                            prompt_text,
                            image_path=send_image_path,
                        )
                        request_status = "ok"
                        http_status = 200
                        error_message = ""
                    except ApiCallError as exc:
                        if args.stop_on_error:
                            raise
                        response_text = ""
                        raw_json = {}
                        request_status = "error"
                        attempt_count = int(model_config.get("max_retries", 3)) + 1
                        http_status = exc.status_code or ""
                        api_url = exc.url or build_chat_completions_url(model_config)
                        error_message = compact_text(str(exc))
                        print(f"  recorded error and continued: {error_message}")
                    time.sleep(args.sleep)

                row = {
                    "run_id": run_id,
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "input_modality": input_modality,
                    "source_image_path": source_image_path,
                    "model_key": model_config["model_key"],
                    "provider": model_config.get("provider", "openai_compatible"),
                    "model": model_config["model"],
                    "temperature": model_config.get("temperature", 0),
                    "request_status": request_status,
                    "attempt_count": attempt_count,
                    "http_status": http_status,
                    "api_url": api_url,
                    "error_message": error_message,
                    "response_text": response_text,
                    "raw_json": json.dumps(raw_json, ensure_ascii=False),
                }
                row.update(prompt)
                if disable_images:
                    row["image_path"] = ""
                    row["image_role"] = "text_only_ablation"

                append_rows(args.out, [row], fieldnames)
                new_rows_written += 1

                if is_complete_ok(row, rerun_truncated=args.rerun_truncated):
                    existing_complete_counts[resume_key] += 1

                print(
                    f"  saved 1 row to {args.out} "
                    f"(status={request_status}, finish_reason={extract_finish_reason(raw_json)}, total_new={new_rows_written})"
                )

    print(f"Done. New rows written: {new_rows_written}. Skipped: {skipped_rows}. Output: {args.out}")


if __name__ == "__main__":
    main()
