# ml — models, parsers, solver context

Doctrine (PRODUCT_SPEC §12): right tool per task — **deterministic solvers for math, open
LLMs for language, deterministic parsers for file-format fidelity**. Prefer self-hostable,
permissively-licensed (Apache/MIT/BSD) weights. Small-model-first; escalate only when an
eval proves a gap.

## Layout
- `throughline_ml/parser/` — deterministic Fountain + FDX → scenes; lossless FDX
  round-trip; PDF seam (pdfplumber, MIT — never PyMuPDF/AGPL). **No AI here.**
- `throughline_ml/scheduler/` — OR-Tools CP-SAT stripboard + DOOD derivation. The solver
  *proposes*; humans confirm. Hard constraints are never violated (eval gate: 0 violations).
- `throughline_ml/breakdown/` — Breakdown Agent seam: NER (GLiNER) → LLM reconcile (Qwen3,
  constrained JSON) → **draft** elements with confidence + source span. Concrete adapters
  need a model endpoint + the `[ai]` extra.
- `throughline_ml/rag/` — hybrid search + grounded Q&A seam; abstains below the
  faithfulness gate (≥0.90).
- `../ml/prompts/` — **versioned** prompt files. Never inline long prompts in code.

## Rules — YOU MUST
- AI output is a DRAFT with confidence + provenance; safety-critical types
  (stunt/sfx/animal/vehicle) are recall-first and always `needs_review`.
- Deterministic parsers own AICP/MM/FDX fidelity — never AI.
- AI-feature changes must pass their eval gates (`make evals`) before merge.

## Test
`pytest ml` — pure, no network; the scheduler runs OR-Tools on CPU.
