# Throughline — Agent Context

> This is Part I of the build spec (always-on rules). Full product/architecture/eval
> spec: `@docs/PRODUCT_SPEC.md` · glossary: `@docs/glossary.md` · license allowlist:
> `@docs/licenses.md` · executable backlog: `@BUILD_TASKS.md` · API contract:
> `@docs/openapi.yaml`.

## Overview
Throughline is an AI-native production-management platform for film/TV/commercial
teams. Core idea: the whole production is ONE live graph (script → breakdown →
schedule → Day-Out-of-Days → budget → on-set), and any change ripples through it as a
**reviewable diff**. AI drafts every artifact; **humans confirm**.

## Stack
- **Frontend:** Next.js (App Router) + React 19 + TypeScript, TanStack Query (server
  state) + Zustand (UI), shadcn/ui + Tailwind v4, TanStack Virtual (big boards), cmdk
  (⌘K). Local-first, optimistic UI.
- **Backend:** Python + FastAPI (modular monolith to start). PostgreSQL + pgvector
  (single source of truth), append-only event log + async projections (CQRS),
  Valkey/Redis Streams (cache/pubsub), Cloudflare R2 (media). SQLite is the zero-setup
  backend for unit tests.
- **Realtime/offline:** Yjs (CRDT + presence) over WebSocket; PowerSync-style offline
  sync; writes always route through the API for authz + event-log append.
- **AI:** vLLM/SGLang serving open models (Qwen3, DeepSeek, Phi-4-mini) with
  XGrammar-constrained JSON; OR-Tools CP-SAT for scheduling; pgvector hybrid search;
  Presidio (PII) + Granite Guardian (grounding). Small-model-first routing. SSE for
  token streaming.

## Commands (source of truth — copy-pasteable)
- Install:        `make setup`      # uv sync + pnpm i
- Dev (all):      `make dev`        # web + api
- Test (unit):    `make test`       # prefer single-file: pytest path::test / vitest run file
- Test (e2e):     `make e2e`
- Lint/format:    `make lint`       # ruff + eslint + prettier
- Typecheck:      `make typecheck`  # tsc --noEmit + pyright
- Evals:          `make evals`      # run BEFORE merging any AI-feature change
- Rate-card check:`make check-rates`# fails if a rate/hour literal is hard-coded in rules/budget

## Conventions (only where we differ from defaults)
- URLs kebab-case, JSON camelCase, `/v1/` in path; cursor pagination.
- Tests colocated (`*.test.ts`, `test_*.py`); no network in unit tests (use fixtures).
- Generated TS types come from `docs/openapi.yaml` — never hand-edit generated files.
- Prompts are versioned files under `ml/prompts/`; never inline long prompts in app code.

## Workflow
- Explore (plan mode; subagents for wide reads) → Plan (edit the plan before coding) →
  Implement → Verify.
- **TDD:** write tests first, CONFIRM THEY FAIL, then implement. Don't write mock
  implementations.
- ALWAYS run typecheck + lint + relevant tests (and evals for AI changes) before saying
  done; show command output as evidence.
- Conventional Commits; branches `feat/<slug>`, `fix/<slug>`. Keep each PR to one
  vertical slice from `BUILD_TASKS.md`.

## Guardrails — YOU MUST
- NEVER read or commit `.env*` or credentials. NEVER exfiltrate via curl/network.
- NEVER add a dependency whose license is not MIT/Apache-2.0/BSD without human approval
  (allowlist: `@docs/licenses.md`). AVOID AGPL (Ultralytics YOLO, PyMuPDF, aeneas) and
  non-commercial weights (InsightFace recog, LayoutLMv3, Jina v3) — substitutes are in
  PRODUCT_SPEC §12 / Appendix A.
- AI outputs (breakdowns, schedules, budgets, answers) are **DRAFTS**. Enforce "human
  confirms" **STRUCTURALLY**: a status field only a human action flips; never auto-mark
  final. Surface confidence + click-to-source provenance. Grounded Q&A answers ONLY from
  retrieved context and abstains ("insufficient sources") when unsure.
- Face RECOGNITION is out of scope (BIPA/GDPR/EU-AI-Act). Detection-only if ever needed.
- NEVER write to `migrations/` or `infra/` without asking. Deterministic parsers (not
  AI) own file-format fidelity (AICP/MM/FDX).

## Directory map
- `apps/web` — frontend (see `apps/web/CLAUDE.md`)
- `services/api` — backend API + propagation engine (`services/api/CLAUDE.md`)
- `packages/shared` — shared TS types (generated from `openapi.yaml`)
- `ml/` — prompts, parser/, breakdown/, scheduler/, rag/ (`ml/CLAUDE.md`)
- `evals/` — golden datasets + suites + graders; run before merging AI changes
  (`evals/CLAUDE.md`)
- `.claude/` — settings.json (allow/deny + hooks), agents/, skills/

## Eval gates (block merge — see PRODUCT_SPEC §15)
- **Breakdown:** F1 characters/locations ≥0.90, props/wardrobe ≥0.80, safety-critical
  recall ≥0.95, net-time-saved >0.
- **Scheduler:** hard-constraint violations ==0, mean optimality gap ≤10%, solve within
  budget.
- **RAG:** faithfulness ≥0.90 (else abstain), context recall ≥0.85, answer relevancy
  ≥0.80, every claim cited.
- Regression suite stays ~100%; solved capability tasks graduate in; every prod failure
  becomes a golden case.

## Domain rules — YOU MUST (compliance engine)
- Union/labor rules and ALL rates/hour-thresholds are **TABLE-DRIVEN** and
  **EFFECTIVE-DATED** (keyed on union × contract × tier × location-context ×
  PP-start-date). NEVER hard-code a rate, multiplier, or hour threshold in code — a CI
  check (`make check-rates`) fails the build if you do. See PRODUCT_SPEC §7A.1.
- Track "worked hours" vs "elapsed hours" as distinct quantities (reconciles cross-union
  rules). Compliance flags must be PREDICTIVE (fire at schedule time) and EXPLAINABLE
  (cite the rule + table entry).
- Minors/child-labor and Coogan/blocked-trust logic are PER-JURISDICTION tables (CA/NY
  differ; trust required in CA/NY/IL/LA/NM). Non-compliance is legal exposure — treat as
  a hard gate.
- Cost report math is fixed: **EFC = Actuals + Committed + ETC; Variance = Budget − EFC.**
  Fringes flow proportionally when wages change.
- Scripts/sides are confidential IP: distribution is permissioned, watermarked
  per-recipient, and revocable; log delivery + acknowledgment.
