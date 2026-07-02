"""Deterministic screenplay parsers (task 1.1).

Deterministic parsers own file-format fidelity — AI never touches it (guardrail).
Supported: Fountain (plain text), Final Draft ``.fdx`` (XML, lossless round-trip on
core fields), and a PDF seam (``pdfplumber``, optional dep).

Public API:
    parse_script(text_or_path, fmt=None) -> ParsedScript
    to_fdx(script) -> str
"""

from .api import parse_script
from .fdx import parse_fdx, to_fdx
from .fountain import parse_fountain
from .types import ParsedElement, ParsedScene, ParsedScript

__all__ = [
    "parse_script",
    "parse_fdx",
    "to_fdx",
    "parse_fountain",
    "ParsedScene",
    "ParsedScript",
    "ParsedElement",
]
