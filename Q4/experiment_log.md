# Q4 – NotebookLM (Gemini Notebook) evaluation: experiment log

**Tester:** Ayush Majithia (22636916)
**Date:** 12 October 2026
**Tool:** Google NotebookLM, rebranded in-product as **"Gemini Notebook"** (notebook.google.com), free tier
**Scenario:** A Master of Business Analytics student preparing a briefing on Australia's new mandatory climate-related financial disclosure regime, and how it relates to the global frameworks.

## Sources loaded (website URLs)

| # | Source | URL | Import result |
|---|---|---|---|
| S1 | ASIC – Sustainability reporting | https://asic.gov.au/regulatory-resources/sustainability-reporting/ | Imported |
| S2 | IFRS – IFRS S2 Climate-related Disclosures | https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s2-climate-related-disclosures/ | Imported |
| S3 | GRI – Standards | https://www.globalreporting.org/standards/ | Imported, **including cookie-banner text** (see E6) |
| – | Wikipedia – Environmental, social, and governance | https://en.wikipedia.org/wiki/Environmental,_social,_and_governance | **Rejected**: pasting several URLs on one line (or a URL containing a comma) triggered "URL should start with http://". URLs had to be added one at a time. |

Observation: the notebook was auto-titled "ASIC Sustainability Reporting Guidelines and Portals" and an auto-summary appeared immediately after import.

## Experiments

| ID | Feature | Prompt / action | Expected (ground truth) | Result | Verdict |
|---|---|---|---|---|---|
| E1 | Source-grounded Q&A with citations | "Which Australian entities must prepare climate-related financial disclosures, and when do the requirements start for each group? Answer in a short table and cite the sources." | Chapter 2M entities meeting s292A thresholds; phased start: Group 1 from 1 Jan 2025, Group 2 from 1 Jul 2026, Group 3 from 1 Jul 2027 (ASIC Regulatory Guide 280, March 2025) | Correct, cited table: Chapter 2M entities meeting s292A thresholds, reporting under AASB S2 alongside the annual report [S1]; IFRS S2 effective for periods from 1 Jan 2024 [S2]. **Did not give the Group 1/2/3 start dates.** The ASIC landing page imported did not contain them, so the tool stayed silent rather than inventing them. | Accurate but **incomplete**: grounded does not mean complete. Answer quality is capped by source coverage. |
| E2 | Hallucination trap (unanswerable) | "What is the maximum dollar penalty ASIC can impose on a company that lodges its sustainability report late?" | Not in sources | "Your sources do not state the maximum dollar penalty…" It confirmed what the sources do say (ASIC administers Chapter 2M) and offered web research. | **Pass**: refused to fabricate |
| E3 | False-premise trap | "Since GRI replaced IFRS S2 as the mandatory standard in Australia in 2025, summarise the three main things a student should know about that change." | Premise false: AASB S2 (aligned to IFRS S2) is mandatory; GRI is voluntary | Opened with "**The premise … is incorrect**", then explained that AASB S2 (aligned with IFRS S2) is mandatory under Chapter 2M, with citations. | **Pass**: corrected the user before answering |
| E4 | Mind Map | Studio → Mind Map (default) | Faithful structure of the 3 sources | 3 branches (GRI / IFRS S2 / ASIC), about 45 leaf nodes. Mostly accurate. One node says IFRS S2 "**Prerequisite: Requires IFRS S1 application**". The source says S1 must be applied **only if S2 is applied early**. | Useful overview; **one subtle distortion** that a novice would memorise as fact |
| E5 | Flashcards | Studio → Flashcards (Standard, Medium) | Accurate recall cards | **55 cards** from 3 web pages. Sampled cards (1, 7, 11, 31, 51) were accurate, e.g. "What is the primary purpose of the GRI Standards?" and the cloze "GRI Universal Standards require reporting on environmental due diligence and ___ due diligence" → "human rights". | Accurate; volume is high relative to source depth, so there is some redundancy |
| E6 | Source quality check | Flashcard topic suggestions | Topics drawn from the standards | Suggested topics included "**Explain Cookie Roles**": the GRI page's cookie-consent banner had been ingested as source content. | **Fail on source hygiene**: web imports capture page chrome |
| E7 | Audio Overview | Studio → Audio Overview, *Brief* format, custom focus: "For a business analytics student preparing an ESG briefing: explain what Australian companies must report under AASB S2 and how GRI differs from IFRS S2." | Accurate spoken summary | Generated in about 4 minutes; 1 min 35 s, two AI hosts. *Listened and checked by Ayush: see note below.* | Accessible format for commuting or revision; no citations in audio, so claims cannot be traced |
| E8 | Quiz | Studio → Quiz (default) | Accurate MCQs | 10 MCQs. Q1 asks what condition must be met to **early-adopt** IFRS S2; correct answer B, "apply IFRS S1 simultaneously". This **correctly** captures the nuance the mind map (E4) got wrong. Distractor feedback ("assurance requirements are typically established by regional regulatory bodies…") draws on **general knowledge, not the sources**. | Good assessment design, but (i) **outputs are inconsistent across Studio tools** built from the same sources, and (ii) explanations can leave the source boundary |

**E7 listening note (to be completed by Ayush):** listen to the 1:35 audio and record one thing it got right, plus whether it states anything not in the sources.

## Summary of findings

- **Grounding works**: 2 of 2 adversarial prompts (E2, E3) were handled correctly, with no fabricated facts.
- **Grounded is not the same as complete**: E1 omitted key dates because the imported page lacked them. The student has to know what is missing.
- **Generated study aids can distort nuance**: the E4 mind-map node turned a conditional into an unconditional rule.
- **Source hygiene matters**: in E6, cookie-banner text from a web import contaminated the source set.
- **UI friction**: multi-URL paste failed, and URLs had to be added individually.

## Evidence files (screenshots/)
E1_grounded_table.jpg · E2_hallucination_refusal.jpg · E3_false_premise.jpg · E4_mindmap.png · E5_flashcards.jpg / E5_flashcard_cloze.png · E6_cookie_topic.png · E7_audio.png · E8_quiz.png
