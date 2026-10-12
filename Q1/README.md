# Q1: EcoReport ESG Incident Assistant

- `build_agent.py`: builds the **Dialogflow CX** agent (8 pages, form parameters, condition routes, flow-level intents) via the Dialogflow CX v3 API. The CX agent could not be run because the Google Cloud billing account was closed by Google ("not in good standing").
- `build_es.py`: builds the equivalent **Dialogflow ES (Trial edition)** agent: entities, slot-filling intent, context-gated severity branch, context-specific fallback, global cancel/handoff/sensitive intents.
- `test_es.py`: runs 7 scripted conversations through `detectIntent`.
- `test_transcripts.txt`: results. **7/7 scenarios passed.**
- `screenshots/`: CX flow graph and Incident Details form.

Run both scripts from Google Cloud Shell (they use `gcloud auth print-access-token`).
