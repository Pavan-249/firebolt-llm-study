# 1. Firebolt LLM Visibility Memo

_Gemini visibility on analytics-database selection prompts._

09 June 2026 | Prepared by Pavan Kumar | Version 1.0 | Run 20260609_165014_f5553d96

## 2. Context

This memo reports a local benchmark of whether Gemini models mention and recommend Firebolt when a developer asks for analytics-database advice.

The run produced 16 scored answers across 8 prompts and 2 models. The result should be read as a model-visibility baseline, not as a product-quality assessment.

## 3. Key findings

- Firebolt was mentioned in 50.0% of scored answers. It was recommended in 42.9% of recommendation-applicable answers. The average visibility score was 3.9 / 13.
- How the prompt was framed mattered most. When the prompt named Firebolt, the model mentioned it in 100.0% of answers. When the prompt only described the workload, the rate was 0.0%.
- Across the workload-only prompts (P004, P005, P006, P008), the Firebolt recommendation rate was 0.0%.

| Metric | Result | How to read it |
| --- | --- | --- |
| Scored answers | 16 | 8 prompts across 2 models with scored answers |
| Firebolt mention rate | 50.0% | Answer contains the word Firebolt |
| Firebolt recommendation rate | 42.9% | Share of answers that put Firebolt forward as a fit. Counted over 14 answers where a recommendation applies (the 'when not to use Firebolt' prompt is left out) |
| Average visibility score | 3.9 / 13 | Excludes the 'when not to use Firebolt' prompt. Current band: weak |

## 4. Experiment setup

The pipeline is fixed: prompts.csv to model answers, then results/scored_answers.csv, then this report. Only rows with status ok and non-empty answer text are scored.

Mention, rank, and recommendation are all decided by exact text checks on the answer, so they are repeatable. A recommendation is counted only when the answer puts Firebolt forward as a fit, not when it merely names it. The judge model writes only the explanation and factual-risk notes.

One prompt, P007, asks when not to use Firebolt. A good answer explains where Firebolt does not fit, so recommending it is not the goal. P007 still counts toward the mention rate, but it is left out of the recommendation rate so a correct 'do not use it here' answer is not scored as a miss.

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
| Max output tokens | 4096 |
| Judge model | gemini-3.1-flash-lite |
| Judge temperature | 0.00 |

### Run health

No model validation or run failures were recorded.

## 7. Results

This section reports measurements only. Interpretation starts in section 10.

| Metric | Result | Definition |
| --- | --- | --- |
| Scored answers | 16 | 8 prompts across 2 models with scored answers |
| Firebolt mention rate | 50.0% | Answer contains the word Firebolt |
| Firebolt recommendation rate | 42.9% | Share of answers that put Firebolt forward as a fit. Counted over 14 answers where a recommendation applies (the 'when not to use Firebolt' prompt is left out) |
| Average visibility score | 3.9 / 13 | Excludes the 'when not to use Firebolt' prompt. Current band: weak |

### By prompt

| Prompt ID | Framing | Category | Prompt | Scored answers | Firebolt mentioned | Firebolt recommended | Average score | Primary recommendation observed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P001 | Named | direct_comparison | I am choosing between Firebolt and ClickHouse for low-latency analytics. Which one should... | 2 | Yes (2/2) | Yes (2/2) | 11.00 / 13 | unclear |
| P002 | Named | direct_comparison | Firebolt vs ClickHouse for customer-facing dashboards: what are the tradeoffs? | 2 | Yes (2/2) | Yes (2/2) | 10.00 / 13 | unclear |
| P003 | Named | lakehouse_iceberg | Firebolt vs Trino for querying Iceberg tables on S3: which is better? | 2 | Yes (2/2) | Yes (2/2) | 11.50 / 13 | Trino \| unclear |
| P004 | Unnamed | workload_discovery | I have 100GB of Parquet data in S3 and need fast dashboard queries. What engine should I u... | 2 | No (0/2) | No (0/2) | -1.00 / 13 | ClickHouse \| DuckDB |
| P005 | Unnamed | workload_discovery | I need to serve analytics to thousands of dashboard users with predictable latency. What d... | 2 | No (0/2) | No (0/2) | -1.50 / 13 | ClickHouse |
| P006 | Unnamed | migration | We currently use Trino for lakehouse queries but dashboard latency is poor. What should we... | 2 | No (0/2) | No (0/2) | -2.00 / 13 | ClickHouse \| unclear |
| P007 | Named | negative_tradeoff | When should I not use Firebolt? | 2 | Yes (2/2) | N/A (boundary prompt) | 8.00 / 10 | unclear |
| P008 | Unnamed | category_discovery | What are good ClickHouse alternatives for low-latency analytics? | 2 | No (0/2) | No (0/2) | -1.00 / 13 | StarRocks \| unclear |

### By model

| Model | Scored answers | Mention rate | Recommendation rate | Average visibility score | Average Firebolt explanation |
| --- | --- | --- | --- | --- | --- |
| gemini-3.1-flash-lite | 8 | 50.0% | 42.9% | 4.62 | 2.38 |
| gemini-3.5-flash | 8 | 50.0% | 42.9% | 4.12 | 2.50 |

### By prompt category

| Category | Scored answers | Mention rate | Recommendation rate | Average visibility score |
| --- | --- | --- | --- | --- |
| lakehouse_iceberg | 2 | 100.0% | 100.0% | 11.50 |
| direct_comparison | 4 | 100.0% | 100.0% | 10.50 |
| negative_tradeoff | 2 | 100.0% | N/A | 8.00 |
| category_discovery | 2 | 0.0% | 0.0% | -1.00 |
| workload_discovery | 4 | 0.0% | 0.0% | -1.25 |
| migration | 2 | 0.0% | 0.0% | -2.00 |

## 8. Named vs unnamed prompt behavior

| Prompt framing | Prompts | Scored answers | Recommendation-applicable answers | Mention rate | Recommendation rate |
| --- | --- | --- | --- | --- | --- |
| Firebolt named in prompt | 4 | 8 | 6 | 100.0% | 100.0% |
| Workload only, Firebolt not named | 4 | 8 | 8 | 0.0% | 0.0% |

Named prompts produced 100.0% mention rate across 8 scored answers. Unnamed prompts produced 0.0% mention rate across 8 scored answers. Recommendation rates exclude negative_tradeoff rows.

This section is still a result, not an explanation. The gap rows in sections 9 and 10 provide the basis for interpreting why the split happened.

## 9. Weak prompt analysis

Each row below is the weakest scored answer for a prompt. It is included to show the failure mode, not to prescribe content. The evidence-gap column should be treated as a hypothesis for review.

| Prompt ID | Model | Primary recommendation observed | Firebolt mentioned | Firebolt recommended | Firebolt rank | Visibility score | Evidence gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P005 | gemini-3.5-flash | ClickHouse | No | No | not_mentioned | -2.0 / 13 | Evidence for high-concurrency dashboard latency and predictability. |
| P006 | gemini-3.1-flash-lite | ClickHouse | No | No | not_mentioned | -2.0 / 13 | Evidence for improving dashboard latency when Trino is already used over lakehouse data. |
| P004 | gemini-3.1-flash-lite | DuckDB | No | No | not_mentioned | -1.0 / 13 | Evidence that Firebolt fits S3-resident Parquet dashboard queries. |
| P008 | gemini-3.1-flash-lite | StarRocks | No | No | not_mentioned | -1.0 / 13 | Evidence positioning Firebolt as a ClickHouse alternative. |

## 10. Content gaps

The gaps below are inferred from rows where Firebolt was absent, weak, or mentioned without a recommendation. They are not product findings. They indicate what public evidence the model appeared not to retrieve.

| Content gap | Prompt IDs | Scored answers | Mention rate | Recommendation rate | Average visibility score | How to use this row |
| --- | --- | --- | --- | --- | --- | --- |
| Lakehouse and Iceberg positioning gap | P004, P006 | 4 | 0.0% | 0.0% | -1.50 | Treat as a hypothesis. Confirm with product and engineering before publishing content. |
| Customer-facing analytics positioning gap | P005 | 2 | 0.0% | 0.0% | -1.50 | Treat as a hypothesis. Confirm with product and engineering before publishing content. |
| Category discovery gap | P008 | 2 | 0.0% | 0.0% | -1.00 | Treat as a hypothesis. Confirm with product and engineering before publishing content. |

## 11. Recommended actions

These actions are tied to the measurements above. They do not assume that every evidence gap should be turned into content.

1. Use the prompt-level table as the baseline. The workload-only prompts P004, P005, P006, and P008 currently have 0.0% Firebolt mention rate.
2. Review each evidence gap with product and engineering owners. Mark each gap as supported, unsupported, or out of scope before deciding on any external content.
3. Only act on supported gaps. If the supporting evidence is missing or weak, record the gap and do not publish a claim for that prompt.
4. Rerun the same prompt set after any approved change. Compare prompt-level mention rate, recommendation rate, and average score against the current baseline.

| Metric | Current run | Next-run check |
| --- | --- | --- |
| Workload-only mention rate | 0.0% | Use the same P004, P005, P006, and P008 prompts. |
| Overall mention rate | 50.0% | Compare against the same 8-prompt set. |
| Overall recommendation rate | 42.9% | Exclude negative_tradeoff rows from this denominator. |

## 12. Limitations

- This is a small diagnostic benchmark, not a full market study.
- Only Gemini models are included in this run.
- The run uses 8 prompts per model to stay inside the free Gemini quota.
- Model answers can change over time as model versions and training data change.
- The judge model writes the explanation text, so important rows should still be read by a person.
- The result is most useful when the same prompt set is rerun after public content about Firebolt changes.

## 13. Appendix with raw excerpts

Excerpts are included for the weak-prompt rows only. They are collapsed by default so the memo does not read like a transcript.

<details>
<summary>P004 - gemini-3.1-flash-lite - score -1.0 / 13</summary>

**Prompt:** I have 100GB of Parquet data in S3 and need fast dashboard queries. What engine should I use?

**Firebolt status:** Mentioned: No; recommended: No; rank: not_mentioned; score: -1.0 / 13.

For a 100GB dataset, you are in a "target range." It is small enough to fit into the memory of a single large instance, but large enough that a naive approach (like reading the whole file into a Pandas DataFrame) will cause performance bottlenecks and memory errors. Since your data is already in Parquet on S3, you have a few distinct paths depending on your tolerance for operational overhead and your latency requirements. 1. The "managed" Path: AWS Athena (Presto/Trino-based) If you are already in the AWS ecosystem, Athena is the path of least resistance. The Fit: It's serverless. You point it at your S3 bucket, define a schema in Glue, and query. Tradeoffs: It is not designed...

</details>

<details>
<summary>P005 - gemini-3.5-flash - score -2.0 / 13</summary>

**Prompt:** I need to serve analytics to thousands of dashboard users with predictable latency. What database should I consider?

**Firebolt status:** Mentioned: No; recommended: No; rank: not_mentioned; score: -2.0 / 13.

Serving analytics to thousands of concurrent dashboard users with predictable, sub-second latency is a specific and challenging workload. It is often referred to as user-facing analytics. Traditional cloud data warehouses (like Snowflake, BigQuery, or Redshift) are excellent for internal BI and heavy ad-hoc queries, but they are not designed for this. They will struggle with high concurrency, and the cost of auto-scaling them to support thousands of concurrent users will be prohibitively expensive. To solve this, you need to look at Real-Time OLAP (RT-OLAP) databases or specialized caching architectures. Here is a breakdown of the three main paths you should consider, along with...

</details>

<details>
<summary>P006 - gemini-3.1-flash-lite - score -2.0 / 13</summary>

**Prompt:** We currently use Trino for lakehouse queries but dashboard latency is poor. What should we evaluate next?

**Firebolt status:** Mentioned: No; recommended: No; rank: not_mentioned; score: -2.0 / 13.

It's a common "Trino wall." Trino is a general-purpose federated query engine, but it is fundamentally designed for ad-hoc exploration and ETL, not for high-concurrency, sub-second dashboarding. When you force Trino to serve dashboards, you're hitting the overhead of its distributed query planning and the latency of reading raw files from S3/GCS on every request. To move forward, you need to decide if you want to accelerate the lakehouse or move the data into a specialized serving layer. The answer evaluates your next steps. 1. The "Lakehouse Acceleration" Path (Keep the data in S3/Object Storage) If you want to keep your data in your data lake and avoid the operational burd...

</details>

<details>
<summary>P008 - gemini-3.1-flash-lite - score -1.0 / 13</summary>

**Prompt:** What are good ClickHouse alternatives for low-latency analytics?

**Firebolt status:** Mentioned: No; recommended: No; rank: not_mentioned; score: -1.0 / 13.

When you're looking for alternatives to ClickHouse, you're usually trying to solve for one of three things: operational simplicity, better integration with a specific data lake format (like Iceberg/Delta), or lower maintenance overhead. ClickHouse is very fast, but it is "opinionated" about how you store and manage data. If that doesn't fit your stack, here are the primary alternatives, categorized by how they handle the workload. - 1. The "Cloud-Native/Serverless" Route: StarRocks or Apache Doris If you like the performance profile of ClickHouse but want something that handles real-time updates (upserts/deletes) more gracefully and integrates better with standard BI...

</details>

