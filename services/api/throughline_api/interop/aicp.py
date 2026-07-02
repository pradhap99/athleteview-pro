"""AICP bid-form export/import — lossless round-trip on core fields.

The AICP firm-bid form organizes costs into lettered sections (A–W in the modern long
form). ``SECTION_TITLES`` is *structural* metadata (the section layout, not rates) and is
configurable per org — titles below follow common usage of the standard form. A budget
line maps to a section via its ``aicp_section`` letter; unmapped lines land in a
``_UNSECTIONED`` bucket so the round-trip NEVER drops a line.

Round-trip contract (tested): ``from_aicp(to_aicp(lines))`` preserves the core fields —
id, account code, description, qty, unit, rate, fringes, category, section.
"""

from __future__ import annotations

import csv
import io
from typing import Any

from ..budget.model import BudgetLine, line_from_payload

AICP_FORMAT = "aicp-bid"
AICP_VERSION = "1.0"
UNSECTIONED = "_UNSECTIONED"

# Structural section map for the standard AICP bid form (configurable; not rates).
SECTION_TITLES: dict[str, str] = {
    "A": "Pre-production & wrap crew labor",
    "B": "Shooting crew labor",
    "C": "Location & travel expenses",
    "D": "Props, wardrobe & animals",
    "E": "Studio & set construction costs",
    "F": "Set operation expenses",
    "G": "Equipment costs",
    "H": "Film stock / media & processing",
    "I": "Talent labor",
    "J": "Talent expenses",
    "K": "Post-production labor",
    "L": "Post-production expenses",
    "M": "Editorial",
    "N": "Music",
    "O": "Sound & mix",
    "P": "Graphics & VFX",
    "Q": "Color & finishing",
    "R": "Insurance",
    "S": "Director / creative fees",
    "T": "Production fee / markup",
    "U": "Contingency / weather day",
    "V": "Miscellaneous",
    "W": "Other / client-specified",
}


def to_aicp(lines: list[BudgetLine], *, title: str = "") -> dict[str, Any]:
    """Serialize budget lines into the AICP bid-form structure (JSON-shaped)."""
    sections: dict[str, dict[str, Any]] = {}
    for line in lines:
        letter = line.aicp_section if line.aicp_section in SECTION_TITLES else UNSECTIONED
        section = sections.setdefault(
            letter,
            {
                "section": letter,
                "title": SECTION_TITLES.get(letter, "Unsectioned"),
                "lines": [],
                "subtotal": 0.0,
            },
        )
        section["lines"].append(line.to_payload())
        section["subtotal"] = round(section["subtotal"] + line.total, 2)

    ordered = [sections[k] for k in sorted(sections, key=lambda s: (s == UNSECTIONED, s))]
    return {
        "format": AICP_FORMAT,
        "version": AICP_VERSION,
        "title": title,
        "sections": ordered,
        "grandTotal": round(sum(s["subtotal"] for s in ordered), 2),
    }


def from_aicp(doc: dict[str, Any]) -> list[BudgetLine]:
    """Parse an AICP bid document back into budget lines (inverse of ``to_aicp``)."""
    if doc.get("format") != AICP_FORMAT:
        raise ValueError(f"not an AICP bid document (format={doc.get('format')!r})")
    lines: list[BudgetLine] = []
    for section in doc.get("sections", []):
        letter = section.get("section")
        for payload in section.get("lines", []):
            line = line_from_payload(payload)
            if line.aicp_section is None and letter != UNSECTIONED:
                line.aicp_section = letter
            lines.append(line)
    return lines


def to_aicp_csv(lines: list[BudgetLine]) -> str:
    """Flat CSV of the bid (section, code, description, qty, unit, rate, total)."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["section", "code", "description", "qty", "unit", "rate", "fringes", "total"])
    doc = to_aicp(lines)
    for section in doc["sections"]:
        for p in section["lines"]:
            fringe_text = "; ".join(
                f"{f['name']} {f['ratePct']}%" + (f" cap {f['cap']}" if f.get("cap") else "")
                for f in p.get("fringes", [])
            )
            writer.writerow(
                [
                    section["section"],
                    p["code"],
                    p["description"],
                    p["qty"],
                    p["unit"],
                    p["rate"],
                    fringe_text,
                    p["total"],
                ]
            )
        writer.writerow(
            [
                section["section"],
                "",
                f"SUBTOTAL {section['title']}",
                "",
                "",
                "",
                "",
                section["subtotal"],
            ]
        )
    writer.writerow(["", "", "GRAND TOTAL", "", "", "", "", doc["grandTotal"]])
    return buf.getvalue()
