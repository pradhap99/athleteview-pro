"""Throughline API — FastAPI backend, event log, projections, propagation, rules engine.

The production graph is the product. Writes append events (append-only log); async
projections materialize read views; propagation computes downstream diffs for human
confirmation. See ``@docs/PRODUCT_SPEC.md`` §8–§11.
"""

__version__ = "0.1.0"
