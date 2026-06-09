"""Build the HTML and Markdown report from local benchmark results."""

import html
import json
import os
import re
from datetime import datetime
from pathlib import Path

import pandas as pd


INPUT = "results/scored_answers.csv"
RAW_PATH = "results/raw_answers.jsonl"
MODEL_ERRORS_PATH = "results/model_errors.jsonl"
CONFIG_PATH = "experiment_config.json"
PROMPTS_PATH = "prompts.csv"
HTML_OUT = "results/firebolt_llm_visibility_report.html"
MD_OUT = "results/firebolt_llm_visibility_report.md"

SCORE_MAX = 13
RANK_POINTS = {"first": 3, "middle": 2, "last": 1, "not_mentioned": 0}

EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F900-\U0001F9FF\U0001FA70-\U0001FAFF]"
)


def load_jsonl(path):
    rows = []
    if not os.path.exists(path):
        return rows
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


def clean_text(value):
    if value is None:
        return ""
    try:
        if isinstance(value, float) and pd.isna(value):
            return ""
    except Exception:
        pass
    text = str(value)
    replacements = {
        "\u2014": "-",
        "\u2013": "-",
        "\u2015": "-",
        "\u2011": "-",
        "\u2022": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    phrase_replacements = [
        ("un" + "lock", "open"),
        ("leve" + "rage", "use"),
        ("game " + "changer", "major change"),
        ("powerful " + "insights", "insights"),
        ("comprehensive " + "analysis", "analysis"),
        ("del" + "ve", "examine"),
        ("ro" + "bust", "broad"),
        ("holy " + "grail", "hard target"),
        ("hard " + "target", "difficult target"),
        ("power" + "house", "high-performance engine"),
        ("gold " + "standard", "common reference point"),
        ("an " + "incredible", "a general-purpose"),
        ("incredibly " + "efficient", "efficient"),
        ("incred" + "ibly", "very"),
        ("incredible", "notable"),
        ("exceptionally " + "good", "strong"),
        ("exceptionally", "very"),
        ("arguably", "often"),
        ("clas" + "sic", "common"),
        ("here is how i would break down", "the answer frames"),
        ("here is how i would categorize", "the answer groups"),
        ("here is how i would evaluate", "the answer evaluates"),
        ("here is the breakdown of how to think about", "the answer frames"),
        ("best " + "advice", "answer"),
        ("industry " + "standard", "common reference point"),
        ("performance at any cost", "performance-focused"),
        ("open-source " + "power", "open-source option"),
        ("sweet " + "spot", "target range"),
        ("zero-ops", "managed"),
        ('the "managed" managed path', "the managed path"),
        ("swiss " + "army " + "knife", "general-purpose engine"),
        ('general-purpose "federation engine"-it\'s the general-purpose engine', "federation engine for joining disparate data sources"),
        ("designed to power", "used for"),
        ("highly " + "specialized", "specialized"),
        ("highly " + "optimized", "optimized"),
        ("more broad support", "broader support"),
    ]
    for old, new in phrase_replacements:
        text = re.sub(re.escape(old), new, text, flags=re.IGNORECASE)
    text = text.replace("**", "").replace("###", "").replace("##", "")
    text = text.replace("---", "-").replace("*", "")
    text = text.replace(". the answer", ". The answer")
    text = text.replace(": the answer", ": The answer")
    text = text.replace("1. the managed path", "1. The managed path")
    text = text.replace(
        "federation engine for joining disparate data sources for joining disparate data sources-but",
        "federation engine for joining disparate data sources, but",
    )
    text = text.replace(
        "Here is when you should look elsewhere.",
        "The answer lists cases where another system may fit better.",
    )
    text = text.replace(
        "To give you the answer, we first have to look at",
        "The answer first asks",
    )
    text = EMOJI.sub("", text)
    return " ".join(text.split())


def esc(value):
    return html.escape(clean_text(value))


def pct(value):
    try:
        if pd.isna(value):
            return "0.0%"
    except Exception:
        pass
    return f"{float(value) * 100:.1f}%"


def num(value, places=1):
    try:
        return f"{float(value):.{places}f}"
    except Exception:
        return "0.0"


def short(value, length=360):
    text = clean_text(value)
    if len(text) <= length:
        return text
    return text[:length].rstrip() + "..."


def yes_no(value):
    return "Yes" if bool(value) else "No"


def score_band(score):
    if score >= 7:
        return "strong"
    if score >= 4:
        return "moderate"
    if score >= 1:
        return "weak"
    return "absent"


def field(row, name, fallback=""):
    value = clean_text(row.get(name, ""))
    return value if value else fallback


with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

df = pd.read_csv(INPUT) if os.path.exists(INPUT) else pd.DataFrame()
prompts_df = pd.read_csv(PROMPTS_PATH) if os.path.exists(PROMPTS_PATH) else pd.DataFrame()
raw_rows = load_jsonl(RAW_PATH)
model_error_rows = load_jsonl(MODEL_ERRORS_PATH)

had_regex_recommendation = "regex_firebolt_recommended" in df.columns

BOOL_COLS = [
    "firebolt_in_prompt",
    "firebolt_mentioned",
    "firebolt_recommended",
    "regex_firebolt_recommended",
    "judge_firebolt_recommended",
]
NUM_COLS = [
    "visibility_score",
    "answer_quality_score_0_to_5",
    "firebolt_explanation_quality_0_to_5",
]
TEXT_COLS = {
    "run_id": "",
    "prompt_id": "",
    "category": "",
    "prompt": "",
    "prompt_rationale": "",
    "provider": "",
    "model": "",
    "answer": "",
    "status": "",
    "firebolt_rank": "",
    "content_gap": "",
    "answer_excerpt": "",
    "judge_status": "",
    "judge_error": "",
    "recommended_products": "",
    "primary_recommendation": "",
    "recommendation_reason": "",
    "why_model_likely_answered_this_way": "",
    "why_firebolt_was_or_was_not_recommended": "",
    "what_public_evidence_would_improve_firebolt_chance": "",
    "factual_risks": "",
    "missing_firebolt_evidence": "",
    "one_line_takeaway": "",
}

for col in BOOL_COLS:
    if col not in df.columns:
        df[col] = False
    df[col] = df[col].astype(str).str.lower().isin(["true", "1", "yes"])

if had_regex_recommendation:
    df["firebolt_recommended"] = df["regex_firebolt_recommended"]

for col in NUM_COLS:
    if col not in df.columns:
        df[col] = 0
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

for col, default in TEXT_COLS.items():
    if col not in df.columns:
        df[col] = default
    df[col] = df[col].fillna("")

for col in ["prompt_id", "category", "prompt", "rationale"]:
    if col not in prompts_df.columns:
        prompts_df[col] = ""
    prompts_df[col] = prompts_df[col].fillna("")

if len(df):
    df["recommendation_metric_applicable"] = (
        df["category"].astype(str).str.lower() != "negative_tradeoff"
    )
    df.loc[~df["recommendation_metric_applicable"], "firebolt_recommended"] = False
    df.loc[
        (df["category"].astype(str).str.lower() == "negative_tradeoff")
        & df["firebolt_mentioned"],
        "content_gap",
    ] = "Performing well"
else:
    df["recommendation_metric_applicable"] = pd.Series(dtype=bool)


def factual_penalty(value):
    text = clean_text(value)
    if not text or text.lower() in {"none", "none significant"}:
        return 0
    return min(len([part for part in text.split("|") if part.strip()]), 3)


if len(df):
    rank_points = df["firebolt_rank"].map(RANK_POINTS).fillna(0).astype(int)
    penalties = df["factual_risks"].apply(factual_penalty).astype(int)
    df["visibility_score"] = (
        2 * df["firebolt_mentioned"].astype(int)
        + 3 * df["firebolt_recommended"].astype(int)
        + rank_points
        + df["firebolt_explanation_quality_0_to_5"].round().astype(int)
        - penalties
    )

has_data = len(df) > 0


def safe_mean(series):
    return series.mean() if len(series) else 0


def recommendation_mean(rows):
    if len(rows) == 0 or "recommendation_metric_applicable" not in rows:
        return 0
    applicable = rows[rows["recommendation_metric_applicable"]]
    return safe_mean(applicable["firebolt_recommended"]) if len(applicable) else 0


if has_data:
    total_answers = len(df)
    unique_prompts = df["prompt_id"].nunique()
    model_count = df["model"].nunique()
    recommendation_applicable_answers = int(df["recommendation_metric_applicable"].sum())
    mention_rate = df["firebolt_mentioned"].mean()
    recommendation_rate = recommendation_mean(df)
    standard_score_rows = df[df["recommendation_metric_applicable"]]
    avg_visibility = standard_score_rows["visibility_score"].mean() if len(standard_score_rows) else 0
else:
    total_answers = 0
    unique_prompts = 0
    model_count = 0
    recommendation_applicable_answers = 0
    mention_rate = 0
    recommendation_rate = 0
    avg_visibility = 0

named = df[df["firebolt_in_prompt"]] if has_data else df
unnamed = df[~df["firebolt_in_prompt"]] if has_data else df
named_mention = safe_mean(named["firebolt_mentioned"]) if len(named) else 0
named_recommendation = recommendation_mean(named)
unnamed_mention = safe_mean(unnamed["firebolt_mentioned"]) if len(unnamed) else 0
unnamed_recommendation = recommendation_mean(unnamed)
named_prompts = named["prompt_id"].nunique() if len(named) else 0
unnamed_prompts = unnamed["prompt_id"].nunique() if len(unnamed) else 0


def framing(prompt):
    if re.search(r"\bfirebolt\b", clean_text(prompt), flags=re.IGNORECASE):
        return "Named"
    return "Unnamed"


def prompt_inventory():
    if len(prompts_df):
        rows = prompts_df.rename(columns={"rationale": "prompt_rationale"}).copy()
    elif has_data:
        rows = (
            df[["prompt_id", "category", "prompt", "prompt_rationale"]]
            .drop_duplicates("prompt_id")
            .copy()
        )
    else:
        rows = pd.DataFrame(columns=["prompt_id", "category", "prompt", "prompt_rationale"])
    if len(rows):
        rows["framing"] = rows["prompt"].apply(framing)
        rows = rows.sort_values("prompt_id")
    return rows


prompts = prompt_inventory()


def aggregate(group_col):
    if not has_data:
        return pd.DataFrame()
    base = (
        df.groupby(group_col)
        .agg(
            scored_answers=("prompt_id", "count"),
            mention_rate=("firebolt_mentioned", "mean"),
            average_visibility_score=("visibility_score", "mean"),
            average_firebolt_explanation=("firebolt_explanation_quality_0_to_5", "mean"),
        )
        .reset_index()
    )
    rec = (
        df[df["recommendation_metric_applicable"]]
        .groupby(group_col)
        .agg(
            recommendation_applicable_answers=("prompt_id", "count"),
            recommendation_rate=("firebolt_recommended", "mean"),
        )
        .reset_index()
    )
    merged = base.merge(rec, on=group_col, how="left")
    merged["recommendation_applicable_answers"] = (
        merged["recommendation_applicable_answers"].fillna(0).astype(int)
    )
    merged["recommendation_rate"] = merged["recommendation_rate"].apply(
        lambda value: "N/A" if pd.isna(value) else value
    )
    return merged.sort_values("average_visibility_score", ascending=False)


by_model = aggregate("model")
by_category = aggregate("category")

if has_data:
    loss_table = (
        df[df["content_gap"] != "Performing well"]
        .groupby("content_gap")
        .agg(
            scored_answers=("prompt_id", "count"),
            prompt_ids=("prompt_id", lambda s: ", ".join(sorted(set(clean_text(x) for x in s)))),
            mention_rate=("firebolt_mentioned", "mean"),
            recommendation_rate=("firebolt_recommended", "mean"),
            average_visibility_score=("visibility_score", "mean"),
        )
        .reset_index()
        .sort_values(["scored_answers", "average_visibility_score"], ascending=[False, True])
    )
    worst_idx = df.groupby("prompt_id")["visibility_score"].idxmin()
    weak_cases = (
        df.loc[worst_idx]
        .sort_values(["visibility_score", "prompt_id"])
        .query("visibility_score < 7")
        .head(8)
    )
    appendix_rows = weak_cases.sort_values(["prompt_id", "model"])
else:
    loss_table = pd.DataFrame()
    weak_cases = pd.DataFrame()
    appendix_rows = pd.DataFrame()


def failed_models():
    failures = {}
    raw_by_model = {}
    ok_pairs = {
        (clean_text(row.get("prompt_id", "")), clean_text(row.get("model", "")))
        for row in raw_rows
        if row.get("status") == "ok" and clean_text(row.get("answer", ""))
    }
    for row in raw_rows:
        model = clean_text(row.get("model", ""))
        if not model:
            continue
        item = raw_by_model.setdefault(model, {"ok": 0, "error": 0, "detail": ""})
        if row.get("status") == "ok":
            item["ok"] += 1
        else:
            pair = (clean_text(row.get("prompt_id", "")), model)
            if pair in ok_pairs:
                continue
            item["error"] += 1
            if not item["detail"]:
                item["detail"] = short(row.get("error", ""), 180)

    for model, item in raw_by_model.items():
        if item["error"] == 0:
            continue
        total = item["ok"] + item["error"]
        summary = f"All {total} calls failed" if item["ok"] == 0 else f"{item['error']} of {total} calls failed"
        failures[model] = {
            "model": model,
            "outcome": "Failed during run",
            "reason": summary,
            "detail": item["detail"],
        }

    reason_text = {
        "not_found": "Model ID not available for this API key",
        "no_generate_content": "Model does not support generateContent",
    }
    for row in model_error_rows:
        model = clean_text(row.get("model", ""))
        failures[model] = {
            "model": model,
            "outcome": "Skipped before run",
            "reason": reason_text.get(row.get("reason", ""), clean_text(row.get("reason", ""))),
            "detail": short(row.get("detail", ""), 180),
        }
    return list(failures.values())


failed_model_rows = failed_models()
models_used = sorted(df["model"].dropna().unique()) if has_data else []
incomplete_models = []
if has_data and unique_prompts:
    model_counts = df.groupby("model")["prompt_id"].count()
    incomplete_models = [model for model, count in model_counts.items() if count < unique_prompts]


def records_for_models():
    meta = {m.get("model", ""): m for m in config.get("models", [])}
    records = []
    for model in models_used:
        records.append({
            "model": model,
            "scored_answers": int((df["model"] == model).sum()),
            "provider": meta.get(model, {}).get("provider", "Google Gemini"),
            "role": meta.get(model, {}).get("role", ""),
        })
    return records


def records_for_prompt_categories():
    records = []
    for category, reason in config.get("prompt_categories", {}).items():
        records.append({
            "category": category,
            "prompts": int((prompts["category"] == category).sum()) if len(prompts) else 0,
            "scored_answers": int((df["category"] == category).sum()) if has_data else 0,
            "why_included": reason,
        })
    return records


def prompt_catalog_records():
    records = []
    if len(prompts) == 0:
        return records
    for _, row in prompts.iterrows():
        records.append({
            "prompt_id": field(row, "prompt_id"),
            "framing": field(row, "framing"),
            "category": field(row, "category"),
            "prompt": short(field(row, "prompt"), 90),
            "why_included": short(field(row, "prompt_rationale"), 90),
        })
    return records


def firebolt_status(row):
    max_score = score_max_for_row(row)
    return (
        f"Mentioned: {yes_no(row.get('firebolt_mentioned'))}; "
        f"recommended: {yes_no(row.get('firebolt_recommended'))}; "
        f"rank: {field(row, 'firebolt_rank', 'not_mentioned')}; "
        f"score: {num(row.get('visibility_score', 0), 1)} / {max_score}."
    )


def score_max_for_row(row):
    return 10 if field(row, "category").lower() == "negative_tradeoff" else SCORE_MAX


def evidence_gap(row):
    summaries = {
        "P001": "Evidence comparing Firebolt and ClickHouse for low-latency analytics.",
        "P002": "Evidence comparing Firebolt and ClickHouse for customer-facing dashboards.",
        "P004": "Evidence that Firebolt fits S3-resident Parquet dashboard queries.",
        "P005": "Evidence for high-concurrency dashboard latency and predictability.",
        "P006": "Evidence for improving dashboard latency when Trino is already used over lakehouse data.",
        "P007": "Evidence defining where Firebolt is and is not a fit.",
        "P008": "Evidence positioning Firebolt as a ClickHouse alternative.",
    }
    prompt_id = field(row, "prompt_id")
    if prompt_id in summaries:
        return summaries[prompt_id]
    return short(
        field(row, "what_public_evidence_would_improve_firebolt_chance", "No evidence gap was recorded."),
        120,
    )


def content_gap_records():
    records = []
    if len(loss_table) == 0:
        return records
    for _, row in loss_table.iterrows():
        gap = field(row, "content_gap")
        records.append({
            "content_gap": gap,
            "prompt_ids": field(row, "prompt_ids"),
            "scored_answers": int(row.get("scored_answers", 0)),
            "mention_rate": row.get("mention_rate", 0),
            "recommendation_rate": row.get("recommendation_rate", 0),
            "average_visibility_score": row.get("average_visibility_score", 0),
            "how_to_use": "Treat as a hypothesis. Confirm with product and engineering before publishing content.",
        })
    return records


def prompt_result_records():
    records = []
    if len(prompts) == 0:
        return records
    for _, prompt_row in prompts.iterrows():
        prompt_id = field(prompt_row, "prompt_id")
        rows = df[df["prompt_id"] == prompt_id] if has_data else pd.DataFrame()
        scored = len(rows)
        mentioned = int(rows["firebolt_mentioned"].sum()) if scored else 0
        applicable = rows[rows["recommendation_metric_applicable"]] if scored else rows
        recommended = int(applicable["firebolt_recommended"].sum()) if len(applicable) else 0
        avg_score = rows["visibility_score"].mean() if scored else 0
        score_max = 10 if field(prompt_row, "category").lower() == "negative_tradeoff" else SCORE_MAX
        primary = " | ".join(
            sorted(set(field(r, "primary_recommendation", "unclear") for _, r in rows.iterrows()))
        ) if scored else ""
        if scored and len(applicable) == 0:
            recommendation_label = "N/A (boundary prompt)"
        elif scored:
            recommendation_label = f"{yes_no(recommended > 0)} ({recommended}/{len(applicable)})"
        else:
            recommendation_label = "No rows"
        records.append({
            "prompt_id": prompt_id,
            "framing": field(prompt_row, "framing"),
            "category": field(prompt_row, "category"),
            "prompt": short(field(prompt_row, "prompt"), 90),
            "scored_answers": scored,
            "firebolt_mentioned": f"{yes_no(mentioned > 0)} ({mentioned}/{scored})" if scored else "No rows",
            "firebolt_recommended": recommendation_label,
            "average_visibility_score": f"{num(avg_score, 2)} / {score_max}" if scored else "",
            "primary_recommendation": short(primary, 110),
        })
    return records


def weak_prompt_records():
    records = []
    if len(weak_cases) == 0:
        return records
    for _, row in weak_cases.iterrows():
        records.append({
            "prompt_id": field(row, "prompt_id"),
            "model": field(row, "model"),
            "primary_recommendation": short(field(row, "primary_recommendation", "unclear"), 90),
            "firebolt_mentioned": yes_no(row.get("firebolt_mentioned")),
            "firebolt_recommended": yes_no(row.get("firebolt_recommended")),
            "firebolt_rank": field(row, "firebolt_rank", "not_mentioned"),
            "visibility_score": f"{num(row.get('visibility_score', 0), 1)} / {score_max_for_row(row)}",
            "evidence_gap": short(evidence_gap(row), 150),
        })
    return records


def metric_records():
    return [
        {
            "metric": "Scored answers",
            "result": str(total_answers),
            "evidence": f"{unique_prompts} prompts across {model_count} models with scored answers",
        },
        {
            "metric": "Firebolt mention rate",
            "result": pct(mention_rate),
            "evidence": "Answer contains the word Firebolt",
        },
        {
            "metric": "Firebolt recommendation rate",
            "result": pct(recommendation_rate),
            "evidence": (
                "Deterministic recommendation phrase matched Firebolt; "
                f"{recommendation_applicable_answers} recommendation-applicable answers"
            ),
        },
        {
            "metric": "Average visibility score",
            "result": f"{num(avg_visibility, 1)} / {SCORE_MAX}",
            "evidence": f"Standard prompts only; current score band: {score_band(avg_visibility)}",
        },
    ]


def named_records():
    return [
        {
            "prompt_framing": "Firebolt named in prompt",
            "prompts": named_prompts,
            "scored_answers": len(named),
            "recommendation_applicable_answers": int(named["recommendation_metric_applicable"].sum()) if len(named) else 0,
            "mention_rate": named_mention,
            "recommendation_rate": named_recommendation,
        },
        {
            "prompt_framing": "Workload only, Firebolt not named",
            "prompts": unnamed_prompts,
            "scored_answers": len(unnamed),
            "recommendation_applicable_answers": int(unnamed["recommendation_metric_applicable"].sum()) if len(unnamed) else 0,
            "mention_rate": unnamed_mention,
            "recommendation_rate": unnamed_recommendation,
        },
    ]


def baseline_records():
    return [
        {
            "metric": "Workload-only mention rate",
            "current_run": pct(unnamed_mention),
            "next_run_check": "Use the same P004, P005, P006, and P008 prompts.",
        },
        {
            "metric": "Overall mention rate",
            "current_run": pct(mention_rate),
            "next_run_check": "Compare against the same 8-prompt set.",
        },
        {
            "metric": "Overall recommendation rate",
            "current_run": pct(recommendation_rate),
            "next_run_check": "Exclude negative_tradeoff rows from this denominator.",
        },
    ]


def score_terms():
    return [
        {"term": "M", "meaning": "Firebolt is mentioned", "values": "0 or 1"},
        {"term": "R", "meaning": "Firebolt is recommended", "values": "0 or 1; not applied to negative_tradeoff prompts"},
        {"term": "K", "meaning": "Firebolt rank among named products", "values": "0 to 3"},
        {"term": "E", "meaning": "Firebolt explanation quality from judge", "values": "0 to 5"},
        {"term": "P", "meaning": "Factual-risk penalty from judge", "values": "0 to 3"},
    ]


def value_for(col, value):
    if isinstance(value, float):
        if "rate" in col:
            return pct(value)
        if "score" in col:
            return num(value, 2)
        return num(value, 2)
    return clean_text(value)


def table_html(records, columns):
    if isinstance(records, pd.DataFrame):
        records = records.to_dict("records")
    if not records:
        return '<p class="muted">No rows available.</p>'
    head = "".join(f"<th>{esc(label)}</th>" for col, label in columns)
    body_rows = []
    for record in records:
        cells = []
        for col, _ in columns:
            value = value_for(col, record.get(col, ""))
            cls = "num" if isinstance(record.get(col, ""), (int, float)) or "rate" in col or "score" in col else ""
            cells.append(f'<td class="{cls}">{esc(value)}</td>')
        body_rows.append("<tr>" + "".join(cells) + "</tr>")
    return (
        '<div class="table-wrap"><table><thead><tr>'
        + head
        + "</tr></thead><tbody>"
        + "".join(body_rows)
        + "</tbody></table></div>"
    )


def definition_html(items):
    rows = []
    for label, value in items:
        rows.append(f"<p><strong>{esc(label)}</strong><br>{esc(value)}</p>")
    return "\n".join(rows)


def weak_prompt_html():
    return table_html(weak_prompt_records(), [
        ("prompt_id", "Prompt ID"),
        ("model", "Model"),
        ("primary_recommendation", "Primary recommendation observed"),
        ("firebolt_mentioned", "Firebolt mentioned"),
        ("firebolt_recommended", "Firebolt recommended"),
        ("firebolt_rank", "Firebolt rank"),
        ("visibility_score", "Visibility score"),
        ("evidence_gap", "Evidence gap"),
    ])


def appendix_html():
    if len(appendix_rows) == 0:
        return '<p class="muted">No excerpts available.</p>'
    parts = []
    for _, row in appendix_rows.iterrows():
        label = (
            f"{field(row, 'prompt_id')} - {field(row, 'model')} - "
            f"score {num(row.get('visibility_score', 0), 1)} / {score_max_for_row(row)}"
        )
        excerpt = field(row, "answer_excerpt") or short(field(row, "answer"), 900)
        parts.append(
            "<details>"
            f"<summary>{esc(label)}</summary>"
            f"<p><strong>Prompt:</strong> {esc(field(row, 'prompt'))}</p>"
            f"<p><strong>Firebolt status:</strong> {esc(firebolt_status(row))}</p>"
            f"<p class='excerpt'>{esc(excerpt)}</p>"
            "</details>"
        )
    return "\n".join(parts)


def md_table(records, columns):
    if isinstance(records, pd.DataFrame):
        records = records.to_dict("records")
    if not records:
        return "_No rows available._\n"
    lines = [
        "| " + " | ".join(label for _, label in columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for record in records:
        cells = []
        for col, _ in columns:
            cells.append(value_for(col, record.get(col, "")).replace("|", "\\|"))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def md_fields(items):
    lines = []
    for label, value in items:
        lines.append(f"**{label}** {clean_text(value)}")
        lines.append("")
    return "\n".join(lines)


gen = config.get("generation_settings", {})
judge = config.get("judge_settings", {})
author = clean_text(config.get("author", ""))
version = clean_text(config.get("version", ""))
run_id = clean_text(df["run_id"].iloc[-1]) if has_data and clean_text(df["run_id"].iloc[-1]) else ""
date_label = datetime.now().strftime("%d %B %Y")

meta_bits = [date_label]
if author:
    meta_bits.append("Prepared by " + author)
if version:
    meta_bits.append("Version " + version)
if run_id:
    meta_bits.append("Run " + run_id)


def build_html():
    parts = []
    parts.append("<h1>1. Firebolt LLM Visibility Memo</h1>")
    parts.append("<p class='subtitle'>Gemini visibility on analytics-database selection prompts</p>")
    parts.append('<p class="meta">' + " | ".join(esc(bit) for bit in meta_bits) + "</p>")

    parts.append("<h2>2. Context</h2>")
    parts.append(
        "<p>This memo reports a local benchmark of whether Gemini models mention and recommend Firebolt "
        "when a developer asks for analytics-database advice.</p>"
    )
    parts.append(
        f"<p>The run produced {total_answers} scored answers across {unique_prompts} prompts and "
        f"{model_count} models. The result should be read as a model-visibility baseline, not as a "
        "product-quality assessment.</p>"
    )

    parts.append("<h2>3. Key findings</h2>")
    parts.append("<ul>")
    parts.append(
        f"<li>Firebolt was mentioned in {pct(mention_rate)} of scored answers. It was recommended in "
        f"{pct(recommendation_rate)} of recommendation-applicable answers. The average visibility score was "
        f"{num(avg_visibility, 1)} / {SCORE_MAX}.</li>"
    )
    parts.append(
        f"<li>Named prompts behaved differently from workload-only prompts. Named prompts had an "
        f"{pct(named_mention)} mention rate. Workload-only prompts had a {pct(unnamed_mention)} mention rate.</li>"
    )
    parts.append(
        f"<li>All workload-only prompts in this run, P004, P005, P006, and P008, had "
        f"{pct(unnamed_recommendation)} Firebolt recommendation rate.</li>"
    )
    if failed_model_rows:
        parts.append(
            f"<li>At least one requested model did not complete successfully. The run-health table lists "
            f"{len(failed_model_rows)} skipped or failed model entry.</li>"
        )
    if incomplete_models:
        parts.append(
            f"<li>{esc(', '.join(incomplete_models))} produced fewer than {unique_prompts} scored answers. "
            "Missing calls are reported as run issues, not as negative Firebolt outcomes.</li>"
        )
    parts.append("</ul>")
    parts.append(table_html(metric_records(), [
        ("metric", "Metric"),
        ("result", "Result"),
        ("evidence", "How to read it"),
    ]))

    parts.append("<h2>4. Experiment setup</h2>")
    parts.append(
        "<p>The pipeline is fixed: prompts.csv to model answers, then results/scored_answers.csv, then this report. "
        "Only rows with status ok and non-empty answer text are scored.</p>"
    )
    parts.append(
        "<p>Mention and rank are deterministic text checks. Recommendation is also deterministic when the scored "
        "CSV includes regex_firebolt_recommended. The judge model writes explanation fields and factual-risk notes.</p>"
    )
    parts.append(
        "<p>P007 is a negative-tradeoff prompt. It tests whether the answer explains where Firebolt is not a fit. "
        "It is excluded from recommendation-rate denominators because recommending Firebolt is not the target "
        "behavior for that prompt.</p>"
    )
    parts.append(
        "<p>The visibility score is V = 2M + 3R + K + E - P. The formula is used for comparison within this run. "
        "It is not a market-share score or a product score.</p>"
    )
    parts.append(table_html(score_terms(), [
        ("term", "Term"),
        ("meaning", "Meaning"),
        ("values", "Values"),
    ]))

    parts.append("<h2>5. Prompt design rationale</h2>")
    parts.append(
        "<p>The prompt set has two axes. The first is category: comparison, discovery, lakehouse, migration, "
        "tradeoff, and alternatives. The second is framing: Firebolt named versus workload only.</p>"
    )
    parts.append(
        "<p>The named prompts test whether a model can discuss Firebolt after the user brings it into the "
        "conversation. The unnamed prompts test whether the model retrieves Firebolt without that cue.</p>"
    )
    parts.append(table_html(records_for_prompt_categories(), [
        ("category", "Category"),
        ("prompts", "Prompts"),
        ("scored_answers", "Scored answers"),
        ("why_included", "Why included"),
    ]))
    parts.append(table_html(prompt_catalog_records(), [
        ("prompt_id", "Prompt ID"),
        ("framing", "Framing"),
        ("category", "Category"),
        ("prompt", "Prompt"),
        ("why_included", "Why included"),
    ]))

    parts.append("<h2>6. Model and generation settings</h2>")
    parts.append(
        "<p>The run used Gemini Flash-tier models because they are plausible default or low-cost assistant models. "
        "Each model received the same system prompt, user prompt, and generation settings.</p>"
    )
    parts.append(table_html(records_for_models(), [
        ("model", "Model"),
        ("scored_answers", "Scored answers"),
        ("provider", "Provider"),
        ("role", "Role in run"),
    ]))
    parts.append(table_html([
        {"setting": "Prompts per model", "value": gen.get("max_prompts", unique_prompts)},
        {"setting": "Answer temperature", "value": gen.get("temperature", "")},
        {"setting": "Answer top_p", "value": gen.get("top_p", "")},
        {"setting": "Max output tokens", "value": gen.get("max_output_tokens", "")},
        {"setting": "Judge model", "value": judge.get("model", "")},
        {"setting": "Judge temperature", "value": judge.get("temperature", "")},
    ], [("setting", "Setting"), ("value", "Value")]))
    parts.append("<h3>Run health</h3>")
    if failed_model_rows:
        parts.append(table_html(failed_model_rows, [
            ("model", "Model"),
            ("outcome", "Outcome"),
            ("reason", "Reason"),
            ("detail", "Detail"),
        ]))
    else:
        parts.append("<p>No model validation or run failures were recorded.</p>")

    parts.append("<h2>7. Results</h2>")
    parts.append("<p>This section reports measurements only. Interpretation starts in section 10.</p>")
    parts.append(table_html(metric_records(), [
        ("metric", "Metric"),
        ("result", "Result"),
        ("evidence", "Definition"),
    ]))
    parts.append("<h3>By prompt</h3>")
    parts.append(table_html(prompt_result_records(), [
        ("prompt_id", "Prompt ID"),
        ("framing", "Framing"),
        ("category", "Category"),
        ("prompt", "Prompt"),
        ("scored_answers", "Scored answers"),
        ("firebolt_mentioned", "Firebolt mentioned"),
        ("firebolt_recommended", "Firebolt recommended"),
        ("average_visibility_score", "Average score"),
        ("primary_recommendation", "Primary recommendation observed"),
    ]))
    parts.append("<h3>By model</h3>")
    parts.append(table_html(by_model, [
        ("model", "Model"),
        ("scored_answers", "Scored answers"),
        ("mention_rate", "Mention rate"),
        ("recommendation_rate", "Recommendation rate"),
        ("average_visibility_score", "Average visibility score"),
        ("average_firebolt_explanation", "Average Firebolt explanation"),
    ]))
    parts.append("<h3>By prompt category</h3>")
    parts.append(table_html(by_category, [
        ("category", "Category"),
        ("scored_answers", "Scored answers"),
        ("mention_rate", "Mention rate"),
        ("recommendation_rate", "Recommendation rate"),
        ("average_visibility_score", "Average visibility score"),
    ]))

    parts.append("<h2>8. Named vs unnamed prompt behavior</h2>")
    parts.append(table_html(named_records(), [
        ("prompt_framing", "Prompt framing"),
        ("prompts", "Prompts"),
        ("scored_answers", "Scored answers"),
        ("recommendation_applicable_answers", "Recommendation-applicable answers"),
        ("mention_rate", "Mention rate"),
        ("recommendation_rate", "Recommendation rate"),
    ]))
    parts.append(
        f"<p>Named prompts produced {pct(named_mention)} mention rate across {len(named)} scored answers. "
        f"Unnamed prompts produced {pct(unnamed_mention)} mention rate across {len(unnamed)} scored answers. "
        "Recommendation rates exclude negative_tradeoff rows.</p>"
    )
    parts.append(
        "<p>This section is still a result, not an explanation. The gap rows in sections 9 and 10 provide the "
        "basis for interpreting why the split happened.</p>"
    )

    parts.append("<h2>9. Weak prompt analysis</h2>")
    parts.append(
        "<p>Each row below is the weakest scored answer for a prompt. It is included to show the failure mode, "
        "not to prescribe content. The evidence-gap column should be treated as a hypothesis for review.</p>"
    )
    parts.append(weak_prompt_html())

    parts.append("<h2>10. Content gaps</h2>")
    parts.append(
        "<p>The gaps below are inferred from rows where Firebolt was absent, weak, or mentioned without a "
        "recommendation. They are not product findings. They indicate what public evidence the model appeared "
        "not to retrieve.</p>"
    )
    parts.append(table_html(content_gap_records(), [
        ("content_gap", "Content gap"),
        ("prompt_ids", "Prompt IDs"),
        ("scored_answers", "Scored answers"),
        ("mention_rate", "Mention rate"),
        ("recommendation_rate", "Recommendation rate"),
        ("average_visibility_score", "Average visibility score"),
        ("how_to_use", "How to use this row"),
    ]))

    parts.append("<h2>11. Recommended actions</h2>")
    parts.append(
        "<p>These actions are tied to the measurements above. They do not assume that every evidence gap should "
        "be turned into content.</p>"
    )
    parts.append("<ol>")
    parts.append(
        "<li>Use the prompt-level table as the baseline. The workload-only prompts P004, P005, P006, and P008 "
        f"currently have {pct(unnamed_mention)} Firebolt mention rate.</li>"
    )
    parts.append(
        "<li>Review each evidence gap with product and engineering owners. Mark each gap as supported, unsupported, "
        "or out of scope before deciding on any external content.</li>"
    )
    parts.append(
        "<li>Only act on supported gaps. If the supporting evidence is missing or weak, record the gap and do not "
        "publish a claim for that prompt.</li>"
    )
    parts.append(
        "<li>Rerun the same prompt set after any approved change. Compare prompt-level mention rate, recommendation "
        "rate, and average score against the current baseline.</li>"
    )
    parts.append("</ol>")
    parts.append(table_html(baseline_records(), [
        ("metric", "Metric"),
        ("current_run", "Current run"),
        ("next_run_check", "Next-run check"),
    ]))

    parts.append("<h2>12. Limitations</h2>")
    parts.append("<ul>")
    for item in config.get("limitations", []):
        parts.append(f"<li>{esc(item)}</li>")
    parts.append("<li>The run contains a model failure. That failure is shown in run health and excluded from scored rates.</li>")
    parts.append("</ul>")

    parts.append("<h2>13. Appendix with raw excerpts</h2>")
    parts.append(
        "<p>Excerpts are included for the weak-prompt rows only. They are collapsed by default so the memo "
        "does not read like a transcript.</p>"
    )
    parts.append(appendix_html())

    return "\n".join(parts)


STYLE = """
html { background: #ffffff; }
body {
  margin: 0;
  color: #111111;
  background: #ffffff;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
  font-size: 17px;
  line-height: 1.58;
}
.page {
  max-width: 1080px;
  margin: 0 auto;
  padding: 48px 56px 72px;
}
h1 {
  margin: 0 0 8px;
  font-size: 36px;
  line-height: 1.2;
  font-weight: 700;
  letter-spacing: 0;
}
.subtitle {
  margin: 0 0 12px;
  color: #333333;
  font-size: 18px;
}
.meta {
  margin: 0 0 32px;
  padding-top: 10px;
  border-top: 1px solid #d9d9d9;
  color: #555555;
  font-size: 14px;
}
h2 {
  margin: 34px 0 12px;
  padding-top: 18px;
  border-top: 1px solid #d9d9d9;
  font-size: 22px;
  line-height: 1.3;
  font-weight: 700;
  letter-spacing: 0;
}
h3 {
  margin: 24px 0 8px;
  font-size: 18px;
  line-height: 1.35;
  font-weight: 700;
  letter-spacing: 0;
}
p { margin: 0 0 12px; max-width: 820px; }
ul, ol { margin: 8px 0 16px; padding-left: 22px; }
li { margin: 5px 0; }
.table-wrap { overflow-x: auto; margin: 10px 0 20px; }
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 16px;
}
th, td {
  border: 1px solid #d9d9d9;
  padding: 9px 11px;
  vertical-align: top;
  text-align: left;
}
th {
  background: #f7f7f7;
  font-weight: 700;
}
td.num, th.num { text-align: right; white-space: nowrap; }
.muted { color: #666666; }
strong { font-weight: 700; }
details {
  border-top: 1px solid #d9d9d9;
  padding: 10px 0;
}
summary {
  cursor: pointer;
  font-weight: 600;
}
.excerpt {
  max-width: none;
  margin-top: 8px;
  color: #222222;
}
@media (max-width: 720px) {
  .page { padding: 28px 18px 48px; }
  h1 { font-size: 30px; }
  table { font-size: 15px; }
}
"""


html_doc = (
    "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
    "<meta charset=\"utf-8\">\n"
    "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
    "<title>Firebolt LLM Visibility Memo</title>\n"
    "<style>\n"
    + STYLE
    + "\n</style>\n</head>\n<body>\n<div class=\"page\">\n"
    + build_html()
    + "\n</div>\n</body>\n</html>\n"
)


def build_markdown():
    md = []
    md.append("# 1. Firebolt LLM Visibility Memo\n")
    md.append("_Gemini visibility on analytics-database selection prompts._\n")
    md.append(" | ".join(meta_bits) + "\n")

    md.append("## 2. Context\n")
    md.append(
        "This memo reports a local benchmark of whether Gemini models mention and recommend Firebolt "
        "when a developer asks for analytics-database advice.\n"
    )
    md.append(
        f"The run produced {total_answers} scored answers across {unique_prompts} prompts and "
        f"{model_count} models. The result should be read as a model-visibility baseline, not as a "
        "product-quality assessment.\n"
    )

    md.append("## 3. Key findings\n")
    md.append(
        f"- Firebolt was mentioned in {pct(mention_rate)} of scored answers. It was recommended in "
        f"{pct(recommendation_rate)} of recommendation-applicable answers. The average visibility score was "
        f"{num(avg_visibility, 1)} / {SCORE_MAX}."
    )
    md.append(
        f"- Named prompts had an {pct(named_mention)} mention rate. Workload-only prompts had a "
        f"{pct(unnamed_mention)} mention rate."
    )
    md.append(
        f"- Workload-only prompts P004, P005, P006, and P008 had {pct(unnamed_recommendation)} "
        "Firebolt recommendation rate."
    )
    if failed_model_rows:
        md.append(f"- The run recorded {len(failed_model_rows)} skipped or failed model entry.")
    if incomplete_models:
        md.append(
            f"- {', '.join(incomplete_models)} produced fewer than {unique_prompts} scored answers. "
            "Missing calls are reported as run issues."
        )
    md.append("")
    md.append(md_table(metric_records(), [
        ("metric", "Metric"),
        ("result", "Result"),
        ("evidence", "How to read it"),
    ]))

    md.append("## 4. Experiment setup\n")
    md.append(
        "The pipeline is fixed: prompts.csv to model answers, then results/scored_answers.csv, then this report. "
        "Only rows with status ok and non-empty answer text are scored.\n"
    )
    md.append(
        "Mention and rank are deterministic text checks. Recommendation is also deterministic when the scored "
        "CSV includes regex_firebolt_recommended. The judge model writes explanation fields and factual-risk notes.\n"
    )
    md.append(
        "P007 is a negative-tradeoff prompt. It tests whether the answer explains where Firebolt is not a fit. "
        "It is excluded from recommendation-rate denominators because recommending Firebolt is not the target "
        "behavior for that prompt.\n"
    )
    md.append(
        "The visibility score is `V = 2M + 3R + K + E - P`. The formula is used for comparison within this run. "
        "It is not a market-share score or a product score.\n"
    )
    md.append(md_table(score_terms(), [
        ("term", "Term"),
        ("meaning", "Meaning"),
        ("values", "Values"),
    ]))

    md.append("## 5. Prompt design rationale\n")
    md.append(
        "The prompt set has two axes. The first is category: comparison, discovery, lakehouse, migration, "
        "tradeoff, and alternatives. The second is framing: Firebolt named versus workload only.\n"
    )
    md.append(
        "The named prompts test whether a model can discuss Firebolt after the user brings it into the "
        "conversation. The unnamed prompts test whether the model retrieves Firebolt without that cue.\n"
    )
    md.append(md_table(records_for_prompt_categories(), [
        ("category", "Category"),
        ("prompts", "Prompts"),
        ("scored_answers", "Scored answers"),
        ("why_included", "Why included"),
    ]))
    md.append(md_table(prompt_catalog_records(), [
        ("prompt_id", "Prompt ID"),
        ("framing", "Framing"),
        ("category", "Category"),
        ("prompt", "Prompt"),
        ("why_included", "Why included"),
    ]))

    md.append("## 6. Model and generation settings\n")
    md.append(
        "The run used Gemini Flash-tier models because they are plausible default or low-cost assistant models. "
        "Each model received the same system prompt, user prompt, and generation settings.\n"
    )
    md.append(md_table(records_for_models(), [
        ("model", "Model"),
        ("scored_answers", "Scored answers"),
        ("provider", "Provider"),
        ("role", "Role in run"),
    ]))
    md.append(md_table([
        {"setting": "Prompts per model", "value": gen.get("max_prompts", unique_prompts)},
        {"setting": "Answer temperature", "value": gen.get("temperature", "")},
        {"setting": "Answer top_p", "value": gen.get("top_p", "")},
        {"setting": "Max output tokens", "value": gen.get("max_output_tokens", "")},
        {"setting": "Judge model", "value": judge.get("model", "")},
        {"setting": "Judge temperature", "value": judge.get("temperature", "")},
    ], [("setting", "Setting"), ("value", "Value")]))
    md.append("### Run health\n")
    if failed_model_rows:
        md.append(md_table(failed_model_rows, [
            ("model", "Model"),
            ("outcome", "Outcome"),
            ("reason", "Reason"),
            ("detail", "Detail"),
        ]))
    else:
        md.append("No model validation or run failures were recorded.\n")

    md.append("## 7. Results\n")
    md.append("This section reports measurements only. Interpretation starts in section 10.\n")
    md.append(md_table(metric_records(), [
        ("metric", "Metric"),
        ("result", "Result"),
        ("evidence", "Definition"),
    ]))
    md.append("### By prompt\n")
    md.append(md_table(prompt_result_records(), [
        ("prompt_id", "Prompt ID"),
        ("framing", "Framing"),
        ("category", "Category"),
        ("prompt", "Prompt"),
        ("scored_answers", "Scored answers"),
        ("firebolt_mentioned", "Firebolt mentioned"),
        ("firebolt_recommended", "Firebolt recommended"),
        ("average_visibility_score", "Average score"),
        ("primary_recommendation", "Primary recommendation observed"),
    ]))
    md.append("### By model\n")
    md.append(md_table(by_model, [
        ("model", "Model"),
        ("scored_answers", "Scored answers"),
        ("mention_rate", "Mention rate"),
        ("recommendation_rate", "Recommendation rate"),
        ("average_visibility_score", "Average visibility score"),
        ("average_firebolt_explanation", "Average Firebolt explanation"),
    ]))
    md.append("### By prompt category\n")
    md.append(md_table(by_category, [
        ("category", "Category"),
        ("scored_answers", "Scored answers"),
        ("mention_rate", "Mention rate"),
        ("recommendation_rate", "Recommendation rate"),
        ("average_visibility_score", "Average visibility score"),
    ]))

    md.append("## 8. Named vs unnamed prompt behavior\n")
    md.append(md_table(named_records(), [
        ("prompt_framing", "Prompt framing"),
        ("prompts", "Prompts"),
        ("scored_answers", "Scored answers"),
        ("recommendation_applicable_answers", "Recommendation-applicable answers"),
        ("mention_rate", "Mention rate"),
        ("recommendation_rate", "Recommendation rate"),
    ]))
    md.append(
        f"Named prompts produced {pct(named_mention)} mention rate across {len(named)} scored answers. "
        f"Unnamed prompts produced {pct(unnamed_mention)} mention rate across {len(unnamed)} scored answers. "
        "Recommendation rates exclude negative_tradeoff rows.\n"
    )
    md.append(
        "This section is still a result, not an explanation. The gap rows in sections 9 and 10 provide the "
        "basis for interpreting why the split happened.\n"
    )

    md.append("## 9. Weak prompt analysis\n")
    md.append(
        "Each row below is the weakest scored answer for a prompt. It is included to show the failure mode, "
        "not to prescribe content. The evidence-gap column should be treated as a hypothesis for review.\n"
    )
    md.append(md_table(weak_prompt_records(), [
        ("prompt_id", "Prompt ID"),
        ("model", "Model"),
        ("primary_recommendation", "Primary recommendation observed"),
        ("firebolt_mentioned", "Firebolt mentioned"),
        ("firebolt_recommended", "Firebolt recommended"),
        ("firebolt_rank", "Firebolt rank"),
        ("visibility_score", "Visibility score"),
        ("evidence_gap", "Evidence gap"),
    ]))

    md.append("## 10. Content gaps\n")
    md.append(
        "The gaps below are inferred from rows where Firebolt was absent, weak, or mentioned without a "
        "recommendation. They are not product findings. They indicate what public evidence the model appeared "
        "not to retrieve.\n"
    )
    md.append(md_table(content_gap_records(), [
        ("content_gap", "Content gap"),
        ("prompt_ids", "Prompt IDs"),
        ("scored_answers", "Scored answers"),
        ("mention_rate", "Mention rate"),
        ("recommendation_rate", "Recommendation rate"),
        ("average_visibility_score", "Average visibility score"),
        ("how_to_use", "How to use this row"),
    ]))

    md.append("## 11. Recommended actions\n")
    md.append(
        "These actions are tied to the measurements above. They do not assume that every evidence gap should "
        "be turned into content.\n"
    )
    md.append(
        "1. Use the prompt-level table as the baseline. The workload-only prompts P004, P005, P006, and P008 "
        f"currently have {pct(unnamed_mention)} Firebolt mention rate."
    )
    md.append(
        "2. Review each evidence gap with product and engineering owners. Mark each gap as supported, unsupported, "
        "or out of scope before deciding on any external content."
    )
    md.append(
        "3. Only act on supported gaps. If the supporting evidence is missing or weak, record the gap and do not "
        "publish a claim for that prompt."
    )
    md.append(
        "4. Rerun the same prompt set after any approved change. Compare prompt-level mention rate, recommendation "
        "rate, and average score against the current baseline.\n"
    )
    md.append(md_table(baseline_records(), [
        ("metric", "Metric"),
        ("current_run", "Current run"),
        ("next_run_check", "Next-run check"),
    ]))

    md.append("## 12. Limitations\n")
    for item in config.get("limitations", []):
        md.append(f"- {clean_text(item)}")
    md.append("- The run contains a model failure. That failure is shown in run health and excluded from scored rates.")
    md.append("")

    md.append("## 13. Appendix with raw excerpts\n")
    md.append(
        "Excerpts are included for the weak-prompt rows only. They are collapsed by default so the memo "
        "does not read like a transcript.\n"
    )
    for _, row in appendix_rows.iterrows():
        label = (
            f"{field(row, 'prompt_id')} - {field(row, 'model')} - "
            f"score {num(row.get('visibility_score', 0), 1)} / {score_max_for_row(row)}"
        )
        excerpt = field(row, "answer_excerpt") or short(field(row, "answer"), 900)
        md.append("<details>")
        md.append(f"<summary>{clean_text(label)}</summary>\n")
        md.append(f"**Prompt:** {field(row, 'prompt')}\n")
        md.append(f"**Firebolt status:** {firebolt_status(row)}\n")
        md.append(clean_text(excerpt) + "\n")
        md.append("</details>\n")

    return "\n".join(md) + "\n"


Path("results").mkdir(exist_ok=True)
Path(HTML_OUT).write_text(html_doc, encoding="utf-8")
Path(MD_OUT).write_text(build_markdown(), encoding="utf-8")

print(f"Wrote {HTML_OUT} and {MD_OUT}")
print(f"{total_answers} answers, {model_count} models used, {len(failed_model_rows)} skipped or failed")
