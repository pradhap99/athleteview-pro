# Throughline — Build Backlog (executable, eval-gated)

> Part III of the build spec. Build **one slice at a time, top to bottom**. Each is
> scoped to a single reviewable PR and ends with a verification/eval gate. Use plan mode
> first; write tests/evals first; show verification output as evidence before moving on.
> Full context: `@docs/PRODUCT_SPEC.md` · rules: `@CLAUDE.md`.

Convention per task — **Goal · Touch · Out of scope · Acceptance criteria · Verify**.

### Status legend
- ✅ implemented + tested in this repo
- 🟡 scaffolded (structure/seams/prompts in place; needs model serving or further work)
- ⬜ not started

---

## EPIC 0 — Foundation & repo

### 0.1 Monorepo + tooling + CI skeleton — ✅
- **Goal:** monorepo (`apps/web`, `services/api`, `packages/shared`, `ml`, `evals`) with
  make targets, lint/typecheck/test, CI running them.
- **Touch:** repo root, `Makefile`, CI config, `.claude/settings.json` (allow/deny + hooks).
- **Out of scope:** any product feature.
- **AC:** `make setup|dev|test|lint|typecheck` all run; CI green on an empty app;
  deny-rules block `.env*` reads and non-allowlisted licenses; "AI output = draft"
  documented.
- **Verify:** CI passes; `make lint typecheck test` clean.

### 0.2 Postgres schema + event log + projections skeleton — ✅
- **Goal:** the core data model (§9) + append-only `events` + a projection runner.
- **Touch:** `services/api` migrations, event/projection modules.
- **AC:** tables from §9 exist; writing an event triggers a projection; a snapshot
  endpoint reconstructs state `?at=eventId`; RBAC/tenant isolation in place.
- **Verify:** unit tests for event→projection; a "reconstruct at past event" test passes.

---

## EPIC 1 — Script → breakdown (P0)

### 1.1 Script ingest (FDX/Fountain/PDF) → scenes — ✅ (FDX + Fountain) / 🟡 (PDF)
- **Goal:** deterministic parser to Scene nodes. **Touch:** `ml/` (parser via
  screenplay-tools/pdfplumber), api ingest endpoint.
- **AC:** standard `.fdx` and Fountain import to scenes with int/ext, location,
  time-of-day, page-eighths, characters; PDF sides supported; parser is deterministic
  (no AI).
- **Verify:** golden parse fixtures; round-trip export to `.fdx` lossless on core fields.

### 1.2 Breakdown Agent (LLM draft + confidence + provenance) — 🟡
- **Goal:** GLiNER v2.1 + spaCy candidates → Qwen3 (XGrammar JSON) reconcile → typed
  elements with confidence + source span. **Touch:** `ml/breakdown`, api,
  `evals/datasets/breakdown`.
- **AC:** every element is a draft (accept/reject) with click-to-source; low-confidence
  flagged; safety-critical types tuned for recall; nothing auto-final.
- **Verify (EVAL GATE):** on the gold set — F1 characters/locations ≥0.90, props/wardrobe
  ≥0.80, safety-critical recall ≥0.95; timed QA study shows **net time saved > 0**.
  `make evals` green.

### 1.3 Breakdown review UI + revision diff — 🟡 (revision diff + apply live server-side; confirm-queue UI pending)
- **Goal:** fast keyboard confirm queue; re-import a revision → element-level diff
  (new/changed/deleted) + downstream ripple. **Touch:** `apps/web`, api.
- **AC:** confirm/reject via keyboard; revision diff renders; confirmed elements unlock
  scheduling/budget; status flips only by human action.
- **Verify:** e2e: import → confirm → re-import revision → diff shown; unit tests for
  diff logic.

---

## EPIC 2 — Schedule, DOOD, budget (P0 spine)

### 2.1 CP-SAT scheduler + DOOD derivation — ✅
- **Goal:** OR-Tools model — assign scenes to days minimizing company moves + cast
  hold-days under availability/capacity/turnaround; derive DOOD. **Touch:**
  `ml/scheduler`, api, `evals/datasets/scheduler`.
- **AC:** stripboard from confirmed elements, manually re-orderable; DOOD distinguishes
  work/hold/travel; a change yields a proposed re-board diff (never silent); hard
  constraints never violated.
- **Verify (EVAL GATE):** instance bank — hard-constraint violations ==0; mean optimality
  gap ≤10%; solve within budget (PAR-2). Regression asserts feasibility 100%.

### 2.2 Reactive propagation + ripple preview — 🟡 (engine ✅ incl. hold-day/location-day/$ deltas from driver-linked budget lines; drag-overlay UI + OT/permit signals pending)
- **Goal:** change one node → dependents recompute as a reviewable diff; drag-a-scene
  shows consequences before drop. **Touch:** api propagation engine, `apps/web` overlay.
- **AC:** propagation always produces a diff to accept/reject; ripple preview shows new
  hold days / OT / permit conflicts / $ delta before commit; accepted change appends an
  event.
- **Verify:** unit tests for cascade correctness; e2e drag-with-preview.

### 2.3 Budget + AICP/Movie Magic interop + "cost of this decision" — 🟡 (budget lines linked to graph drivers, $ delta on reschedule, derivations, AICP A–W export/import round-trip + CSV; **Movie Magic .mmb deferred pending the legal review flagged below**)
- **Goal:** budget derived from graph; AICP (A–W) + MM (.mmb) export/round-trip; live $ +
  delta on every object. **Touch:** api budget, ml (explainable estimates), interop,
  `apps/web` overlay.
- **AC:** budget lines link to breakdown/schedule (change surfaces delta); AICP + MM
  round-trip lossless on account codes/fringes/globals; every figure expands to
  derivation; estimate/committed/actual/EFC tracked.
- **Verify:** round-trip fixtures for AICP + `.mmb`; snapshot tests for derivations.
  **Legal review of MM format is a gating dependency — flag to human.**

---

## EPIC 3 — Speed, collaboration, search (P1)

### 3.1 Local-first, optimistic UI shell + ⌘K + virtualized board — 🟡
- **Goal:** the app *feels* instant (§8 targets). **Touch:** `apps/web`.
- **AC:** interaction p95 <100 ms (target 50–60) on the stripboard/budget; ⌘K palette
  operates on the graph; big boards virtualized; optimistic updates with background sync.
- **Verify:** perf test asserting interaction budget; keyboard-only e2e of core flows.

### 3.2 Real-time multiplayer (Yjs) + presence — ⬜
- **AC:** two clients co-edit the board/budget; presence/cursors; writes route through API
  for authz + event append; conflicts surface as diffs, never silent overwrite.
- **Verify:** multi-client integration test; conflict test.

### 3.3 Production-wide hybrid search (+ grounded Q&A) — 🟡
- **Goal:** pgvector + keyword hybrid over scripts/notes/docs; grounded Q&A with
  citations. **Touch:** api, `ml/rag`, `evals/datasets/rag`.
- **AC:** hybrid results respect RBAC; Q&A answers only from retrieved context, cites
  source nodes, abstains when unsure.
- **Verify (EVAL GATE):** faithfulness ≥0.90 (else abstain), context recall ≥0.85, answer
  relevancy ≥0.80, every claim cited.

---

## EPIC 4 — On set + the loop (P1→P2)

### 4.1 Call sheets + delivery/ack tracking + per-role copilots — ✅ (weather = provider seam; LLM phrasing of nudges = ml seam)
- **AC met:** call sheets auto-populate from the graph — day's scenes in order, cast with
  DOOD codes, location day-info (sun/magic hour/hospital/parking via 6.3), company move
  into the day; per-recipient ack tokens (viewers need no seat) with delivery tracking; a
  re-publish supersedes the prior revision and **re-notifies only recipients whose own
  day changed** (identical re-publish notifies no one; a call-time change notifies all);
  deterministic per-role copilots (coordinator: unacked chase; 1st AD: company moves;
  LP: accounts trending over) — every nudge cites its graph fact.

### 4.2 Mobile offline + live wrap loop (P2) — ⬜
- **AC:** AD taps scenes complete + DIT confirms footage → schedule reflows,
  days-vs-budget recompute, DPR + next call sheet auto-draft; fully offline, syncs on
  reconnect; never mutates verified media.
- **Verify:** offline→reconnect sync test; wrap-loop e2e.

### 4.3 What-if branches + Time Machine (P2) — 🟡 (event-log substrate in place)
- **AC:** fork graph, edit branch, side-by-side diff (budget/DOOD/calendar), merge/discard;
  timeline scrubber reconstructs any past state with blame; restore as branch.
- **Verify:** branch-diff-merge test; reconstruct-at-event test.

---

## Cross-cutting (every AI PR)
- Add/extend golden cases in `evals/datasets/<feature>/`; capability tasks graduate into
  the regression suite; every production failure becomes a golden case.
- Run `make evals`; block merge on the gates above; track latency/tokens/cost; read
  transcripts before trusting scores.
- Adversarial review subagent (fresh context) reviews the diff against this task's AC
  before merge.

---

## EPIC 5 — Compliance & production accounting (P0 table stakes)

### 5.1 Table-driven, effective-dated rules engine — ✅
- **Goal:** the union-rules core — configurable tables keyed on union × contract × tier ×
  location-context × PP-start-date; track worked-vs-elapsed hours + per-person running
  counters. **Touch:** `services/api/rules`, ml (NL rule authoring optional),
  `evals/datasets/rules`.
- **Out of scope:** hard-coded rates/thresholds (forbidden — all `[RATE CARD]`).
- **AC:** rules resolve from tables by effective date; worked vs elapsed hours tracked
  distinctly; changing signatory/contract reloads the rule set; every flag explains the
  rule + cites the table entry.
- **Verify:** unit tests per union (SAG/DGA/IATSE/Teamsters) for turnaround, meal penalty,
  OT tiers, 6th/7th day; a "change effective date → different threshold" test.

### 5.2 Predictive compliance flags + minors/Coogan — 🟡
- **AC:** at schedule time, flag forced-call/meal-penalty/turnaround/minor-hours breaches
  before commit; per-jurisdiction minors table (CA/NY age bands, hard caps, teacher
  ratios, permitted windows) + Coogan/blocked-trust logic (CA/NY/IL/LA/NM); nothing
  hard-coded.
- **Verify:** scenario tests: a call that forces a meal penalty is flagged; a minor
  scheduled past cap is blocked; jurisdiction swap changes limits.

### 5.3 Budget structure + fringes + weekly cost report + hot costs — ✅ (ATL/BTL/Post/Other + free-form CoA codes; fringes with caps flow proportionally; EFC = Actuals + Committed + ETC, Variance = Budget − EFC; hot costs priced from rules-engine flags — feeds from Exhibit G once 5.5 lands; every figure carries a derivation)
- **AC:** ATL/BTL/Post/Other structure with configurable CoA; fringes engine
  (rate/unit/cap, proportional on wage change); weekly cost report with
  **EFC = Actuals + Committed + ETC; Variance = Budget − EFC**; daily hot costs from
  prior-day Exhibit G + rules engine; every figure expands to derivation.
- **Verify:** cost-report reconciliation tests; hot-costs regenerate from a fixture
  Exhibit G; fringe-cap tests.

### 5.4 POs / commitments / check requests / petty cash — ✅
- **AC met:** approved-uninvoiced PO = committed (feeds the cost report), goods receipt +
  invoice complete a **3-way match** (mismatch → refused, all three legs cited) → actual;
  check requests route through an ordered sign-off chain (dept head → UPM → …), booking
  only on completion; petty-cash envelopes reconcile to the cent (receipts + returned =
  float) and refuse further receipts once reconciled.

### 5.5 Exhibit G + cost-coded timecards + start packets + payroll handoff — ✅ (MM budget/schedule round-trip stays deferred pending legal review)
- **AC met:** Exhibit G renders to the guild form (status codes W/SW/SWF/WF/H/T/TR/R/F,
  report/dismiss, tenths of an hour, MPV count + forced-call from the rules engine, minor
  flag, wardrobe/stunt adjustments, performer e-signature) and is the feed hot costs
  regenerate from; timecards compute against the rules engine (auto-recalc on read),
  split across account codes without cent drift, and route an ordered approval chain;
  deal memos/start packets are structured events with box/kit as a separate
  taxability-flagged line (accountable plan → non-taxable); approved timecards export in
  a payroll-ready schema (EP / Cast&Crew / Wrapbook) with wage-type breakdown + cost
  codes + union P&H wage-base summary.

---

## EPIC 6 — Production workflow table stakes (P0/P1)

### 6.1 Colored-page script revisions (P0) — ✅ (revision clouds / as-broadcast export = P2, out of scope)
- **AC met:** color order White→Blue→…→Tan→Double White→Triple… enforced; releasing a
  revision **locks pages** — scenes inserted after N become NA/NB and before the first
  become A1 (existing numbers never shift), applied automatically to revision diffs;
  auto revision-mark asterisks on changed lines (deterministic line diff); revision slug
  (color + date) + full history on the graph.
### 6.2 Sides + secure watermarked distribution (P0) — ✅
- **AC met:** sides auto-generate from a shooting day's scenes in shooting order
  (scene-number order until call sheets land in 4.1) + character-filtered in one click;
  recipient name/email + link id burned into **every page**; capability links (token =
  credential, viewers need no seat) with expiry + one-click revocation + download/print
  flags; every open and acknowledgment is an event — tracking endpoint surfaces the
  chase-before-call list.

### 6.3 Location management (P0) — ✅ (weather = provider seam at the call-sheet layer; neighborhood notification = P2)
- **AC met:** per-location doc vault (release/permit/**COI with additional-insured +
  expiry + liability limit**) with most-urgent-first expiry alerts; deterministic NOAA
  sunrise/sunset + magic hour (±few min, unit-tested against known LA values) +
  parking/basecamp/nearest-24h-hospital as the call-sheet day-info block; company moves
  derived from consecutive schedule days with different primary locations.
### 6.4 Cast & crew DB + deal memos + e-signature (P0) — ✅
- **AC met:** org-scoped cross-project contacts DB (person once, reused across shows;
  roles/union/agency/default rates; **engagement history assembled from deal memos across
  every show in the org**); deal-memo templates merge defaults into new memos (explicit
  values win, missing terms 422); start packets per hire (5.5); e-signature with an
  ORDERED signing chain, out-of-order refusal, completion state, and a pending/reminders
  feed (who's next, waiting since).
### 6.5 Tax-incentive estimator (P1) — ⬜
### 6.6 Clearances / cue sheets / releases; safety; green (P1/P2) — ⬜

---

## Cross-cutting for EPIC 5/6
- All rates/thresholds are **[RATE CARD]** in effective-dated tables — a CI check
  (`make check-rates`) fails the build if a rate/hour-threshold literal appears in
  rules/budget code.
- Compliance flags must be **explainable** (cite the rule + table entry) and
  **predictive** (fire at schedule time, not only at timecard time).
