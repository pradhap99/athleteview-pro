# Throughline — Dependency & Model-Weight License Allowlist

## Policy

Ship **only MIT / Apache-2.0 / BSD** licensed dependencies and model weights. Anything else — AGPL, non-commercial, source-available, gated, or custom licenses — requires **explicit human approval** before it enters the codebase or the serving plane.

This is enforced structurally, not by convention:
- A **loader allowlist** restricts which model checkpoints can be loaded.
- A **CI license check** fails the build on any non-allowlisted dependency license.
- A **per-checkpoint license register** is maintained (this file); CC-BY models require a published NOTICES / attribution page.
- Never train shipped models on scraped copyrighted screenplay corpora; use customer opt-in or licensed/cleared data. Open corpora are for internal eval only.

Sources: PRODUCT_SPEC §12 (AI/ML architecture, feature→model→license table), §14 (model licensing rules), and Appendix A (model licensing register). Verify each license against the current HuggingFace model card / GitHub LICENSE file at build time — model licensing shifts fast in 2026.

---

## Allowed model weights

| Model | License | Use |
|---|---|---|
| Qwen3 (8B–32B) | Apache-2.0 | Reasoning + structured JSON (XGrammar-constrained); small-model-first routing |
| Qwen3-Embedding | Apache-2.0 | Embeddings for hybrid dense+keyword search |
| Qwen2.5-VL-7B / 32B | Apache-2.0 | (Future / Phase 3) dailies vision-language tagging |
| DeepSeek-V3.2 | MIT | Reasoning + structured JSON (escalation path) |
| DeepSeek-R1 | MIT | Reasoning |
| Phi-4-mini | MIT | Reasoning + structured JSON (small-model-first) |
| BGE-M3 | MIT | Embeddings / hybrid search |
| GLiNER v2.1 | Apache-2.0 | Zero-shot element tagging (pin the v2.1 Apache weights) |
| faster-whisper | MIT | (Phase 3) dailies transcription |
| pyannote community-1 | CC-BY-4.0 (gated, **attribute**) | (Phase 3) speaker diarization — requires attribution / NOTICES page |
| SAM 2.1 | Apache-2.0 | (Phase 3) segmentation |
| SigLIP 2 | Apache-2.0 | (Phase 3) vision |
| DINOv2 | Apache-2.0 | (Phase 3) vision features (note: DINOv**3** is denied — see below) |
| Grounding DINO | Apache-2.0 | (Phase 3) open-vocab detection |
| OWLv2 | Apache-2.0 | (Phase 3) open-vocab detection |
| PySceneDetect | BSD | (Phase 3) shot / scene-cut detection |
| PaddleOCR | Apache-2.0 | Document OCR/KIE (invoices, timecards, legacy call sheets) |
| Donut | MIT | Document OCR/KIE |
| Granite Guardian | Apache-2.0 | Grounded-answer safety (groundedness / hallucination gate) |

---

## Allowed key dependencies

- **FastAPI** (MIT) — backend API framework (modular monolith).
- **SQLAlchemy** (MIT) — ORM / data access.
- **Google OR-Tools (CP-SAT)** (Apache-2.0) — schedule optimization (feasibility + objective).
- **pdfplumber** (MIT) — deterministic PDF script parsing (format fidelity, never AI).
- **screenplay-tools** (MIT) — deterministic `.fdx` / Fountain script parsing.
- **GLiNER** (Apache-2.0) — zero-shot NER library for element tagging.
- **spaCy** (MIT) — NLP pipeline supporting element tagging.
- **Presidio** (MIT) — PII detection/redaction before storage and model calls.
- **pgvector** (PostgreSQL License, BSD-style) — vector search inside Postgres (with pgvectorscale).
- **vLLM** (Apache-2.0) — default model serving (OpenAI-compatible endpoint).
- **SGLang** (Apache-2.0) — prefix-heavy serving.
- **llama.cpp** (MIT) — local serving.
- **Ollama** (MIT) — local serving.
- **Yjs** (MIT) — CRDT for multiplayer editing + presence.
- **Next.js** (MIT) — frontend (App Router).
- **React** (MIT), **TanStack Query / Virtual** (MIT), **Zustand** (MIT), **shadcn/ui** (MIT), **Tailwind CSS** (MIT), **cmdk** (MIT) — frontend stack.
- **XGrammar** (Apache-2.0) — constrained JSON decoding.

(All above are MIT / Apache-2.0 / BSD-style and pass the policy. Confirm exact license at add time; the CI check is authoritative.)

---

## DENY / AVOID

Do **not** add these without explicit human approval. Substitutes for the intended capability are in the allowed tables above and in PRODUCT_SPEC §12 / Appendix A.

### AGPL — would force open-sourcing our code
- **Ultralytics YOLO** (object detection)
- **PyMuPDF** (PDF parsing) — use pdfplumber instead
- **aeneas** (forced audio alignment) — use WhisperX / MFA instead

### Non-commercial weights — not license-cleared for a commercial product
- **InsightFace recognition weights** — and note face **recognition** is a non-goal entirely (see below)
- **LayoutLMv3** (document layout)
- **Jina v3** (embeddings) — use Qwen3-Embedding / BGE-M3 instead
- **Canary-1b** (non-flash variant) — transcription
- **Qwen2.5-VL-3B** — the 3B checkpoint is non-commercial; the 7B / 32B checkpoints are Apache-2.0 and allowed

### Gated / custom license — requires approval and review
- **DINOv3** (custom/gated) — DINOv2 (Apache-2.0) is the allowed substitute

### Capability that is out of scope regardless of license
- **Face recognition** is a **non-goal** — BIPA (written consent before capture), GDPR Art. 9 (explicit consent + DPIA), and EU AI Act high-risk obligations for post-hoc identification (phasing in from 2 Aug 2026) make it a legal/regulatory liability. Face **detection** only, if ever needed — never recognition/identification.
