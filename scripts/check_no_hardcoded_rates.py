#!/usr/bin/env python3
"""CI guard: fail if a rate/multiplier/hour-threshold literal is hard-coded.

Union rates and hour thresholds MUST live in effective-dated [RATE CARD] tables
(``services/api/throughline_api/rules/tables/*.yaml``), never in code — the 2024 MOAs
changed thresholds and they phase in by shoot-start date, so a literal in code is a latent
compliance bug. This scans the rules/ (and future budget/) Python modules and rejects any
numeric literal that isn't a structural/unit constant.

Run via ``make check-rates``. See CLAUDE.md → "Domain rules" and PRODUCT_SPEC §7A.1.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCAN_DIRS = [
    ROOT / "services/api/throughline_api/rules",
    ROOT / "services/api/throughline_api/budget",  # created by task 5.3
]

# Structural / unit constants that are NOT rates: indices, calendar positions (days 0-7,
# 24h), minutes-per-hour, rounding precision, common scale factors.
ALLOWED_INTS = {0, 1, 2, 3, 4, 5, 6, 7, 24, 60, 100, 1000}
ALLOWED_FLOATS = {0.0, 1.0}


def _is_test_path(path: Path) -> bool:
    return path.name.startswith("test_") or path.name.endswith("_test.py") or "tests" in path.parts


def scan_file(path: Path) -> list[tuple[int, object]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    bad: list[tuple[int, object]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant):
            continue
        value = node.value
        if isinstance(value, bool):  # bool is an int subclass — never a rate
            continue
        if isinstance(value, int) and value not in ALLOWED_INTS:
            bad.append((node.lineno, value))
        elif isinstance(value, float) and value not in ALLOWED_FLOATS:
            bad.append((node.lineno, value))
    return bad


def main() -> int:
    violations: list[tuple[Path, int, object]] = []
    scanned = 0
    for base in SCAN_DIRS:
        if not base.exists():
            continue
        for py in sorted(base.rglob("*.py")):
            if _is_test_path(py):
                continue
            scanned += 1
            for lineno, value in scan_file(py):
                violations.append((py, lineno, value))

    if violations:
        print("✗ Hard-coded rate/threshold literals found in rules/budget code:\n")
        for path, lineno, value in violations:
            print(f"  {path.relative_to(ROOT)}:{lineno}: {value!r}")
        print(
            "\nAll rates/multipliers/hour-thresholds must live in effective-dated "
            "[RATE CARD] tables (rules/tables/*.yaml). See CLAUDE.md → Domain rules."
        )
        return 1

    print(f"✓ No hard-coded rates/thresholds in rules/budget code ({scanned} file(s) scanned).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
