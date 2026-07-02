# Throughline — Product & Technical Specification

> Part II of the build spec. Companion files: root CLAUDE.md (Part I) and BUILD_TASKS.md (Part III).

# Throughline — Master Build Specification
### PRD · Functional Specs · Technical Architecture · Eval Plan · Build Backlog
**Version 1.1 — July 2026 (adds §7A essential Hollywood features) · Working title: Throughline (trademark check pending) · Prepared for hand-off to Claude Code**

---

## 0. How to use this document (read this first)

This is a single, self-contained build specification meant to be handed to **Claude Code**. It fuses the product requirements (what/why), the functional specs (behavior + acceptance criteria), the technical architecture (how), and the evaluation plan (how we know it's good).

**Recommended workflow with Claude Code:**
1. Drop this file in the repo as `docs/PRODUCT_SPEC.md`, plus the companion `CLAUDE.md` (repo root) and `BUILD_TASKS.md` (the executable, eval-gated backlog).
2. Build **one vertical slice at a time** from `BUILD_TASKS.md`, in the order given. Each task is scoped to be reviewable in a single PR and ends with an explicit verification/eval gate.
3. For each task: use **plan mode** first (explore → plan), write **tests/evals first**, implement, then run the verification command and show the output as evidence before moving on.
4. AI features must pass their **eval gates** (Section 15) before merge. Quality regressions block the release.

**The one-sentence product:** Throughline is the AI-native operating system for film/TV/commercial production — one *live production graph* from script to shoot day, where changing anything ripples through breakdown, schedule, Day-Out-of-Days, and budget instantly, AI drafts every artifact and humans confirm, and everything round-trips losslessly with the tools the industry already requires (Movie Magic, AICP, Final Draft).

---

## 1. Executive summary

Production still runs on a relay race of disconnected documents — a breakdown in one app, a schedule in a second, a budget in a third, call sheets in a fourth — stitched together by hand. Every handoff is lossy, every change is re-keyed, and the industry loses roughly **10% of budget** to that friction. The most-cited source of on-set stress is not money; it is miscommunication and stale versions.

Throughline replaces the relay race with **one live production graph**. A scene is not a row duplicated across five files — it is a node whose cast, props, location, day, and dollars are edges. Change the node and the whole graph recomputes, showing a reviewable diff before anything is committed. Specialized AI agents *draft* the breakdown, schedule, budget, and call sheets with visible confidence and provenance; humans *confirm*. The product is obsessive about speed (sub-100 ms interactions, local-first), explainability (every number expands to its derivation), and interoperability (lossless AICP/Movie Magic/Final Draft round-trips so there is zero switching cost).

**Why now (the window is open):** In December 2025 Wrapbook acquired Cinapse to build exactly this connected schedule→budget→cost→payroll back office — but it is **integration-in-progress, not shipped**. Strada abandoned its AI media-search product to become a remote-editing tool. Filmustage owns fast pre-production breakdown but stops at the edge of pre-pro. **No one has shipped the end-to-end, revision-native, on-set-feedback loop.** That is the crown-jewel gap, and it is claimable now.

**The three bets that define the category:**
1. **One living thread**, not four synced tools (breakdown ↔ schedule ↔ DOOD ↔ budget ↔ on-set actuals).
2. **Revision-native**: change the script or a constraint, and the diff ripples everywhere with one-click, previewable approval — because v20 is where every incumbent breaks.
3. **The loop closes on set**: same-day actuals and completed-scene taps flow *back* into the schedule and budget — the unclaimed half of the market's vision.

---

## 2. Vision & positioning

**Vision:** A production should have one brain. Throughline keeps a single living model of the whole production and does the grunt work of keeping it true — so a lean, generalist team runs a shoot with the coordination reliability of a studio, without the studio's staff or software stack.

**Positioning map (mid-2026):**

| Player | What they are now | Throughline's relationship |
|---|---|---|
| **Wrapbook + Cinapse** | Building the connected back office (payroll + accounting + scheduling) — **not shipped** | Race to ship the loop first, for the mid-budget/agency segment they underserve |
| **Filmustage** | Fast AI pre-production + "AI Dude" agent; stops at pre-pro's edge | Match breakdown speed, then own scheduling↔budget↔on-set they don't reach |
| **Strada** | Pivoted to remote editing (dropped AI search) | Complementary — hand off media to Strada/Frame.io; don't compete in edit |
| **StudioBinder / Yamdu / Celtx** | Broad suites, AI as a bolt-on, document-shaped data | Out-execute on the *living graph* they can't retrofit |
| **Movie Magic (EP)** | The de-facto file-format standard; dated, no AI, no actuals | Interoperate (round-trip its files), don't fight the format |
| **TheBid.io / Saturation** | Early AI-native AICP/finance; aggressive free tiers | Beat on the end-to-end loop; match generous entry pricing |

**Positioning statement:** For mid-budget production companies and agencies who are too big for spreadsheets and too small for the studio stack, Throughline is the AI-native production platform that keeps your whole production as one live, explainable graph — unlike Movie Magic/StudioBinder (disconnected documents) or Wrapbook+Cinapse (studio back office, not yet shipped), Throughline makes every change ripple instantly and round-trips losslessly with the tools you already deliver to.

---

## 3. Market & competitive refresh (mid-2026)

**Segment:** mid-budget production companies and agencies — commercials, branded content, indie features/episodic; 5–100 staff; lean, generalist; multiple concurrent projects. Buyer ≠ daily user (line producer/agency producer buys; 1st AD/coordinator lives in it).

**What changed in 2026:**
- **Wrapbook acquired Cinapse (Dec 2025)** — modern cloud scheduling behind $6B+ of productions folding into payroll+accounting; goal is real-time hot costs from the schedule. **Still integrating.**
- **Filmustage** shipped "AI Dude" (breakdown + stripboard manipulation + schedule analytics + VFX cost signals), multi-model support (Filmustage/Gemini/GPT), and "Budget Hints" (explainable line items). Publishes ~86% auto-tag accuracy. Chasing vertical drama (70+ episodes).
- **Strada** launched Strada Connect (P2P remote editing, from $8/mo, no seat/storage caps) and **deprioritized AI media search** after weak demand — a signal that "AI search" alone doesn't sell; workflow ownership does.
- **New entrants:** FinalBit (all-in-one AI), **TheBid.io** (AI-native AICP commercial bids — directly relevant to the agency wedge), Saturation.io (permanent free tier incl. AI budgeting + AICP).

**Validated open gaps (where to win):**
1. The end-to-end **no-lossy-handoff loop** is still unbuilt (crown jewel).
2. **Round-trip revision handling** — tools are fast on v1, brutal on v20 ("total re-draw").
3. **Commercial/AICP** is served by Excel relics (Hot Budget/Showbiz); AI-native bid→actualize→reconcile is open.
4. **On-set → plan feedback** is one-directional; actuals don't flow back.
5. **Explainability/trust** is nascent (only Filmustage gestures at it).
6. **Vertical drama / high-volume episodic** — most tools weren't built for it.

**Pricing benchmarks:** pre-pro AI clusters at **$29–$49/mo** entry (Filmustage Director's Cut $49/mo; Studiovity $29; FinalBit $15–60); collaboration racing to the bottom (Strada from $8/mo; Saturation free). StudioBinder $42→$340/mo by tier. Implication: a generous free tier is expected; premium is justified only by owning the end-to-end loop.

---

## 4. Differentiation & moat

**Eight defensible differentiators (each with why it wins):**
1. **One living production thread**, not four synced tools — switching cost becomes enormous; Wrapbook's own roadmap validates demand before they've shipped.
2. **Revision-native** — change the script, watch the diff ripple with one-click approve; eliminates the daily "total re-draw."
3. **Same-day on-set actuals flow back** into budget + schedule — the unclaimed half of the market's vision.
4. **Explainable AI by default** — every auto-decision shows reasoning and is one-click overridable; converts skeptical line producers/ADs in a union-sensitive, co-pilot-not-replacement climate.
5. **AICP-native for commercials/agencies, AI-fast** — a wedge where incumbents are Excel relics.
6. **>90% breakdown accuracy on messy + vertical/episodic formats, model-agnostic** — beats the ~86% bar; hedges against any single AI vendor.
7. **Speed measured in round-trips, not first-drafts** — sub-minute *re*-generation after every change maps to real on-set stress.
8. **Cloud-optional, no per-seat, no storage caps** — neutralizes the $8/free race while monetizing the loop.

**The moat (what compounds):** the **graph itself** is proprietary structured data no competitor can extract from PDFs; the **event log** becomes a private benchmark dataset (real rates, overtime patterns, spread costs) that makes AI estimates smarter with every production; **cross-project memory** (vendor/crew/location economics) carries between shows; **read-only share links** create network reach without seats. Compound on *derived intelligence*, never on trapping raw data — ship **lossless one-click export (AICP + Movie Magic + Final Draft + PDF + CSV)** as a marketed feature. The confidence to leave is what makes people commit.

---

## 5. Users & personas

Primary segment as above. Buyer/user split shapes the product: sell up (budget accuracy, AICP/MM interop, margin protection) and delight down (kill the re-keying).

- **Maya — Line Producer / UPM (economic buyer, scripted).** Owns budget + schedule feasibility; picks tooling. JTBD: build an accurate budget/schedule fast and keep it truthful as things change. **5-min aha:** imports last project's Movie Magic budget → sees it reconstructed as a live graph → toggles "5 days instead of 6" → top sheet drops $60k in real time, no re-keying.
- **Marco — Agency Producer / EP (economic buyer, commercial).** Owns the client bid. JTBD: produce a clean AICP triple-bid fast and defend markup. **Aha:** gets a live read-only bid link (not a PDF) in the exact AICP section structure, and later one-click bid-vs-actual.
- **Devon — 1st AD (scheduling power user).** Owns the shooting schedule → call sheets. JTBD: when the day changes, the board re-optimizes and flows to DOOD + call sheet. **Aha:** hits "optimize for cast spread" → "-3 hold days, -$7,200" in seconds; keeps the judgment, loses the board math.
- **Priya — Production Coordinator (highest-frequency daily user).** Lives in call sheets, sides, revisions, contacts, comms. JTBD: one source of truth that notifies the right people and tracks confirmations. **Aha:** AD locks tomorrow's order → call sheet drafts itself with correct times/weather/cast → reviewed and sent in two minutes.
- **Sam — DIT / Data Manager (on-set).** Owns offload/verify and camera-to-post handoff. JTBD: verify media safely and pass footage to post with metadata intact and searchable. **Aha:** taps scenes as footage lands → the plan and reality stay in sync with no spreadsheet handoff.
- **Renu — Post Supervisor / Editor (handoff consumer).** JTBD: find the right take instantly (by line, scene, who's on screen). **Aha:** searches "the take where she says the line by the window" and jumps to the frame.

---

## 6. Product principles

1. **One graph, not many files.** A normalized production graph is the product; every screen is a view onto it; nothing is a private copy.
2. **AI drafts, humans confirm.** Every AI output is a *draft* with a confidence signal and click-to-source provenance; a human approves anything affecting people, money, or the published record. Nothing is auto-marked final.
3. **Explainable by default.** Every number expands to its full derivation (rate × days × fringe × markup); every AI decision shows its reasoning and is one-click overridable.
4. **Instant or it doesn't count.** Interactions feel instant (<100 ms, target 50–60 ms) via local-first, optimistic UI; the server syncs in the background, never on the interaction's critical path.
5. **Keyboard-first.** Every action has a shortcut; a ⌘K command palette operates on the graph, not just navigation.
6. **Revision-native.** The unit of work is the *change*; every change produces a reviewable, previewable diff and a full audit trail.
7. **Offline-first on set.** Core views work with no signal and sync on reconnect — set is where plans meet reality.
8. **Interoperate, don't imprison.** Lossless round-trip with Movie Magic, AICP, Final Draft; one-click export of the entire graph. Compound on derived intelligence, not lock-in.
9. **Utility AI only.** Analysis and workflow automation — never generative content that replaces creative labor or performers. Keeps us outside the WGA/SAG-AFTRA flashpoints.

---

## 7. Functional specification

Priorities: **P0** = MVP wedge, **P1** = fast-follow, **P2** = expansion. Each feature lists user stories, acceptance criteria (AC), AI behavior, and priority. AC are written so two reviewers would independently agree on pass/fail.

### 7.1 The production graph + reactive propagation (P0 — the spine)
**Purpose:** one normalized model — Script → Scenes → Elements (cast, props, wardrobe, locations, vehicles, SFX/VFX, stunts, animals, sound, set dressing) → Strips/Days → Day-Out-of-Days → Budget lines → Call sheets → Shoot-day actuals → post handoff — where every entity is a linked node.
- *Stories:* As any user, when I change one node (recast, move a day, edit a rate), I see every downstream consequence recompute and I approve or reject the diff.
- *AC:* A change emits an event; dependents recompute as a **proposed diff** (never a silent write); the user can preview, accept, or reject; accepted changes append to the event log; every artifact is reconstructable at any revision.
- *AI behavior:* none in the core engine — propagation is deterministic. AI proposes *content* (Section 12); the graph guarantees *consistency*.
- **Ripple preview (P1):** while dragging a scene to a new day, a translucent overlay shows consequences *before drop* — new cast hold days, overtime, permit conflicts, "+$8,400 to the top sheet."

### 7.2 Script ingest & AI breakdown (P0)
**Purpose:** turn a script into a fully tagged, editable breakdown on the graph in minutes, with confidence + provenance + revision diffs.
- *Stories:* Import a `.fdx`/Fountain/PDF and get scenes with drafted element tags; correct tags in a fast keyboard queue; re-import a revision and see a **breakdown diff** (new/changed/deleted elements) with downstream ripples.
- *AC:* A standard `.fdx` yields a scene-by-scene breakdown with element categories in <5 min for a 100-page script; every AI tag is a visible draft with one-tap accept/reject and click-to-source highlight in the script; low-confidence/ambiguous tags are flagged for review, never silently included; a revised script produces an element-level diff.
- *AI behavior:* deterministic parser structures the script; a zero-shot NER pass proposes candidates; an open LLM (structured JSON) reconciles/dedupes/ resolves ambiguity; each element carries a confidence + source span; safety-critical types (stunts, weapons, animals, SFX) tuned for high recall.

### 7.3 Scheduling, DOOD & cast-spread optimizer (P0)
**Purpose:** generate and maintain a shooting schedule + DOOD that survive change.
- *Stories:* Generate a stripboard from the breakdown under constraints (cast availability, location days, day/night, company moves, turnaround); when a day moves, see the board re-optimize and the DOOD update as a diff; hit "minimize hold days" and see the re-ordered board with exact dollar savings.
- *AC:* Stripboard generates from confirmed elements and is manually re-orderable; DOOD is derived and correctly distinguishes work/hold/travel; a change produces a proposed re-board + DOOD update as a reviewable diff; hard constraints are never violated in a proposed schedule; the optimizer surfaces *why* and applies with a one-click preview.
- *AI behavior:* a constraint solver (OR-Tools CP-SAT) proposes; natural-language commands ("move all of Sarah's scenes into a 3-day block") translate to constraints the solver honors; the human approves.

### 7.4 Budget, AICP/Movie Magic interop & "cost of this decision" (P0)
**Purpose:** defensible budgets in the buyer's required format, kept honest against actuals.
- *Stories:* Produce an AICP bid from breakdown+schedule and export it cleanly; build a Movie-Magic-structured budget; track estimate/committed/actual/EFC as actuals arrive; see a live dollar figure and delta on every object in the UI ("+$12k: night ext lighting + 0.4 OT days").
- *AC:* Budgets author and export in AICP bid-form structure (sections A–W) and Movie Magic budgeting structure, round-trip lossless on core fields (account codes, fringes, globals); budget lines link to breakdown/schedule so any change surfaces the cost delta; every figure expands to its derivation.
- *AI behavior:* an LLM drafts and *explains* line-item estimates from the graph (visible assumptions/sources, à la explainability principle); OCR reads invoices/timecards into actuals as drafts; no numbers auto-approved.
- **Bid ⇄ actuals as one object (P2):** the AICP bid becomes the live budget becomes wrap actuals — variance is automatic; hand the client a bid-vs-actual reconciliation in one click.

### 7.5 What-if branches (P1)
**Purpose:** fork the entire production graph, try an alternative, compare side by side.
- *AC:* A user can branch the graph, edit the branch freely, and view a side-by-side diff of budget + DOOD + calendar vs. the mainline; merge the winner or discard; branches are event-log-backed.

### 7.6 Time Machine — event-log scrubber (P1)
**Purpose:** see the production as it was at any moment; "blame" any line; restore.
- *AC:* A timeline slider reconstructs the schedule/budget at any past event; any figure shows who changed it and why ("added by AD when scene 42 went night"); any prior state is restorable as a branch.

### 7.7 Coordination, call sheets & per-role copilots (P1)
**Purpose:** replace email/WhatsApp sprawl with structured, routed, searchable comms; auto-draft call sheets; proactive role copilots.
- *AC:* Call sheets auto-populate cast/crew/scenes/times/locations/weather from the graph; distribution tracks delivery + acknowledgment per recipient; a revision supersedes prior versions and re-notifies only affected people; viewers need no paid seat; notifications route by role/department and reference the specific change.
- *AI behavior:* per-role copilots watch the graph and surface the right nudge in the right person's language (LP: "trending 6% over in Art Dept"; 1st AD: "most efficient order tomorrow given weather+cast+daylight"; Coordinator: drafts the call sheet the instant the schedule settles).

### 7.8 On-set mobile — the live wrap loop (P2)
**Purpose:** close the loop where plans meet reality.
- *AC:* On mobile, the AD taps scenes complete and the DIT confirms footage received; this reflows the remaining schedule, recomputes days-remaining vs. budget, and auto-drafts a Daily Production Report + tomorrow's call sheet; works offline and syncs on reconnect; nothing overwrites the DIT's verified media.

### 7.9 Production-wide search & grounded Q&A (P1 search / P2 Q&A)
**Purpose:** one search box across scripts, notes, comms, documents, and (later) footage logs.
- *AC:* Hybrid semantic + keyword search spans all production content; grounded Q&A answers only from retrieved context, cites the specific source node, and abstains ("insufficient sources") rather than guess; results respect role-based access.

### 7.10 Interoperability & handoff (P0 AICP+FDX / P1 MM / P2 post)
- *AC:* Import/export round-trips Movie Magic Scheduling (.mmsp) + Budgeting (.mmb) and Final Draft (.fdx) without core-field loss; AICP export matches the standard form; structured metadata hands off to Frame.io/Strada and editorial (EDL/AAF via OpenTimelineIO). Deterministic parsers own format fidelity — never AI.

---

## 7A. Essential production features — Hollywood table stakes

Professional US productions reject tools that lack these. Priority: **[TS]** table stakes (rejected without) · **[P2]** expansion/differentiator. **Load-bearing rule for the whole section:** every dollar figure, hour threshold, and rate is **[RATE CARD]** — stored in a **configurable, effective-dated table keyed on union × contract-family × tier × location-context × principal-photography-start-date**. Never hard-code rates or multipliers; the 2024 union MOAs changed thresholds and they phase in by shoot start date.

### 7A.1 Union & labor-compliance rules engine (P0 — #1 table stake AND a moat)
The single highest-value feature. It plugs directly into scheduling (predictive flags) and budget/hot-costs (actual computation).
- *Architecture (build first):* a **table-driven, effective-dated rules engine**; track **"worked hours" vs "elapsed hours"** as distinct quantities per person/day (this reconciles almost every cross-union rule); per-person running counters (turnaround clock, day-in-week, consecutive-days, weekly meal-penalty count, weekly rest); a **location-context** dimension per day (studio / studio-zone / nearby / distant-overnight) that bends most rules.
- *Rules to encode + flag* across **SAG-AFTRA, DGA, IATSE, Teamsters**: overtime tiers (1×/1.5×/2×, with union-specific worked-vs-elapsed basis), **meal periods & escalating meal penalties**, **turnaround / forced-call** (studio 12h vs location 10/11h; IATSE 10h/9h distant; Teamsters rest 10h; DGA 9h Basic vs 8h Commercial; rest-invasion penalties differ by union — IATSE 2×, Teamsters 3×), **6th/7th-day premiums**, **golden/triple time**, night premium (per-local toggle), travel-as-work, hold/idle pay, and the **14-day rule**. Model DGA as a **day-count** model (extra ½/full-day at hour thresholds), not hourly OT — architecturally distinct from SAG/IATSE.
- *Minors / child labor (P0):* **per-jurisdiction, versioned table** (CA and NY diverge materially) — age-band hours (work/school/rest), hard caps (CA 8h/day, 48h/week, 12h turnaround "no exceptions"), studio-teacher ratios, permitted work windows, and **Coogan/blocked-trust** logic (required in CA, NY, IL, LA, NM; % and custodian thresholds differ). Non-compliance is legal/criminal exposure, not just cost.
- *AC:* engine **flags at schedule time** (predictive: "this call forces a meal penalty / turnaround violation / minor-hours breach") and **computes at timecard time** (actual penalties/premiums); all thresholds/rates come from the effective-dated table; changing the signatory/contract selection reloads the correct rule set; every flag explains the rule and cites the table entry (explainability principle).

### 7A.2 Production accounting: cost report, hot costs, POs, petty cash (P0)
- **Budget structure:** Top Sheet → accounts → detail, split **ATL / BTL-production / Post / Other**; configurable Chart of Accounts (Category/Account/SubAccount/Set); **fringes engine** (name/rate/unit/**cap**, applied to fringe ranges, flowing proportionally when wages change).
- **Weekly Cost Report** (the artifact studios/financiers/bond companies read): per account — Approved Budget · Actuals (cost-to-date) · Committed (open POs) · **ETC** · **EFC** · Variance. **Formula: EFC = Actuals + Committed + ETC; Variance = Budget − EFC.** Rolls up ATL→BTL→Post→Other→fringes→contingency; Summary/Detail views; period + cumulative.
- **Daily Hot Costs:** next-morning actual vs. budgeted labor for the prior shoot day, driven by OT + meal/forced-call penalties (computed from Exhibit G + the rules engine), by department. Line producers read this first every morning.
- **POs + commitments** (approved-uninvoiced PO = committed cost; 3-way match on invoice → actual), **check requests with UPM sign-off routing**, **petty cash / accountable advances** (envelope model; reconcile receipts + remaining = float), and a **cash-flow forecast** (P2 for indies, P0 for studio/financier work with drawdown limits).
- *AC:* cost report math matches the formula above and reconciles to POs + timecards; hot costs regenerate from the prior day's Exhibit G; every figure expands to its derivation.

### 7A.3 Timecards, start paperwork & payroll handoff (P0)
- **Exhibit G** (SAG-AFTRA time report): per-performer report/dismiss times, meals, travel, **work-status codes** (W/SW/SWF/H/T/TR/R/F), minor flag, penalty fields (forced-call, MPV count, wardrobe/stunt adjustments), tenths of an hour, **performer e-signature**.
- **Cost-coded crew timecards:** call/meals/wrap, computed hours + rate multiplier, day-type, turnaround counter, **split a day across account codes**, configurable multi-level approval (dept head → UPM → accountant), auto-recalc.
- **Start packets / deal memos** as structured data (legal name, rate, guarantee, account code, box/kit + cadence, dates) + W-4/W-9/I-9/direct-deposit; **box/kit rental as a separate, taxability-flagged pay line** (accountable-plan → non-taxable; else W-2/1099 routing).
- **Payroll handoff & fringe reporting:** clean export to **Entertainment Partners / Cast & Crew / Wrapbook** (employer-of-record model) with wage-type breakdown + cost codes; **union P&H reporting** (SAG-AFTRA Contributions Manager schema, MPIPHP) with caps/ceilings. Round-trip budgets with **Movie Magic / Showbiz / Hot Budget**.
- *AC:* Exhibit G renders to the guild form and is the feed for hot costs; timecards compute against the rules engine; approved timecards export in a payroll-ready schema; MM budget/schedule interchange round-trips core fields.

### 7A.4 Script revisions — colored pages (P0)
- *AC:* enforce the standard revision color order (White → Blue → Pink → Yellow → Green → Goldenrod → Buff → Salmon → Cherry → Tan → Double White…); **locked pages** (numbering frozen after release); **A-pages/A-scenes** (10A, 10B without renumbering); **revision marks** (auto-asterisks in the margin on changed lines); revision slug (color + date) per page and a full revision history on the title page. Ties into the revision-native breakdown diff (§7.2). Revision clouds / as-broadcast export = **[P2]**.

### 7A.5 Sides + secure watermarked distribution (P0)
- *AC:* auto-generate daily **sides** from the call sheet's scenes in shooting order (half-letter), and **character-filtered** sides in one click; **personalized watermarking** (recipient name/email burned into every page of scripts/sides); **permissioned, closed-loop distribution** with expiring/revocable links and download/print controls; **read/acknowledge + delivery tracking** (who opened, who hasn't — chase before call). This is the Scenechronize/Croogloo security bar.

### 7A.6 Location management (P0)
- *AC:* per-location **document vault** — signed location release/agreement, permit(s), and **COI (additional-insured endorsement + expiry + liability limit)** with issue/expiry dates and expiry alerts; **sunrise/sunset + magic hour + weather** per location/date auto-populated onto the call sheet; maps/directions, parking/basecamp/craft-service, and **nearest 24-hr hospital**; **company-move logistics** (move time, from/to, travel time) reflected on schedule + call sheet. Neighborhood-notification tracking = [P2].

### 7A.7 Clearances & legal (P2, P0 for E&O-bound deliverables)
- *AC:* **script clearance report** (log every flagged name/business/product/trademark/address with status + required change + proof implemented); **music cue sheet** (per cue: title, timecode, duration, composer, publisher, and which of **sync / master-use / performance** licenses is secured); **releases registry** (appearance/talent, location, minor) matched to person/scene/footage; **chain-of-title** doc set; **E&O** policy record; a **delivery-checklist rollup** (P2) that assembles the distributor/streamer deliverables package.

### 7A.8 Cast & crew management + e-signature (P0)
- *AC:* reusable **cross-project contacts/crew database** (person once, reused across shows, with roles/union/agency/rates/history — never re-enter crew per project); template-driven **deal memos**; **start packets** assembled per hire; built-in **e-signature** (signing order, reminders, mobile) for memos/releases/approvals. Cross-project memory feeds the moat (rates/vendors carry between shows).

### 7A.9 Tax-incentive estimator (P1 — decides where to shoot)
- *AC:* an incentive estimator **inside the budget** modeling per jurisdiction: **qualified (in-jurisdiction) spend**, **credit %** (incl. uplifts for VFX/local-hire/out-of-zone), **annual/per-project caps**, **ATL vs BTL eligibility** (ATL often capped), and **credit type** (transferable / refundable / non-transferable) with estimated **cash value after broker discount**; net-of-incentive cost comparison across jurisdictions. Ship with a static jurisdiction table; a **live-maintained library** is [P2] (rates/caps change mid-year — verify against the film office before hard-coding).

### 7A.10 Safety & compliance (P1; P0 for CA incentive projects)
- *AC:* attachable **AMPTP Safety Bulletin** library; **written risk assessments** (mandatory for firearms, pyro/explosives, major stunts, vehicle/process, aircraft/watercraft, >60-hr weeks) with mitigation plans; **safety-meeting logging** (daily + firearms-scene meetings) with attendance; **incident reporting** + final safety-evaluation workflow; **CA SB 132 safety-advisor** tracking for productions taking the CA tax credit (Safety on Productions Pilot, 2025–2030).

### 7A.11 Sustainability / green reporting (P1; P0 for UK/global studio work)
- *AC:* **albert-compatible carbon tracking** (energy, fuel, travel, hotels) with report export — effectively mandatory for UK commissions; map to **PGA Green Production Guide (PEAR/Carbon Calculator)** and **EMA Green Seal** point criteria for US studio work. Increasingly a commission/delivery condition.


---

## 8. System architecture

**Guiding principle (from the fastest apps — Linear, Figma, Superhuman):** do the work locally and optimistically so the UI responds in <100 ms (target 50–60 ms); sync to the server in the background, never in the interaction's critical path.

**Reference architecture (logical tiers):**
- **Clients** — Web app (desktop-grade budgeting/scheduling), mobile app (on-set, offline-first), and a thin on-set/DIT ingest agent near the media.
- **Edge/API gateway** — auth, rate limiting, tenant routing.
- **Core services** — Ingestion, Breakdown, Scheduling, Budget, Propagation, Collaboration, Coordination/CallSheet, Search, Notification, Interop. Ship as a **modular monolith** (FastAPI) at MVP; extract hot paths and heavy services later.
- **Hot-path workers (selective, measured)** — a small number of Rust/Go workers for graph propagation and grid math *only where profiling proves Python is the bottleneck*. Default to Python; optimize by evidence, not preemptively.
- **Data plane** — **PostgreSQL as the single system of record**: the production graph via adjacency lists + depth-guarded recursive CTEs (no separate graph DB at this bounded depth); an **append-only event log → async projections** for reactive cascade + audit + Time Machine; **pgvector (+pgvectorscale)** for semantic search. **Valkey/Redis Streams** for cache + pub/sub. **Cloudflare R2** (zero egress) for media/proxies/documents.
- **Real-time + sync** — **Yjs** CRDT + awareness for multiplayer editing/presence; a durable sync engine (**PowerSync** for true on-set offline, or **Zero** for web — note Zero 1.0 landed June 2026, Postgres-only, no SSR) with all writes routed through the backend for authorization.
- **AI serving plane** — **vLLM** (default) / **SGLang** (prefix-heavy) behind an internal OpenAI-compatible endpoint; **XGrammar** constrained decoding for valid JSON; small-model-first routing; speculative decoding on low-concurrency paths; embedding + prefix + semantic caches; a GPU **batch queue** for overnight/heavy jobs (dailies, bulk breakdown). Durable multi-step AI workflows via **Temporal**.
- **Transport** — **SSE** for AI token streaming and one-way live updates; **WebSocket** for CRDT sync + agent control; REST (+ typed TS client) for CRUD; gRPC internal-only.

**Four data-flow narratives:**
1. *Hot-path edit* — user drags a strip → optimistic local update (<50 ms) + Yjs doc mutate → background WS sync → server authorizes, appends event, runs propagation → projections update → clients reconcile. UI never blocks on the server.
2. *AI breakdown* — script upload → parser → NER + LLM (constrained JSON, streamed via SSE) → draft elements written to graph with confidence/provenance → human confirm queue.
3. *Semantic search* — query → embed → pgvector ANN + keyword (hybrid) → grounded LLM answer with citations → faithfulness gate.
4. *Reactive cascade / audit* — any accepted change is an event → async projectors recompute DOOD/budget/call-sheet views + emit notifications → event log powers Time Machine + blame.

**Latency targets (put these in the perf budget):** interaction feel p95 < 100 ms (target 50–60 ms); API read p95 < 150 ms, write p95 < 250 ms; sync propagation to collaborators p95 < 500 ms; AI breakdown < 5 min for 100 pages; schedule re-solve (interactive) < 10 s for a typical feature; semantic search p95 < 800 ms; AI time-to-first-token < 1 s with streaming.

> Caveat carried from research: specific model version names and vendor throughput numbers shift fast in 2026 — the architecture and thresholds are durable; re-check exact model/latency figures at build time.

---

## 9. Data model (the production graph)

Pragmatic implementation: **relational-with-edges in Postgres** (not a niche graph DB) + an event log. Core tables (illustrative, not exhaustive):

- `projects` (id, org_id, title, type[scripted|commercial|episodic], created_at)
- `scripts` (id, project_id, version, source_format, imported_at)
- `scenes` (id, script_id, number, int_ext, location_id, time_of_day, page_eighths, heading, body)
- `elements` (id, project_id, etype, name, confidence, source[rule|ner|llm|human], source_span, needs_review)
- `scene_elements` (scene_id, element_id) — many-to-many edge
- `shooting_days` (id, project_id, index, date, primary_location_id)
- `day_scenes` (day_id, scene_id, order)
- `dood_entries` (project_id, cast_element_id, day_index, code[SW|W|WF|H|SWF])
- `budget_lines` (id, project_id, code, category, description, qty, unit, rate, fringe_pct, driver_ref) — `driver_ref` links to the graph fact that drives it
- `actuals` (id, budget_line_id, amount, source_doc_id, status[draft|approved])
- `call_sheets` (id, day_id, revision, published_at) + `call_sheet_recipients` (…, delivered_at, acknowledged_at)
- `media_assets` (id, project_id, scene_id, path, proxy_path, checksum, verified_by)
- `contacts` / `crew_roles`, `locations`, `documents` (ingested), `embeddings` (pgvector)
- **`events`** (id, project_id, ts, actor, kind, payload jsonb) — the append-only spine powering propagation, audit, Time Machine, and branches
- `branches` (id, project_id, parent_event_id, name) — what-if forks
- `users`, `orgs`, `roles`, `permissions` — RBAC + tenant isolation (row-level security or schema-per-tenant)

**Consistency model:** writes append events; projectors (async) materialize read views; propagation computes downstream diffs from an event and enqueues them for human approval; approvals are themselves events. This yields the "change once, review the ripple" promise with a complete audit trail and free versioning.

---

## 10. API specification (shape, not exhaustive)

- **Style:** REST + typed TS client (generated from OpenAPI); gRPC internal-only; SSE for streaming; WebSocket for collab/agent control. `/v1/` in path; camelCase JSON; cursor pagination.
- **Representative endpoints:**
  - `POST /v1/projects/{id}/scripts:import` → returns job id; breakdown streamed via SSE `GET /v1/jobs/{id}/stream`.
  - `GET /v1/projects/{id}/graph` → materialized graph snapshot (+ `?at=eventId` for Time Machine).
  - `POST /v1/projects/{id}/changes` → submit a change; returns a **proposed diff** (dependents recomputed) for confirm/reject.
  - `POST /v1/projects/{id}/changes/{diffId}:confirm|reject`.
  - `POST /v1/projects/{id}/schedule:optimize` (body: constraints/objective) → proposed re-board + rationale.
  - `POST /v1/projects/{id}/budget:export?format=aicp|mmb|pdf|csv`; `POST …/scripts:export?format=fdx`.
  - `POST /v1/projects/{id}/branches`; `GET …/branches/{b}:diff`.
  - `POST /v1/projects/{id}/search` (hybrid) and `POST …/ask` (grounded Q&A with citations).
  - `WS /v1/projects/{id}/collab` (Yjs sync + presence); `POST …/callsheets/{day}:publish`.
- **Contract discipline:** `docs/openapi.yaml` is the single source of truth, imported into both frontend and backend context; contract tests gate merges.

---

## 11. Real-time collaboration & offline sync

- **Multiplayer editing** of the stripboard/budget via **Yjs** documents (CRDT) + awareness (presence, cursors). Grid/board edits use CRDT; for last-writer-wins fields (e.g., a single scalar rate) a simpler LWW register is acceptable — decide per field, documented in code.
- **Offline-first on set:** local store holds the working graph; **PowerSync**-style bidirectional sync reconciles on reconnect; all writes still route through the backend for authorization and event-log append (the CRDT is the *editing* layer, the event log is the *truth* layer).
- **Conflict handling:** CRDT merges structural edits; server validates hard constraints on sync and surfaces any resulting conflict as a diff to resolve, never a silent overwrite.

---

## 12. AI / ML architecture

**Doctrine:** right tool per task — deterministic solvers for math, open LLMs for language, specialist models for audio/vision. Prefer **self-hostable, permissively-licensed (Apache/MIT/BSD)** weights for cost control, IP privacy (unreleased scripts stay on your infra), and reproducible eval-gated releases. Small-model-first routing keeps latency-critical paths cheap; escalate to a larger/frontier model only when an eval proves a quality gap.

**Feature → model/tool map (all commercial-license-cleared):**

| Capability | Model / tool | License | Notes |
|---|---|---|---|
| Script parsing (.fdx/Fountain/PDF) | screenplay-tools, pdfplumber | MIT | deterministic; never AI for format fidelity |
| Element tagging (zero-shot) | GLiNER v2.1 + spaCy | Apache / MIT | pin GLiNER v2.1 Apache weights |
| Reasoning + structured JSON | Qwen3 (8B–32B), DeepSeek-V3.2, Phi-4-mini | Apache / MIT | XGrammar-constrained JSON; small-model-first |
| Embeddings / search | Qwen3-Embedding, BGE-M3 + pgvector | Apache / MIT | hybrid dense+keyword |
| Grounded-answer safety | Granite Guardian | Apache-2.0 | groundedness/hallucination gate |
| PII redaction | Presidio | MIT | scrub before storage/model calls |
| Schedule optimization | Google OR-Tools (CP-SAT) | Apache-2.0 | feasibility + objective |
| Document OCR/KIE (invoices, timecards, legacy call sheets) | PaddleOCR, Donut | Apache / MIT | actuals ingestion |
| Serving | vLLM, SGLang (local: llama.cpp/Ollama) | Apache / MIT | OpenAI-compatible endpoint |
| (Future) dailies: transcription / diarization / align / shots / VLM | faster-whisper, pyannote, WhisperX/MFA, PySceneDetect, Qwen2.5-VL | MIT / BSD / Apache | Phase 3 |

**Explainability & guardrails (product-level):** every AI output carries confidence + provenance (model, inputs, source span, what changed) and is diff-reviewable; low-confidence flags for review; "human confirms" is enforced *structurally* (a status field only a human action flips), not by prose. **Avoided (licensing landmines):** Ultralytics YOLO / PyMuPDF / aeneas (AGPL — would force open-sourcing), InsightFace recognition weights / LayoutLMv3 / Jina v3 (non-commercial), DINOv3 (custom/gated). **Face recognition is a non-goal** (BIPA/GDPR/EU-AI-Act high-risk, obligations from Aug 2026); face *detection* only if ever needed.

---

## 13. Non-functional requirements

- **Performance:** meet the latency targets in §8 (interaction p95 <100 ms; write p95 <250 ms; breakdown <5 min/100pp; re-solve <10 s; search p95 <800 ms; TTFT <1 s).
- **Offline:** core on-set views (call sheet, schedule, DPR) fully functional offline with conflict-aware sync.
- **Security:** SSO (higher tiers), RBAC least-privilege, tenant isolation, encryption in transit + at rest, full audit trail; PII redaction before storage/model calls.
- **Scalability:** multiple concurrent productions per org with isolation; GPU batch pool for heavy jobs; horizontal scale of stateless services.
- **Reliability:** event log is the durable source of truth; projections rebuildable; media originals never mutated.
- **Accessibility:** WCAG 2.1 AA; full keyboard operability (aligns with keyboard-first principle).
- **Observability:** per-AI-agent confidence/latency/cost metrics; drift alerts when acceptance rate drops.

---

## 14. Trust, legal, union & compliance

- **Union/creative-labor:** utility/analysis AI only; no writing/rewriting covered material, no generative performances/replicas — outside WGA/SAG-AFTRA flashpoints. AI outputs are human-confirmed drafting aids (human authorship preserved).
- **Biometrics:** face recognition OFF at launch; detection-only if ever added; BIPA (written consent before capture), GDPR Art. 9 (explicit consent + DPIA), EU AI Act high-risk for post-hoc identification (obligations phase in from 2 Aug 2026).
- **Model licensing:** ship only Apache/MIT/BSD weights; maintain a per-checkpoint license register; publish a NOTICES/attribution page for CC-BY models; enforce a loader allowlist + CI license check.
- **Training data:** never train shipped models on scraped copyrighted screenplay corpora; use customer opt-in or licensed/cleared data; open corpora for internal eval only.
- **Data ownership:** customer data is the customer's; lossless export is a right, marketed as a feature.

---

## 15. Evaluation plan (the quality firewall)

**Method (grounded in Anthropic's eval guidance):** task → multiple trials → graders (code-based preferred; calibrated LLM-judge where needed; human to calibrate) → outcomes, not paths → suites → CI harness. **Capability evals** start low (a hill to climb); **regression evals** sit near 100% and block releases on any drop; solved capability tasks **graduate** into the regression suite; every production failure becomes a new golden case. Start with **20–50 real-failure tasks** per feature; each task has a reference solution; balance positive and negative cases; report **pass@k** (one success suffices) and **pass^k** (customer-facing consistency).

**15.1 Script breakdown (information extraction).** Build a gold set from real scripts across genres/formats/eras with a written annotation guideline + double-annotation; measure inter-annotator agreement (the F1 ceiling). Metrics: precision/recall/**F1 per element type** (exact match + a relaxed boundary variant), micro/macro averages, negative cases. Product metric: **net time saved after human QA** (timed sessions vs manual). **Gates:** characters/locations F1 ≥ 0.90; props/wardrobe/vehicles F1 ≥ 0.80; **safety-critical types (stunts/weapons/animals/SFX) recall ≥ 0.95**; ship only if net time saved > 0.

**15.2 Scheduling optimizer (CSP/optimization).** Deterministic code graders. (1) **Hard-constraint correctness** — any violation (double-booked actor/location, availability, turnaround) = fail. (2) **Optimality gap** vs best-known/baseline — target mean ≤ 10%; track fraction solved to proven optimality. (3) **Solve-time budget** — fixed wall-clock cap; report solve rate within budget using a PAR-2-style penalty for timeouts. Golden bank of realistic instances with known feasible/optimal solutions; regression asserts feasibility = 100% and no gap/solve-time regression.

**15.3 RAG / grounded Q&A (Ragas-style).** Separate retrieval from generation: Context Precision/Recall (retrieval), Faithfulness/Answer Relevancy (generation). Give the judge an "Unknown" escape hatch; calibrate judges vs humans quarterly. **Gates:** Faithfulness ≥ 0.90 (hard — else abstain/route to human); Context Recall ≥ 0.85; Answer Relevancy ≥ 0.80; **every claim cited**; bias toward abstention (an ungrounded answer about a contract clause is a liability).

**15.4 Regression / CI gating.** Golden datasets version-controlled in `evals/datasets/` (one per feature). Run evals on every AI-feature change and every model upgrade (promptfoo declarative assertions and/or DeepEval pytest-style `assert_test`), executable in `claude -p` non-interactive CI. Merge gates: regression suite pass, faithfulness/feasibility hard gates, no drop in per-type F1 / optimality gap beyond tolerance. Track latency/tokens/cost alongside quality. **Read transcripts before trusting scores.**

---

## 16. Repo structure & Claude Code workflow

**Monorepo layout** (nested `CLAUDE.md` per package; start-in-subdir loads local + root only):
```
repo/
  CLAUDE.md                 # root context (see companion file); imports @AGENTS.md if multi-tool
  docs/  PRODUCT_SPEC.md (this) · architecture.md · glossary.md · openapi.yaml · licenses.md
  apps/web/        CLAUDE.md   # Next.js App Router + React 19, TanStack Query, Zustand, shadcn/Tailwind, TanStack Virtual, cmdk
  services/api/    CLAUDE.md   # FastAPI, Postgres+pgvector, event log, propagation
  packages/shared/ CLAUDE.md   # shared TS types generated from openapi.yaml
  ml/              CLAUDE.md   # prompts (versioned), breakdown/, scheduler/, rag/
  evals/           CLAUDE.md   # datasets/, suites/, graders/, reports/ (first-class, PM-contributable)
  .claude/  settings.json (allow/deny + hooks) · agents/ (security-reviewer, eval-runner) · skills/ (run-evals, aicp-export, breakdown-schema)
```

**Workflow discipline (encoded in `CLAUDE.md`):** Explore (plan mode, subagents for wide reads) → Plan (edit the plan before coding) → Implement (tests first; confirm they fail; then code) → Verify (run typecheck+lint+tests+relevant evals; show output as evidence) → adversarial **review subagent** in fresh context sees only the diff + acceptance criteria. `/clear` between unrelated tasks. Guardrails that must always hold are **deny rules / hooks**, not prose (block `.env*` reads, non-allowlisted licenses, writes to `migrations/`/`infra/`, and enforce "AI output = draft" structurally).

---

## 17. Build backlog & roadmap (epics → the executable slices live in BUILD_TASKS.md)

- **Phase 0 — Discovery (0–3 mo):** graph core + event log; script parsing; Breakdown Agent (LLM seam) + eval harness; FDX/AICP import/export. *Exit:* breakdown eval passes gates on a real gold set; net-time-saved > 0 with 5 design partners.
- **Phase 1 — MVP wedge (3–9 mo):** script→budget spine (breakdown → CP-SAT schedule → DOOD → budget), AICP export, reactive propagation + ripple preview, production-wide search; web app (local-first, keyboard-first). *Exit:* partners ship real bids/boards; positive net time saved; first paid orgs.
- **Phase 2 — On set + collab (9–18 mo):** call sheets + propagation, per-role copilots, real-time multiplayer (Yjs), mobile offline, DPR; Movie Magic round-trip; what-if branches; Time Machine. *Exit:* productions run shoot days end-to-end; retention signal.
- **Phase 3 — The loop + intelligence (18–30 mo):** on-set live wrap loop (actuals flow back), dailies intelligence, bid⇄actuals, post handoff (OTIO); studio-grade security/SSO. *Exit:* the closed loop no incumbent has shipped; move upmarket.

Every slice in `BUILD_TASKS.md` carries acceptance criteria + a verification/eval gate.

---

## 18. Pricing & go-to-market

**Wedge:** "AI script-to-budget that speaks AICP and Movie Magic," landing the economic buyer (line/agency producer) at commercial/branded shops and indie episodic, then expanding into the shoot day and the loop. **Motion:** product-led, bottom-up; free individual tier so the tool is person-carried project to project; 5–10 design-partner agencies each run one real bid.

**Pricing model (matched to how productions buy; neutralizes the $8/free race):**
- **Free (individual):** one active project; breakdown + basic schedule.
- **Per production:** active-project fee (pay while shooting, pause between); full pre-pro spine + AICP export + search + call sheets.
- **Organization / agency (annual, the revenue engine):** multiple concurrent productions, shared contact DB, Movie Magic round-trip, collaboration, on-set + dailies, SSO/security.
- **Lossless export is free and marketed** — the confidence to leave is what earns commitment.

---

## 19. Success metrics

- **North Star:** shoot days run end-to-end on Throughline (call sheet delivered via the product AND DPR filed through it).
- **Input:** breakdowns completed; AICP/MM exports shipped; **net time saved per breakdown/bid** (≥60% target after QA); confirmed change-propagations (proves the core promise); dailies hours indexed (Phase 3).
- **Quality:** AI draft acceptance rate (guards the trust gap); eval-gate pass rates.
- **Business:** concurrent productions per org; annual retention; free→paid conversion.

---

## 20. Riskiest assumptions & validation (test before over-building)

1. **AI breakdown accuracy makes "draft+confirm" faster than manual.** Test: gold-set eval + timed QA study; ship only if net time saved > 0 (≥60% target). *If wrong, the value evaporates.*
2. **Movie Magic .mmb/.mmsp round-trip is technically + legally feasible.** Test: parse samples, prototype round-trip, early legal review of the proprietary format.
3. **Buyers adopt despite Movie Magic habit.** Test: land on the AICP gap with zero-switching interop; 5 agencies run one real bid each.
4. **Reactive propagation is trusted (no silent wrong changes).** Test: always render a reviewable diff; measure accept/revert with partners.
5. **Open models are good enough vs frontier APIs for our tasks (and fast enough).** Test: eval open vs API on breakdown/logging; hybrid where a gap is proven; meet latency targets.
6. **We can close the on-set loop before Wrapbook+Cinapse ship it.** Test: speed to Phase 3; design-partner pull.

---

## 21. Open questions
- Lead scripted (line producer) or commercial (agency producer) first? Shared graph, different first-run job (board vs bid).
- How much Movie Magic round-trip at MVP vs AICP-only to start?
- Self-host vs API split per model, and the GPU budget it implies.
- PowerSync vs Zero for the durable sync engine (Zero is newer, web-fast, Postgres-only, no SSR yet).
- Build vs partner for payroll/actuals (Wrapbook) and post handoff (Strada/Frame.io).

---

## Appendix A — Model licensing register (ship only these; verify at build)
Qwen3 / Qwen3-Embedding / Qwen2.5-VL-7B·32B (Apache-2.0) · DeepSeek-V3.2 / R1 (MIT) · Phi-4-mini (MIT) · BGE-M3 (MIT) · GLiNER v2.1 (Apache) · faster-whisper (MIT) · pyannote community-1 (CC-BY-4.0, gated, attribute) · SAM 2.1 / SigLIP 2 / DINOv2 / Grounding DINO / OWLv2 (Apache) · PySceneDetect (BSD) · PaddleOCR (Apache) / Donut (MIT) · OR-Tools (Apache) · Presidio (MIT) / Granite Guardian (Apache) · vLLM / SGLang (Apache) / llama.cpp / Ollama (MIT). **AVOID:** Ultralytics YOLO, PyMuPDF, aeneas (AGPL); InsightFace recog weights, LayoutLMv3, Jina v3, Canary-1b non-flash, Qwen2.5-VL-3B (non-commercial); DINOv3 (custom/gated).

## Appendix B — Glossary
Breakdown · Stripboard · DOOD (Day-Out-of-Days) · AICP bid (sections A–W) · Movie Magic (.mmb/.mmsp) · Fringe · EFC (estimate-to-complete) · Company move · Hold day · Spread cost · Dailies · CRDT · Event sourcing / CQRS · pass@k / pass^k · Optimality gap · Faithfulness.

## Appendix C — Latency targets (perf budget)
Interaction p95 <100 ms (target 50–60) · API read p95 <150 ms · API write p95 <250 ms · collaborator sync p95 <500 ms · breakdown <5 min/100pp · interactive re-solve <10 s · search p95 <800 ms · AI TTFT <1 s.

## Appendix D — Key sources
Wrapbook–Cinapse acquisition (wrapbook.com/blog; variety.com) · Filmustage AI Dude + Budget Hints + vertical drama (filmustage.com/blog) · Strada Connect / AI-search pivot (cined.com; strada.tech) · TheBid.io / Saturation AICP (thebid.io; saturation.io) · AICP bid form (aicp.com; wrapbook.com) · Claude Code best practices, memory, permissions, sub-agents (code.claude.com/docs) · Demystifying evals for AI agents (anthropic.com/engineering) · Ragas metrics (docs.ragas.io) · Linear/Superhuman/Figma speed (performance.dev; blakecrosley.com; figma.com/blog) · Open-model license sources: HF model cards + GitHub LICENSE files (Qwen, DeepSeek, SAM2, SigLIP2, OR-Tools, Presidio, etc.).

---
*End of Master Build Specification. Companion files: `CLAUDE.md` (repo context) and `BUILD_TASKS.md` (executable, eval-gated backlog).*
