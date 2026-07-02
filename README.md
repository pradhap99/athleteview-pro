# Throughline

**The AI-native operating system for film/TV/commercial production.**

One *live production graph* from script to shoot day: change anything — recast a role,
move a day, edit a rate — and it ripples through breakdown → schedule → Day-Out-of-Days →
budget → call sheets as a **reviewable diff**. AI drafts every artifact; **humans
confirm**. Everything round-trips losslessly with the tools the industry already requires
(Movie Magic, AICP, Final Draft).

> **Working title:** Throughline (trademark/domain check pending; fallback "Keyframe").

---

## Why

Production runs on a relay race of disconnected documents — a breakdown in one app, a
schedule in a second, a budget in a third, call sheets in a fourth — stitched together by
hand. Every handoff is lossy; every change is re-keyed. Throughline replaces the relay
race with one normalized graph where a scene is a *node* whose cast, props, location, day,
and dollars are *edges*. Change the node and the graph recomputes, showing the diff before
anything commits.

See `docs/PRODUCT_SPEC.md` for the full PRD, architecture, data model, API, and eval plan.

## Architecture at a glance

| Layer | Choice |
|---|---|
| Frontend | Next.js (App Router) + React 19 + TS · TanStack Query + Zustand · shadcn/Tailwind · cmdk (⌘K) · local-first, optimistic |
| Backend | Python + FastAPI (modular monolith) · **PostgreSQL** single source of truth · append-only **event log → async projections** (CQRS) · pgvector · Valkey/Redis · Cloudflare R2 |
| Realtime | Yjs (CRDT + presence) over WebSocket · PowerSync-style offline sync |
| AI | vLLM/SGLang serving open, permissively-licensed models (Qwen3, DeepSeek, Phi-4) · XGrammar JSON · **OR-Tools CP-SAT** scheduling · pgvector hybrid search · Presidio + Granite Guardian |

Design principles: **one graph not many files · AI drafts, humans confirm · explainable by
default · instant (<100 ms) · keyboard-first · revision-native · offline-first on set ·
interoperate don't imprison · utility AI only.**

## Repository layout

```
throughline/
  CLAUDE.md                 # agent context & guardrails (Part I of the spec)
  BUILD_TASKS.md            # executable, eval-gated backlog (Part III)
  docs/                     # PRODUCT_SPEC.md · glossary.md · licenses.md · openapi.yaml
  apps/web/                 # Next.js frontend
  services/api/             # FastAPI + event log + projections + propagation + rules engine
  packages/shared/          # shared TS types (generated from openapi.yaml)
  ml/                       # deterministic parsers, breakdown, scheduler (CP-SAT), rag
  evals/                    # golden datasets + suites + graders (quality firewall)
  scripts/                  # dev tooling (rate-card guard, etc.)
```

## Quickstart

```bash
make setup        # uv venv + editable install (+ web deps if pnpm present)
make test         # python unit tests
make lint         # ruff check + format
make typecheck    # pyright
make check-rates  # fails if a union rate/threshold is hard-coded (see below)
make dev          # api (:8000) + web (:3000)
```

Python only (no Node needed for the backend/ML slices):

```bash
uv venv .venv --python 3.11
uv pip install --python .venv -e ".[dev]"
.venv/bin/pytest
```

## What's built so far

This repo is being built **one eval-gated vertical slice at a time** (see
`BUILD_TASKS.md`). Implemented and tested today:

- **0.1 Foundation** — monorepo, Makefile, CI, guardrails (`.claude/settings.json`), the
  rate-card CI guard.
- **0.2 Graph core** — append-only event log + async projections + graph snapshot
  reconstruction (`GET /v1/projects/{id}/graph?at=eventId`) + propose/confirm/reject
  change diffs. "AI drafts, humans confirm" is enforced **structurally** — a draft's
  status can only be flipped by an explicit human action.
- **1.1 Script ingest** — deterministic Fountain + Final Draft (`.fdx`) parser →
  scene nodes (int/ext, location, time-of-day, page-eighths, characters) with lossless
  `.fdx` round-trip. (No AI touches format fidelity.)
- **2.1 Scheduler** — OR-Tools CP-SAT stripboard: assign scenes to days minimizing
  company moves + cast hold-days under availability/turnaround constraints; DOOD derived
  (work/hold/travel).
- **5.1 Rules engine** — table-driven, effective-dated union/labor rules engine
  (SAG-AFTRA/DGA/IATSE/Teamsters) with worked-vs-elapsed hour tracking. **No rate or hour
  threshold is hard-coded** — all live in effective-dated rate-card tables, enforced by
  `make check-rates`.
- **5.3 Budget + cost report + hot costs** — budget lines with fringes (caps, proportional
  flow) and full derivations; weekly cost report with the fixed math
  (**EFC = Actuals + Committed + ETC; Variance = Budget − EFC**) rolled up
  ATL/BTL/Post/Other; daily hot costs priced from rules-engine flags (OT, meal penalties,
  rest invasion, 6th/7th day) — every dollar cites its table entry.
- **2.3 (AICP half)** — AICP bid-form (A–W) export/import with lossless round-trip on core
  fields + CSV. Movie Magic `.mmb` stays deferred pending format legal review.
- **2.2 $-ripples** — rescheduling a scene now previews the money: hold-day/location-day
  deltas priced from driver-linked budget lines ("+$850 to the top sheet") before anything
  commits.
- **1.3 (server half)** — script revision diff: re-importing a revised draft yields an
  element-level proposed diff (scenes added/removed/changed, character adds/drops) that
  applies only on human confirm.

AI-model slices (breakdown NER/LLM, RAG grounded Q&A, OCR actuals) are **scaffolded** —
seams, versioned prompts, and eval harnesses are in place; they require a model-serving
endpoint (vLLM/SGLang) to run end-to-end and must pass their eval gates before merge.

## The quality firewall

AI features do not merge until they pass eval gates (see `docs/PRODUCT_SPEC.md` §15):
breakdown F1 ≥0.90 (chars/locations) & safety-critical recall ≥0.95; scheduler
hard-constraint violations ==0 & optimality gap ≤10%; RAG faithfulness ≥0.90 or it
abstains. Run `make evals`.

## License

Apache-2.0. Ships only Apache/MIT/BSD model weights and dependencies — see
`docs/licenses.md`. Face **recognition** is a non-goal (BIPA/GDPR/EU-AI-Act); detection
only if ever needed.
