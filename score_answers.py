import os
import re
import json
import time
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from tqdm import tqdm
from google import genai
from google.genai import types

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY in .env")

client = genai.Client(api_key=API_KEY)

CONFIG_PATH = "experiment_config.json"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

JUDGE_CONFIG = CONFIG.get("judge_settings", {})
JUDGE_MODEL = JUDGE_CONFIG.get("model", "gemini-3.1-flash-lite")

JUDGE_SETTINGS = {
    "temperature": JUDGE_CONFIG.get("temperature", 0.0),
    "max_output_tokens": JUDGE_CONFIG.get("max_output_tokens", 900),
    "sleep_between_calls": JUDGE_CONFIG.get("sleep_between_calls", 8),
}

GEN_CONFIG = CONFIG.get("generation_settings", {})
MIN_ANSWER_CHARS = int(GEN_CONFIG.get("min_answer_chars", 400))
NORMAL_FINISH = {"STOP", "FINISH_REASON_STOP", ""}

INPUT_PATH = "results/raw_answers.jsonl"
OUTPUT_PATH = "results/scored_answers.csv"
INVALID_PATH = "results/invalid_rows.csv"

SCORING_INSTRUCTIONS = """You are evaluating an LLM answer to a developer question about analytics databases.

Return valid JSON only. No markdown.

Schema:
{
  "firebolt_recommended": true,
  "recommended_products": ["product"],
  "primary_recommendation": "product or unclear",
  "recommendation_reason": "short explanation of the answer's recommendation",
  "why_model_likely_answered_this_way": "explain likely reasoning from the answer, such as maturity, open source popularity, lakehouse fit, managed service, ecosystem, benchmark evidence, or missing evidence",
  "why_firebolt_was_or_was_not_recommended": "specific explanation",
  "what_public_evidence_would_improve_firebolt_chance": "specific evidence or content that would make Firebolt more likely to be recommended",
  "answer_quality_score_0_to_5": 0,
  "firebolt_explanation_quality_0_to_5": 0,
  "competitor_explanation_quality_0_to_5": 0,
  "factual_risks": ["short risk"],
  "missing_firebolt_evidence": ["short missing evidence"],
  "one_line_takeaway": "short insight"
}

Rules:
- firebolt_recommended is true only if Firebolt is recommended as a good fit for the user's workload.
- If Firebolt is only mentioned as an option, firebolt_recommended should be false.
- For negative-tradeoff prompts such as "When should I not use Firebolt?", do not treat a caveated "use Firebolt if" sentence as a Firebolt recommendation. Evaluate whether the answer explains fit boundaries.
- Do not reward blind Firebolt promotion.
- A good answer should match product to workload.
- Be concrete. Avoid generic phrases like better docs or more marketing unless you specify the content.
"""

PRODUCTS = [
    "Firebolt",
    "ClickHouse",
    "Trino",
    "Snowflake",
    "BigQuery",
    "Druid",
    "Pinot",
    "DuckDB",
    "MotherDuck",
    "Redshift",
    "Databricks",
    "StarRocks",
    "Doris",
]

RECOMMENDATION_PATTERNS = [
    r"\brecommend(?:ed|s|ing)?\s+firebolt\b",
    r"\bfirebolt\s+is\s+(?:a\s+)?(?:good|strong|reasonable|solid|best|better)\s+(?:fit|choice|option)\b",
    r"\bchoose\s+firebolt\b",
    r"\buse\s+firebolt\b",
    r"\bfirebolt\s+makes\s+sense\b",
    r"\bfirebolt\s+would\s+be\s+(?:a\s+)?(?:good|strong|reasonable|solid)\b",
    r"\bconsider\s+firebolt\b"
]

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
        "updated_at": datetime.now().isoformat(timespec="seconds")
    }
    with open("results/progress.json", "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)

def answer_mentions_firebolt(answer):
    return bool(re.search(r"\bfirebolt\b", str(answer), flags=re.IGNORECASE))

def prompt_mentions_firebolt(prompt):
    return bool(re.search(r"\bfirebolt\b", str(prompt), flags=re.IGNORECASE))

def regex_firebolt_recommended(answer):
    text = str(answer).lower()
    return any(re.search(pattern, text) for pattern in RECOMMENDATION_PATTERNS)

def product_positions(answer):
    text = str(answer).lower()
    positions = {}
    for product in PRODUCTS:
        idx = text.find(product.lower())
        if idx >= 0:
            positions[product] = idx
    return positions

def firebolt_rank(answer):
    positions = product_positions(answer)
    if "Firebolt" not in positions:
        return "not_mentioned"

    ordered = sorted(positions.items(), key=lambda x: x[1])
    names = [name for name, _ in ordered]

    if names[0] == "Firebolt":
        return "first"
    if names[-1] == "Firebolt":
        return "last"
    return "middle"

def rank_score(rank):
    return {
        "first": 3,
        "middle": 2,
        "last": 1,
        "not_mentioned": 0,
    }.get(rank, 0)

def extract_json(text):
    text = str(text).strip()
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No JSON object found")

    parsed = json.loads(text[start:end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("Judge JSON was not an object")
    return parsed

def judge_explanation(prompt, answer):
    judge_prompt = f"""{SCORING_INSTRUCTIONS}

Developer question:
{prompt}

Model answer:
{answer}
"""
    last_error = None

    for attempt in range(4):
        try:
            response = client.models.generate_content(
                model=JUDGE_MODEL,
                contents=judge_prompt,
                config=types.GenerateContentConfig(
                    temperature=JUDGE_SETTINGS["temperature"],
                    max_output_tokens=JUDGE_SETTINGS["max_output_tokens"],
                ),
            )
            return extract_json(response.text or "")
        except Exception as e:
            last_error = e
            time.sleep(15 * (attempt + 1))

    raise last_error

def excerpt(text, n=700):
    text = " ".join(str(text).split())
    if len(text) <= n:
        return text
    return text[:n].rstrip() + "..."

def recommendation_metric_applies(category):
    return str(category).lower() != "negative_tradeoff"


def infer_content_gap(category, prompt, firebolt_in_prompt, firebolt_mentioned, firebolt_recommended):
    if not recommendation_metric_applies(category):
        return "Performing well" if firebolt_mentioned else "Boundary prompt failure"

    p = str(prompt).lower()

    if firebolt_in_prompt and not firebolt_mentioned:
        return "Firebolt ignored despite being named"

    if not firebolt_mentioned:
        if any(x in p for x in ["best", "alternative", "options"]):
            return "Category discovery gap"
        if any(x in p for x in ["iceberg", "s3", "parquet", "lakehouse"]):
            return "Lakehouse and Iceberg positioning gap"
        if any(x in p for x in ["dashboard", "embedded", "customer-facing", "latency", "concurrency"]):
            return "Customer-facing analytics positioning gap"
        return "General awareness gap"

    if firebolt_mentioned and not firebolt_recommended:
        if "clickhouse" in p:
            return "ClickHouse comparison confidence gap"
        if "trino" in p:
            return "Trino migration positioning gap"
        if "snowflake" in p:
            return "Snowflake comparison positioning gap"
        if any(x in p for x in ["iceberg", "s3", "parquet", "lakehouse"]):
            return "Lakehouse evidence gap"
        return "Mentioned but not recommended"

    return "Performing well"

def load_raw(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def select_target_run(rows):
    """Pick one run_id to score: the run with the most rows, latest if tied."""
    from collections import Counter
    counts = Counter(r.get("run_id", "") for r in rows)
    if not counts:
        return ""
    return sorted(counts.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)[0][0]


def completeness(row):
    """Return (is_complete, reason). Uses capture_status when run_benchmark
    recorded it, otherwise falls back to answer length and finish reason."""
    cap = row.get("capture_status")
    if cap is not None:
        return cap == "complete", cap
    answer = str(row.get("answer", "")).strip()
    finish = str(row.get("finish_reason", "") or "")
    if not answer:
        return False, "empty"
    if finish.upper() not in NORMAL_FINISH:
        return False, "incomplete"
    if len(answer) < MIN_ANSWER_CHARS:
        return False, "incomplete"
    return True, "complete"


def split_valid_invalid(all_rows, target_run):
    valid, invalid = [], []
    for row in all_rows:
        rid = row.get("run_id", "")
        if rid != target_run:
            invalid.append({**row, "invalid_reason": "other_run_id"})
            continue
        if row.get("status") != "ok":
            invalid.append({**row, "invalid_reason": "api_error"})
            continue
        ok, reason = completeness(row)
        if not ok:
            invalid.append({**row, "invalid_reason": reason})
            continue
        valid.append(row)
    return valid, invalid


def write_invalid_rows(invalid):
    cols = ["run_id", "prompt_id", "model", "status", "capture_status",
            "finish_reason", "answer_chars", "invalid_reason", "answer_excerpt"]
    records = []
    for row in invalid:
        answer = str(row.get("answer", ""))
        records.append({
            "run_id": row.get("run_id", ""),
            "prompt_id": row.get("prompt_id", ""),
            "model": row.get("model", ""),
            "status": row.get("status", ""),
            "capture_status": row.get("capture_status", ""),
            "finish_reason": row.get("finish_reason", ""),
            "answer_chars": row.get("answer_chars", len(answer.strip())),
            "invalid_reason": row.get("invalid_reason", ""),
            "answer_excerpt": excerpt(answer, 200) if answer.strip() else "",
        })
    pd.DataFrame(records, columns=cols).to_csv(INVALID_PATH, index=False)


def main():
    input_path = INPUT_PATH
    output_path = OUTPUT_PATH

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"{input_path} not found. Run run_benchmark.py first.")

    all_rows = load_raw(input_path)
    run_ids = sorted({r.get("run_id", "") for r in all_rows})
    target_run = os.getenv("BENCHMARK_RUN_ID") or select_target_run(all_rows)
    if len(run_ids) > 1:
        print(f"WARNING: raw answers contain {len(run_ids)} run ids {run_ids}.")
        print(f"Scoring only run {target_run} to keep the dataset isolated.")

    valid, invalid = split_valid_invalid(all_rows, target_run)
    write_invalid_rows(invalid)

    print(f"Run {target_run}: {len(valid)} valid answers, {len(invalid)} quarantined "
          f"(see {INVALID_PATH}).")

    rows = valid
    total = len(rows)
    if total == 0:
        print("No valid answers to score for run", target_run)
        save_progress("scoring", 0, 0, status="no_rows")
        pd.DataFrame([]).to_csv(output_path, index=False)
        return

    print(f"Scoring {total} answers with judge model {JUDGE_MODEL}.")
    save_progress("scoring", 0, total, status="running")

    scored_rows = []

    with tqdm(total=total, desc="Scoring answers", unit="answer") as bar:
        for idx, row in enumerate(rows, start=1):
            prompt = row["prompt"]
            answer = row["answer"]
            model = row.get("model", "")
            prompt_id = row.get("prompt_id", "")
            category = row.get("category", "")

            firebolt_in_prompt = prompt_mentions_firebolt(prompt)
            firebolt_mentioned = answer_mentions_firebolt(answer)
            regex_recommended = regex_firebolt_recommended(answer)
            recommendation_applicable = recommendation_metric_applies(category)
            fb_rank = firebolt_rank(answer)

            judge_error = ""
            try:
                judged = judge_explanation(prompt, answer)
                judge_status = "ok"
            except Exception as e:
                judged = {
                    "firebolt_recommended": regex_recommended,
                    "recommended_products": [],
                    "primary_recommendation": "",
                    "recommendation_reason": "",
                    "why_model_likely_answered_this_way": "Judge model did not return usable JSON for this row.",
                    "why_firebolt_was_or_was_not_recommended": "",
                    "what_public_evidence_would_improve_firebolt_chance": "",
                    "answer_quality_score_0_to_5": 0,
                    "firebolt_explanation_quality_0_to_5": 0,
                    "competitor_explanation_quality_0_to_5": 0,
                    "factual_risks": [],
                    "missing_firebolt_evidence": [],
                    "one_line_takeaway": "",
                }
                judge_status = "error"
                judge_error = str(e)

            judged_firebolt_recommended = bool(judged.get("firebolt_recommended", False))
            firebolt_recommended = regex_recommended and recommendation_applicable

            factual_risks = judged.get("factual_risks", [])
            if not isinstance(factual_risks, list):
                factual_risks = [str(factual_risks)]

            missing_evidence = judged.get("missing_firebolt_evidence", [])
            if not isinstance(missing_evidence, list):
                missing_evidence = [str(missing_evidence)]

            factual_penalty = min(len(factual_risks), 3)

            visibility_score = (
                2 * int(firebolt_mentioned)
                + 3 * int(firebolt_recommended)
                + rank_score(fb_rank)
                + int(judged.get("firebolt_explanation_quality_0_to_5", 0))
                - factual_penalty
            )

            scored_rows.append({
                **row,
                "firebolt_in_prompt": firebolt_in_prompt,
                "firebolt_mentioned": firebolt_mentioned,
                "firebolt_recommended": firebolt_recommended,
                "regex_firebolt_recommended": regex_recommended,
                "judge_firebolt_recommended": judged_firebolt_recommended,
                "recommendation_metric_applicable": recommendation_applicable,
                "firebolt_rank": fb_rank,
                "visibility_score": visibility_score,
                "content_gap": infer_content_gap(category, prompt, firebolt_in_prompt, firebolt_mentioned, firebolt_recommended),
                "answer_excerpt": excerpt(answer),
                "judge_status": judge_status,
                "judge_error": judge_error,
                "recommended_products": " | ".join(judged.get("recommended_products", [])) if isinstance(judged.get("recommended_products", []), list) else str(judged.get("recommended_products", "")),
                "primary_recommendation": judged.get("primary_recommendation", ""),
                "recommendation_reason": judged.get("recommendation_reason", ""),
                "why_model_likely_answered_this_way": judged.get("why_model_likely_answered_this_way", ""),
                "why_firebolt_was_or_was_not_recommended": judged.get("why_firebolt_was_or_was_not_recommended", ""),
                "what_public_evidence_would_improve_firebolt_chance": judged.get("what_public_evidence_would_improve_firebolt_chance", ""),
                "answer_quality_score_0_to_5": judged.get("answer_quality_score_0_to_5", 0),
                "firebolt_explanation_quality_0_to_5": judged.get("firebolt_explanation_quality_0_to_5", 0),
                "competitor_explanation_quality_0_to_5": judged.get("competitor_explanation_quality_0_to_5", 0),
                "factual_risks": " | ".join(factual_risks),
                "missing_firebolt_evidence": " | ".join(missing_evidence),
                "one_line_takeaway": judged.get("one_line_takeaway", ""),
            })

            save_progress("scoring", idx, total, prompt_id, model, "running")
            bar.update(1)
            time.sleep(JUDGE_SETTINGS["sleep_between_calls"])

    pd.DataFrame(scored_rows).to_csv(output_path, index=False)
    save_progress("scoring", total, total, status="completed")

if __name__ == "__main__":
    main()
