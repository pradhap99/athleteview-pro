# evals — the quality firewall

Method (PRODUCT_SPEC §15): task → trials → **code-based graders** (LLM-judge only where
needed; human to calibrate) → outcomes not paths → suites → CI. Capability evals start low;
**regression evals sit near 100% and block releases on any drop**; solved capability tasks
graduate into regression; every production failure becomes a golden case.

## Layout
- `datasets/<feature>/` — version-controlled golden data (breakdown, scheduler; rag next).
- `graders/` — deterministic graders + gate checks (`breakdown_f1`, `scheduler_metrics`).
- `suites/` — `pytest` gate tests, marked `@pytest.mark.eval`; run via `make evals`.

## Gates (block merge)
- **Breakdown:** characters/locations F1 ≥0.90; props/wardrobe/vehicles ≥0.80;
  safety-critical recall ≥0.95; net time saved >0 (timed QA study).
- **Scheduler:** hard-constraint violations ==0; mean optimality gap ≤10%; solve within
  budget (PAR-2).
- **RAG:** faithfulness ≥0.90 (else abstain); context recall ≥0.85; answer relevancy
  ≥0.80; every claim cited.

## Rules — YOU MUST
- Read transcripts before trusting scores. Balance positive + negative cases.
- A firewall that never fails is useless — suites prove graders REJECT bad output
  (e.g. a dropped safety-critical element must fail the gate).
- Live model gates skip without a model endpoint (`THROUGHLINE_LLM_ENDPOINT`); grader
  correctness is always exercised.
