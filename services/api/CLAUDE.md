# services/api — backend context

FastAPI modular monolith. **The append-only event log is the single source of truth**;
everything else is a projection (`graph.py` folds events → `GraphState`). Writes go through
`events.append_event`; nothing mutates/deletes an event.

## Layout
- `throughline_api/db.py` — SQLAlchemy `Event` model + engine helpers (Postgres in prod,
  SQLite for tests).
- `throughline_api/events.py` — event kinds + append/list helpers.
- `throughline_api/graph.py` — projection fold + `reconstruct(...at=eventId)` (Time Machine).
- `throughline_api/propagation.py` — change → **proposed diff** → confirm/reject (reuses
  the ML scheduler's DOOD math for ripple deltas).
- `throughline_api/rules/` — table-driven, effective-dated union rules engine (task 5.1).
- `throughline_api/app.py` — the `/v1` API + dev auth (X-User-Id / X-Org-Id / X-Role).

## Rules — YOU MUST
- **Human confirms structurally:** a draft's `status` is a pure function of events; only an
  `element.confirmed` / `change.confirmed` event (accepted solely from a human actor)
  flips it. No projector or AI path may emit those. Never auto-mark final.
- **Never a silent write:** downstream effects are always a `change.proposed` diff a human
  accepts; propagation must not mutate state directly.
- **No hard-coded rates:** all union rates/thresholds live in `rules/tables/*.yaml`
  (effective-dated). `make check-rates` fails the build otherwise.
- Don't hand-write `migrations/` (guardrail) — dev/test tables come from
  `db.init_db` (SQLAlchemy metadata); real migrations are a separate, human-reviewed step.

## Test
`pytest services/api` — SQLite in-memory per test (see `tests/conftest.py`); no network.
