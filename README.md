# Firebolt LLM Visibility Study

Small diagnostic benchmark measuring whether Gemini models mention and recommend Firebolt on analytics-database selection prompts.

## Report

- GitHub Pages: https://pavan-249.github.io/firebolt-llm-study/
- Local HTML: `results/firebolt_llm_visibility_report.html`
- Scored rows: `results/scored_answers.csv`

## Method

The benchmark uses 8 fixed prompts across 2 Gemini models. Mention and rank are deterministic text checks. Recommendation is based on deterministic Firebolt recommendation patterns. A Gemini judge supplies explanation fields, factual-risk notes, and answer-quality fields.

P007 is treated as a negative-tradeoff prompt. It is excluded from recommendation-rate denominators because recommending Firebolt is not the target behavior for that prompt.

## Reproduce

Set `GEMINI_API_KEY` in a local `.env` file, then run:

```bash
python run_benchmark.py --fresh
python score_answers.py
python report.py
```

The `.env` file is ignored and must not be committed.
