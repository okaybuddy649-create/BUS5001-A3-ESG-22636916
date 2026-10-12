# Q3: LLM-based ESG message triage

**Design:** 11 messages (5 from the brief + 6 stress tests: multi-issue, positive, sensitive/PII, prompt injection, vague, sarcasm). Expected labels were set by the analyst before any model was run.

| Method | Implementation |
|---|---|
| LLM, original prompt | Template from the brief, unchanged, greedy decoding |
| LLM, revised prompt | Persona, closed label sets, urgency definitions, injection guard, null-for-missing, human-review rule, one-shot example. Run 1 greedy; runs 2–3 sampled (T = 0.7) for consistency |
| Rule-based baseline | Keyword rules + TextBlob polarity (extends the unit workshop baseline) |
| Zero-shot baseline | `facebook/bart-large-mnli` (category, urgency) + `distilbert-base-uncased-finetuned-sst-2-english` (sentiment) |

**Model:** `Qwen/Qwen2.5-1.5B-Instruct`, run locally on CPU in Google Cloud Shell, so no message text was sent to an external API. `BUS5001_A3_Q3_ESG_Triage.ipynb` is the equivalent Colab version for Gemini.

**Files in `logs/`:** `llm_runs.jsonl` (every raw output, with prompt version, temperature, parse and schema-validation results), `comparison.csv`, `metrics.csv`, `consistency.csv`, `errors.csv`, `run_info.json`.

**Prompts:** [`prompts.md`](prompts.md) holds the original and revised templates exactly as run.
