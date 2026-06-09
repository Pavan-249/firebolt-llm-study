# 1. Firebolt LLM Visibility Memo

_Gemini visibility on analytics-database selection prompts._

09 June 2026 | Prepared by Pavan Kumar | Version 1.0 | Run 20260609_140045_1cf0c17b

## 2. Context

This memo reports a local benchmark of whether Gemini models mention and recommend Firebolt when a developer asks for analytics-database advice.

The run produced 16 scored answers across 8 prompts and 2 models. The result should be read as a model-visibility baseline, not as a product-quality assessment.

## 3. Key findings

- Firebolt was mentioned in 37.5% of scored answers. It was recommended in 21.4% of recommendation-applicable answers. The average visibility score was 1.9 / 13.
- Named prompts had an 75.0% mention rate. Workload-only prompts had a 0.0% mention rate.
- Workload-only prompts P004, P005, P006, and P008 had 0.0% Firebolt recommendation rate.

| Metric | Result | How to read it |
| --- | --- | --- |
| Scored answers | 16 | 8 prompts across 2 models with scored answers |
| Firebolt mention rate | 37.5% | Answer contains the word Firebolt |
| Firebolt recommendation rate | 21.4% | Deterministic recommendation phrase matched Firebolt; 14 recommendation-applicable answers |
| Average visibility score | 1.9 / 13 | Standard prompts only; current score band: weak |

## 4. Experiment setup

The pipeline is fixed: prompts.csv to model answers, then results/scored_answers.csv, then this report. Only rows with status ok and non-empty answer text are scored.

Mention and rank are deterministic text checks. Recommendation is also deterministic when the scored CSV includes regex_firebolt_recommended. The judge model writes explanation fields and factual-risk notes.

P007 is a negative-tradeoff prompt. It tests whether the answer explains where Firebolt is not a fit. It is excluded from recommendation-rate denominators because recommending Firebolt is not the target behavior for that prompt.

The visibility score is `V = 2M + 3R + K + E - P`. The formula is used for comparison within this run. It is not a market-share score or a product score.

| Term | Meaning | Values |
| --- | --- | --- |
| M | Firebolt is mentioned | 0 or 1 |
| R | Firebolt is recommended | 0 or 1; not applied to negative_tradeoff prompts |
| K | Firebolt rank among named products | 0 to 3 |
| E | Firebolt explanation quality from judge | 0 to 5 |
| P | Factual-risk penalty from judge | 0 to 3 |

## 5. Prompt design rationale

The prompt set has two axes. The first is category: comparison, discovery, lakehouse, migration, tradeoff, and alternatives. The second is framing: Firebolt named versus workload only.

The named prompts test whether a model can discuss Firebolt after the user brings it into the conversation. The unnamed prompts test whether the model retrieves Firebolt without that cue.

| Category | Prompts | Scored answers | Why included |
| --- | --- | --- | --- |
| direct_comparison | 2 | 4 | Tests whether the model can compare Firebolt against a named competitor. |
| workload_discovery | 2 | 4 | Tests whether Firebolt appears when the user describes the workload but does not name Firebolt. |
| lakehouse_iceberg | 1 | 2 | Tests Firebolt positioning around S3, Parquet, Iceberg, and external table analytics. |
| migration | 1 | 2 | Tests whether Firebolt is suggested when a team has pain with its current system. |
| negative_tradeoff | 1 | 2 | Tests whether the model understands when Firebolt is not the right fit. |
| category_discovery | 1 | 2 | Tests whether Firebolt appears naturally in a broad category question. |

| Prompt ID | Framing | Category | Prompt | Why included |
| --- | --- | --- | --- | --- |
| P001 | Named | direct_comparison | I am choosing between Firebolt and ClickHouse for low-latency analytics. Which one should... | Tests Firebolt against the strongest default OLAP competitor. |
| P002 | Named | direct_comparison | Firebolt vs ClickHouse for customer-facing dashboards: what are the tradeoffs? | Tests whether Firebolt is positioned clearly for serving analytics and high concurrency. |
| P003 | Named | lakehouse_iceberg | Firebolt vs Trino for querying Iceberg tables on S3: which is better? | Tests Firebolt against a common lakehouse query engine. |
| P004 | Unnamed | workload_discovery | I have 100GB of Parquet data in S3 and need fast dashboard queries. What engine should I u... | Tests whether Firebolt appears from workload description without a vendor-first framing. |
| P005 | Unnamed | workload_discovery | I need to serve analytics to thousands of dashboard users with predictable latency. What d... | Tests Firebolt visibility for high-concurrency customer-facing analytics. |
| P006 | Unnamed | migration | We currently use Trino for lakehouse queries but dashboard latency is poor. What should we... | Tests whether Firebolt is suggested when the user has latency pain with Trino. |
| P007 | Named | negative_tradeoff | When should I not use Firebolt? | Tests whether the model understands Firebolt boundaries and gives a balanced answer. |
| P008 | Unnamed | category_discovery | What are good ClickHouse alternatives for low-latency analytics? | Tests whether Firebolt appears naturally as a category alternative. |

## 6. Model and generation settings

The run used Gemini Flash-tier models because they are plausible default or low-cost assistant models. Each model received the same system prompt, user prompt, and generation settings.

| Model | Scored answers | Provider | Role in run |
| --- | --- | --- | --- |
| gemini-3.1-flash-lite | 8 | Google Gemini | Fast baseline model with the highest daily quota in this account. Also used as the judge model. |
| gemini-3.5-flash | 8 | Google Gemini | Stronger Flash model, used to check whether better reasoning changes how often Firebolt appears. |

| Setting | Value |
| --- | --- |
| Prompts per model | 8 |
| Answer temperature | 0.20 |
| Answer top_p | 0.95 |
| Max output tokens | 900 |
| Judge model | gemini-3.1-flash-lite |
| Judge temperature | 0.00 |

### Run health

No model validation or run failures were recorded.

## 7. Results

This section reports measurements only. Interpretation starts in section 10.

| Metric | Result | Definition |
| --- | --- | --- |
| Scored answers | 16 | 8 prompts across 2 models with scored answers |
| Firebolt mention rate | 37.5% | Answer contains the word Firebolt |
| Firebolt recommendation rate | 21.4% | Deterministic recommendation phrase matched Firebolt; 14 recommendation-applicable answers |
| Average visibility score | 1.9 / 13 | Standard prompts only; current score band: weak |

### By prompt

| Prompt ID | Framing | Category | Prompt | Scored answers | Firebolt mentioned | Firebolt recommended | Average score | Primary recommendation observed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P001 | Named | direct_comparison | I am choosing between Firebolt and ClickHouse for low-latency analytics. Which one should... | 2 | Yes (2/2) | Yes (1/2) | 6.50 / 13 | unclear |
| P002 | Named | direct_comparison | Firebolt vs ClickHouse for customer-facing dashboards: what are the tradeoffs? | 2 | Yes (1/2) | Yes (1/2) | 5.50 / 13 | unclear |
| P003 | Named | lakehouse_iceberg | Firebolt vs Trino for querying Iceberg tables on S3: which is better? | 2 | Yes (1/2) | Yes (1/2) | 6.50 / 13 | Trino \| unclear |
| P004 | Unnamed | workload_discovery | I have 100GB of Parquet data in S3 and need fast dashboard queries. What engine should I u... | 2 | No (0/2) | No (0/2) | -1.50 / 13 | DuckDB |
| P005 | Unnamed | workload_discovery | I need to serve analytics to thousands of dashboard users with predictable latency. What d... | 2 | No (0/2) | No (0/2) | -1.00 / 13 | ClickHouse |
| P006 | Unnamed | migration | We currently use Trino for lakehouse queries but dashboard latency is poor. What should we... | 2 | No (0/2) | No (0/2) | -1.00 / 13 | StarRocks \| unclear |
| P007 | Named | negative_tradeoff | When should I not use Firebolt? | 2 | Yes (2/2) | N/A (boundary prompt) | 6.50 / 10 | unclear |
| P008 | Unnamed | category_discovery | What are good ClickHouse alternatives for low-latency analytics? | 2 | No (0/2) | No (0/2) | -1.50 / 13 | unclear |

### By model

| Model | Scored answers | Mention rate | Recommendation rate | Average visibility score | Average Firebolt explanation |
| --- | --- | --- | --- | --- | --- |
| gemini-3.1-flash-lite | 8 | 50.0% | 42.9% | 4.62 | 2.38 |
| gemini-3.5-flash | 8 | 25.0% | 0.0% | 0.38 | 0.62 |

### By prompt category

| Category | Scored answers | Mention rate | Recommendation rate | Average visibility score |
| --- | --- | --- | --- | --- |
| lakehouse_iceberg | 2 | 50.0% | 50.0% | 6.50 |
| negative_tradeoff | 2 | 100.0% | N/A | 6.50 |
| direct_comparison | 4 | 75.0% | 50.0% | 6.00 |
| migration | 2 | 0.0% | 0.0% | -1.00 |
| workload_discovery | 4 | 0.0% | 0.0% | -1.25 |
| category_discovery | 2 | 0.0% | 0.0% | -1.50 |

## 8. Named vs unnamed prompt behavior

| Prompt framing | Prompts | Scored answers | Recommendation-applicable answers | Mention rate | Recommendation rate |
| --- | --- | --- | --- | --- | --- |
| Firebolt named in prompt | 4 | 8 | 6 | 75.0% | 50.0% |
| Workload only, Firebolt not named | 4 | 8 | 8 | 0.0% | 0.0% |

Named prompts produced 75.0% mention rate across 8 scored answers. Unnamed prompts produced 0.0% mention rate across 8 scored answers. Recommendation rates exclude negative_tradeoff rows.

This section is still a result, not an explanation. The gap rows in sections 9 and 10 provide the basis for interpreting why the split happened.

## 9. Weak prompt analysis

Each row below is the weakest scored answer for a prompt. It is included to show the failure mode, not to prescribe content. The evidence-gap column should be treated as a hypothesis for review.

| Prompt ID | Model | Primary recommendation observed | Firebolt mentioned | Firebolt recommended | Firebolt rank | Visibility score | Evidence gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P004 | gemini-3.1-flash-lite | DuckDB | No | No | not_mentioned | -2.0 / 13 | Evidence that Firebolt fits S3-resident Parquet dashboard queries. |
| P008 | gemini-3.1-flash-lite | unclear | No | No | not_mentioned | -2.0 / 13 | Evidence positioning Firebolt as a ClickHouse alternative. |
| P002 | gemini-3.5-flash | unclear | No | No | not_mentioned | -1.0 / 13 | Evidence comparing Firebolt and ClickHouse for customer-facing dashboards. |
| P005 | gemini-3.1-flash-lite | ClickHouse | No | No | not_mentioned | -1.0 / 13 | Evidence for high-concurrency dashboard latency and predictability. |
| P006 | gemini-3.1-flash-lite | StarRocks | No | No | not_mentioned | -1.0 / 13 | Evidence for improving dashboard latency when Trino is already used over lakehouse data. |
| P003 | gemini-3.5-flash | Trino | No | No | not_mentioned | 1.0 / 13 | Public documentation or benchmarks demonstrating high-performance, zero-copy querying of external Iceberg tables on S3 w... |
| P001 | gemini-3.5-flash | unclear | Yes | No | last | 3.0 / 13 | Evidence comparing Firebolt and ClickHouse for low-latency analytics. |
| P007 | gemini-3.5-flash | unclear | Yes | No | first | 4.0 / 10 | Evidence defining where Firebolt is and is not a fit. |

## 10. Content gaps

The gaps below are inferred from rows where Firebolt was absent, weak, or mentioned without a recommendation. They are not product findings. They indicate what public evidence the model appeared not to retrieve.

| Content gap | Prompt IDs | Scored answers | Mention rate | Recommendation rate | Average visibility score | How to use this row |
| --- | --- | --- | --- | --- | --- | --- |
| Lakehouse and Iceberg positioning gap | P004, P006 | 4 | 0.0% | 0.0% | -1.25 | Treat as a hypothesis. Confirm with product and engineering before publishing content. |
| Category discovery gap | P008 | 2 | 0.0% | 0.0% | -1.50 | Treat as a hypothesis. Confirm with product and engineering before publishing content. |
| Customer-facing analytics positioning gap | P005 | 2 | 0.0% | 0.0% | -1.00 | Treat as a hypothesis. Confirm with product and engineering before publishing content. |
| Firebolt ignored despite being named | P002, P003 | 2 | 0.0% | 0.0% | 0.00 | Treat as a hypothesis. Confirm with product and engineering before publishing content. |
| ClickHouse comparison confidence gap | P001 | 1 | 100.0% | 0.0% | 3.00 | Treat as a hypothesis. Confirm with product and engineering before publishing content. |

## 11. Recommended actions

These actions are tied to the measurements above. They do not assume that every evidence gap should be turned into content.

1. Use the prompt-level table as the baseline. The workload-only prompts P004, P005, P006, and P008 currently have 0.0% Firebolt mention rate.
2. Review each evidence gap with product and engineering owners. Mark each gap as supported, unsupported, or out of scope before deciding on any external content.
3. Only act on supported gaps. If the supporting evidence is missing or weak, record the gap and do not publish a claim for that prompt.
4. Rerun the same prompt set after any approved change. Compare prompt-level mention rate, recommendation rate, and average score against the current baseline.

| Metric | Current run | Next-run check |
| --- | --- | --- |
| Workload-only mention rate | 0.0% | Use the same P004, P005, P006, and P008 prompts. |
| Overall mention rate | 37.5% | Compare against the same 8-prompt set. |
| Overall recommendation rate | 21.4% | Exclude negative_tradeoff rows from this denominator. |

## 12. Limitations

- This is a small diagnostic benchmark, not a full market study.
- Only Gemini models are included in this run.
- The run uses 8 prompts per model to stay inside the free Gemini quota.
- Model answers can change over time as model versions and training data change.
- The judge model writes the explanation text, so important rows should still be read by a person.
- The result is most useful when the same prompt set is rerun after public content about Firebolt changes.
- The run contains a model failure. That failure is shown in run health and excluded from scored rates.

## 13. Appendix with raw excerpts

Excerpts are included for the weak-prompt rows only. They are collapsed by default so the memo does not read like a transcript.

<details>
<summary>P001 - gemini-3.5-flash - score 3.0 / 13</summary>

**Prompt:** I am choosing between Firebolt and ClickHouse for low-latency analytics. Which one should I use?

**Firebolt status:** Mentioned: Yes; recommended: No; rank: last; score: 3.0 / 13.

Both ClickHouse and Firebolt are designed for sub-second, low-latency analytics on large datasets, but they represent two fundamentally different architectural philosophies

</details>

<details>
<summary>P002 - gemini-3.5-flash - score -1.0 / 13</summary>

**Prompt:** Firebolt vs ClickHouse for customer-facing dashboards: what are the tradeoffs?

**Firebolt status:** Mentioned: No; recommended: No; rank: not_mentioned; score: -1.0 / 13.

facing" aspect: Customer-facing means concurrency is king. If 10,000 users hit the dashboard, how do they scale?

</details>

<details>
<summary>P003 - gemini-3.5-flash - score 1.0 / 13</summary>

**Prompt:** Firebolt vs Trino for querying Iceberg tables on S3: which is better?

**Firebolt status:** Mentioned: No; recommended: No; rank: not_mentioned; score: 1.0 / 13.

This is a common "Query Engine vs. Cloud Data Warehouse" comparison, but the context of Apache Iceberg on S3 makes it highly specific.

</details>

<details>
<summary>P004 - gemini-3.1-flash-lite - score -2.0 / 13</summary>

**Prompt:** I have 100GB of Parquet data in S3 and need fast dashboard queries. What engine should I use?

**Firebolt status:** Mentioned: No; recommended: No; rank: not_mentioned; score: -2.0 / 13.

At 100GB, you are in a "target range." You are too large for a traditional RDBMS to handle comfortably without significant indexing overhead, but you are small enough that you don't necessarily need a massive distributed cluster (like a full-blown Spark or Presto deployment) to get sub-second performance. To give you the right recommendation, we need to look at your concurrency requirements and latency expectations. The answer frames your options based on the operational trade-offs. 1. The "managed" Path: DuckDB (via MotherDuck or local) If your dashboard is for a small internal team or a low-concurrency application, DuckDB is the current common reference point for this sc...

</details>

<details>
<summary>P005 - gemini-3.1-flash-lite - score -1.0 / 13</summary>

**Prompt:** I need to serve analytics to thousands of dashboard users with predictable latency. What database should I consider?

**Firebolt status:** Mentioned: No; recommended: No; rank: not_mentioned; score: -1.0 / 13.

Serving thousands of concurrent dashboard users with predictable latency is a common "high-concurrency OLAP" challenge. The primary bottleneck here isn't usually the raw query speed, but concurrency management-ensuring that one heavy query doesn't starve the others and that the system can handle the cache-miss spikes. To give you the right recommendation, we need to look at where your data lives and how "fresh" it needs to be. The answer groups your options based on the architectural trade-offs. 1. The "Pre-Aggregated" Approach (Druid or Pinot) If your dashboard users are hitting the same metrics repeatedly (e.g., "Total Sales by Region"), you should look at Apache Dr...

</details>

<details>
<summary>P006 - gemini-3.1-flash-lite - score -1.0 / 13</summary>

**Prompt:** We currently use Trino for lakehouse queries but dashboard latency is poor. What should we evaluate next?

**Firebolt status:** Mentioned: No; recommended: No; rank: not_mentioned; score: -1.0 / 13.

It's a common inflection point. Trino is a general-purpose "federation engine"-it's essentially the general-purpose engine of data-but it's fundamentally a compute-on-read engine. When you hit it with dashboard traffic, you're asking it to scan files, parse metadata, and execute complex joins in real-time, which is why your latency is suffering. To move from "querying a lake" to "serving dashboards," you need to shift from compute-on-read to compute-on-indexed-data. The answer groups your next steps based on your operational appetite and the nature of your data. - 1. The "Keep the Lake, Add an Accelerator" Approach If you want to keep your data in S3/GCS/ADLS but need su...

</details>

<details>
<summary>P007 - gemini-3.5-flash - score 4.0 / 10</summary>

**Prompt:** When should I not use Firebolt?

**Firebolt status:** Mentioned: Yes; recommended: No; rank: first; score: 4.0 / 10.

Firebolt is a specialized tool. It was built with a specific goal in mind: delivering sub-second, high-concurrency query performance on massive datasets (typically

</details>

<details>
<summary>P008 - gemini-3.1-flash-lite - score -2.0 / 13</summary>

**Prompt:** What are good ClickHouse alternatives for low-latency analytics?

**Firebolt status:** Mentioned: No; recommended: No; rank: not_mentioned; score: -2.0 / 13.

When you're looking for alternatives to ClickHouse, you're usually looking to solve one of three problems: you need something easier to manage, you need better integration with a specific data lake format (like Iceberg/Delta), or you need a different concurrency model. ClickHouse is a beast at raw scan performance, but it's opinionated about its storage format and can be operationally heavy if you aren't using their cloud offering. The answer groups the alternatives based on your specific architectural needs: 1. The "Data Lakehouse" Approach (Decoupled Storage) If your data already lives in S3/GCS in Parquet or Iceberg format, and you don't want to "ingest" it into a proprie...

</details>

