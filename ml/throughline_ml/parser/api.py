"""Format-dispatching entry point for the deterministic parser."""

from __future__ import annotations

import os

from .fdx import parse_fdx
from .fountain import parse_fountain
from .types import ParsedScript


def _looks_like_fdx(text: str) -> bool:
    head = text.lstrip()[:200].lower()
    return "<finaldraft" in head or (
        head.startswith("<?xml") and "finaldraft" in text[:500].lower()
    )


def parse_script(source: str, fmt: str | None = None) -> ParsedScript:
    """Parse a screenplay from a path or raw text.

    ``fmt`` is one of ``fdx`` | ``fountain`` | ``pdf``; if omitted it is inferred from a
    file extension or the content. PDF parsing (``pdfplumber``, optional dep) is a seam.
    """
    text = source
    if os.path.sep in source or source.lower().endswith((".fdx", ".fountain", ".txt", ".pdf")):
        if os.path.exists(source):
            if fmt is None and source.lower().endswith(".pdf"):
                fmt = "pdf"
            if fmt == "pdf" or source.lower().endswith(".pdf"):
                text = _read_pdf(source)
                fmt = fmt or "fountain"
            else:
                with open(source, encoding="utf-8") as fh:
                    text = fh.read()
                if fmt is None:
                    fmt = "fdx" if source.lower().endswith(".fdx") else "fountain"

    if fmt is None:
        fmt = "fdx" if _looks_like_fdx(text) else "fountain"

    if fmt == "fdx":
        return parse_fdx(text)
    return parse_fountain(text)


def _read_pdf(path: str) -> str:
    """Extract text from a PDF via pdfplumber (MIT; optional ``[ai]`` dep).

    Deterministic parser owns format fidelity — no AI. pdfplumber is chosen over PyMuPDF
    which is AGPL (guardrail). Requires ``pip install -e '.[ai]'``.
    """
    try:
        import pdfplumber  # type: ignore
    except ImportError as exc:  # pragma: no cover - optional dep
        raise RuntimeError(
            "PDF parsing requires the optional 'ai' extra: pip install -e '.[ai]'"
        ) from exc
    with pdfplumber.open(path) as pdf:  # pragma: no cover - needs a real PDF
        return "\n".join(page.extract_text() or "" for page in pdf.pages)
