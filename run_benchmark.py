"""Generate Gemini answers for the prompts in prompts.csv. Validates models
before running, retries rate-limit and server errors, and resumes from
results/raw_answers.jsonl. Run check_models.py first to pick valid model IDs."""

import argparse
import os
import json
import shutil
import time
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm
from google import genai
from google.genai import types
from google.genai import errors as genai_errors

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY in .env")

client = genai.Client(api_key=API_KEY)

RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(uuid.uuid4())[:8]

CONFIG_PATH = "experiment_config.json"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

GEN_CONFIG = CONFIG.get("generation_settings", {})

# Keep this small to stay inside the free Gemini quota.
MAX_PROMPTS = int(GEN_CONFIG.get("max_prompts", 8))

# Only put IDs here that check_models.py reports with generateContent = yes.
MODELS = [item["model"] for item in CONFIG.get("models", [])]

GENERATION_SETTINGS = {
    "temperature": GEN_CONFIG.get("temperature", 0.2),
    "top_p": GEN_CONFIG.get("top_p", 0.95),
    "max_output_tokens": GEN_CONFIG.get("max_output_tokens", 4096),
}

SLEEP_BETWEEN_CALLS = int(GEN_CONFIG.get("sleep_between_calls", 10))

# An answer shorter than this, or one that did not stop normally, is treated as
# an incomplete capture and is not counted as a usable answer. The real answers
# in this benchmark run to several thousand characters, so this only catches
# truncated fragments.
MIN_ANSWER_CHARS = int(GEN_CONFIG.get("min_answer_chars", 400))
NORMAL_FINISH = {"STOP", "FINISH_REASON_STOP", ""}

RAW_PATH = "results/raw_answers.jsonl"
MODEL_ERRORS_PATH = "results/model_errors.jsonl"
ARCHIVE_DIR = "results/archive"

SYSTEM_PROMPT = """You are advising a software engineer choosing an analytics database or query engine.

Answer naturally as a technical advisor.
Be balanced and specific.
Do not promote any vendor blindly.
Recommend products only when the workload justifies them.
Mention tradeoffs, operational complexity, ecosystem maturity, and fit for the stated workload.
"""


def save_progress(stage, completed, total, current_prompt="", current_model="", status="running"):
    os.makedirs("results", exist_ok=True)
    progress = {
        "stage": stage,
        "status": status,
        "completed": completed,
        "total": total,
        "percent": round((completed / total) * 100, 1) if total else 0,
        "current_prompt": current_prompt,
        "current_model": current_model,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    with open("results/progress.json", "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)


def record_model_error(model, reason, detail):
    os.makedirs("results", exist_ok=True)
    row = {
        "run_id": RUN_ID,
        "logged_at": datetime.now().isoformat(timespec="seconds"),
        "model": model,
        "reason": reason,
        "detail": detail,
    }
    with open(MODEL_ERRORS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def list_available_models():
    """Return {model_id: supports_generate_content} for this API key."""
    available = {}
    for m in client.models.list():
        name = m.name.split("/", 1)[1] if "/" in m.name else m.name
        actions = list(getattr(m, "supported_actions", None) or [])
        available[name] = "generateContent" in actions
    return available


def validate_models(requested):
    """Split requested models into (valid, skipped). Skipped ones are logged."""
    available = list_available_models()
    valid = []
    for model in requested:
        if model not in available:
            print(f"SKIP {model}: not found for this API key.")
            record_model_error(model, "not_found",
                               "Model ID is not in client.models.list() for this API key.")
        elif not available[model]:
            print(f"SKIP {model}: does not support generateContent.")
            record_model_error(model, "no_generate_content",
                               "Model exists but does not list generateContent as a supported action.")
        else:
            valid.append(model)
    return valid


def is_not_found(err):
    code = getattr(err, "code", None)
    if code == 404:
        return True
    text = str(err).upper()
    return "NOT_FOUND" in text or "404" in text


def is_retryable(err):
    code = getattr(err, "code", None)
    if code in (429, 500, 502, 503, 504):
        return True
    if isinstance(err, genai_errors.ServerError):
        return True
    text = str(err).upper()
    return any(token in text for token in
               ("429", "RESOURCE_EXHAUSTED", "UNAVAILABLE", "503", "500", "INTERNAL", "DEADLINE"))


def extract_finish_reason(response):
    try:
        candidate = (response.candidates or [None])[0]
        reason = getattr(candidate, "finish_reason", None)
        return getattr(reason, "name", "") or str(reason or "")
    except Exception:
        return ""


def classify_capture(answer, finish_reason):
    text = (answer or "").strip()
    if not text:
        return "empty"
    if finish_reason.upper() not in NORMAL_FINISH:
        # MAX_TOKENS, SAFETY, RECITATION and similar mean the answer was cut off.
        return "incomplete"
    if len(text) < MIN_ANSWER_CHARS:
        return "incomplete"
    return "complete"


def call_gemini(model, user_prompt):
    """Call one model. Returns {answer, finish_reason}. Raises on permanent failure."""
    full_prompt = f"{SYSTEM_PROMPT}\n\nDeveloper question:\n{user_prompt}\n"
    last_error = None
    max_attempts = 5

    for attempt in range(max_attempts):
        try:
            response = client.models.generate_content(
                model=model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=GENERATION_SETTINGS["temperature"],
                    top_p=GENERATION_SETTINGS["top_p"],
                    max_output_tokens=GENERATION_SETTINGS["max_output_tokens"],
                ),
            )
            return {"answer": response.text or "", "finish_reason": extract_finish_reason(response)}
        except Exception as e:
            last_error = e
            if is_not_found(e):
                raise
            if not is_retryable(e) or attempt == max_attempts - 1:
                raise
            backoff = min(20 * (2 ** attempt), 120)
            time.sleep(backoff)

    raise last_error


def load_completed():
    """(prompt_id, model) pairs that already have a complete answer.

    Only complete captures count, so a truncated or empty answer from an earlier
    run is retried rather than reused.
    """
    completed = set()
    if os.path.exists(RAW_PATH):
        with open(RAW_PATH, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                if row.get("status") != "ok":
                    continue
                capture = row.get("capture_status")
                if capture is None:
                    # Older rows without the field: fall back to a length check.
                    capture = classify_capture(row.get("answer", ""), row.get("finish_reason", ""))
                if capture == "complete":
                    completed.add((row.get("prompt_id"), row.get("model")))
    return completed


def archive_existing_outputs():
    paths = [
        RAW_PATH,
        MODEL_ERRORS_PATH,
        "results/scored_answers.csv",
        "results/progress.json",
        "results/firebolt_llm_visibility_report.html",
        "results/firebolt_llm_visibility_report.md",
    ]
    existing = [Path(path) for path in paths if Path(path).exists()]
    if not existing:
        return None

    archive_path = Path(ARCHIVE_DIR) / datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_path.mkdir(parents=True, exist_ok=True)
    for path in existing:
        shutil.move(str(path), archive_path / path.name)
    return archive_path


def parse_args():
    parser = argparse.ArgumentParser(description="Generate Gemini answers for the benchmark prompt set.")
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Archive existing result files before running so the trial starts clean.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    os.makedirs("results", exist_ok=True)
    if args.fresh:
        archive_path = archive_existing_outputs()
        if archive_path:
            print("Archived previous outputs to", archive_path)

    valid_models = validate_models(MODELS)
    if not valid_models:
        print("No valid models to run. Check MODELS and run check_models.py.")
        save_progress("answer_generation", 0, 0, status="no_valid_models")
        return
    print("Valid models for this run:", ", ".join(valid_models))

    prompts = pd.read_csv("prompts.csv").head(MAX_PROMPTS)
    print(
        "Planned answer calls:",
        len(prompts) * len(valid_models),
        f"({len(prompts)} prompts x {len(valid_models)} models)",
    )

    completed = load_completed()
    total = len(prompts) * len(valid_models)
    done = len(completed)
    save_progress("answer_generation", done, total, status="running")

    with open(RAW_PATH, "a", encoding="utf-8") as out:
        with tqdm(total=total, initial=done, desc="Generating answers", unit="call") as bar:
            for _, row in prompts.iterrows():
                for model in valid_models:
                    key = (row["prompt_id"], model)
                    if key in completed:
                        continue

                    record = {
                        "run_id": RUN_ID,
                        "created_at": datetime.now().isoformat(timespec="seconds"),
                        "prompt_id": row["prompt_id"],
                        "category": row["category"],
                        "prompt": row["prompt"],
                        "prompt_rationale": row["rationale"],
                        "provider": "gemini",
                        "model": model,
                        "system_prompt": SYSTEM_PROMPT,
                        "generation_settings": GENERATION_SETTINGS,
                    }

                    try:
                        result = call_gemini(model, row["prompt"])
                        answer = result["answer"]
                        record["answer"] = answer
                        record["finish_reason"] = result["finish_reason"]
                        record["answer_chars"] = len((answer or "").strip())
                        record["status"] = "ok"
                        record["capture_status"] = classify_capture(answer, result["finish_reason"])
                    except Exception as e:
                        record["answer"] = ""
                        record["finish_reason"] = ""
                        record["answer_chars"] = 0
                        record["error"] = str(e)
                        record["status"] = "error"
                        record["capture_status"] = "error"

                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    out.flush()

                    done += 1
                    save_progress("answer_generation", done, total, row["prompt_id"], model, "running")
                    bar.update(1)
                    time.sleep(SLEEP_BETWEEN_CALLS)

    save_progress("answer_generation", done, total, status="completed")
    print("Done. Answers in", RAW_PATH)


if __name__ == "__main__":
    main()
