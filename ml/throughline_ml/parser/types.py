"""Types produced by the deterministic script parser.

These are self-contained (no dependency on the API package) so the parser can run
standalone in ``ml`` and in evals. The API layer maps a ``ParsedScript`` into graph
events (scenes + candidate elements) at ingest time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class IntExt(str, Enum):
    INT = "INT"
    EXT = "EXT"
    INT_EXT = "INT/EXT"


# Element categories that live on the graph (PRODUCT_SPEC §7.1 / §9).
ELEMENT_TYPES = (
    "cast",
    "prop",
    "wardrobe",
    "location",
    "vehicle",
    "sfx",
    "vfx",
    "stunt",
    "animal",
    "sound",
    "set_dressing",
)

# Safety-critical types get tuned for recall (guardrail; eval gate ≥0.95).
SAFETY_CRITICAL = frozenset({"stunt", "sfx", "animal", "vehicle"})


@dataclass(frozen=True)
class ParsedElement:
    """A candidate breakdown element found deterministically (e.g. a speaking character).

    ``confidence`` and ``source`` mirror the graph's element provenance. The deterministic
    parser only emits high-confidence structural elements (cast from dialogue cues); the
    AI Breakdown Agent (task 1.2) adds props/wardrobe/etc. as *drafts*.
    """

    etype: str
    name: str
    confidence: float = 1.0
    source: str = "rule"  # rule | ner | llm | human

    def __post_init__(self) -> None:
        if self.etype not in ELEMENT_TYPES:
            raise ValueError(f"unknown element type {self.etype!r}")


@dataclass
class ParsedScene:
    number: str
    int_ext: IntExt
    location: str
    time_of_day: str
    heading: str
    body: str = ""
    characters: list[str] = field(default_factory=list)
    page_eighths: int = 1
    elements: list[ParsedElement] = field(default_factory=list)

    def core_key(self) -> tuple:
        """The 'core fields' that interop round-trips must preserve losslessly."""
        return (
            self.number,
            self.int_ext.value,
            self.location.upper(),
            self.time_of_day.upper(),
            tuple(sorted(self.characters)),
        )


@dataclass
class ParsedScript:
    title: str = ""
    scenes: list[ParsedScene] = field(default_factory=list)
    source_format: str = ""

    @property
    def total_page_eighths(self) -> int:
        return sum(s.page_eighths for s in self.scenes)

    def characters(self) -> list[str]:
        seen: dict[str, None] = {}
        for scene in self.scenes:
            for c in scene.characters:
                seen.setdefault(c, None)
        return list(seen)
