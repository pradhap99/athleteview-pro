"""Final Draft ``.fdx`` parser + exporter → ParsedScript, with lossless round-trip.

FDX is XML: ``<FinalDraft><Content><Paragraph Type="Scene Heading" Number="1">
<Text>INT. KITCHEN - DAY</Text></Paragraph>...``. We parse with the stdlib and export
the same shape so core fields (scene number, int/ext, location, time-of-day, characters)
survive a parse → export → parse cycle unchanged.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from xml.dom import minidom

from .pageeighths import estimate_page_eighths
from .slugline import parse_slugline
from .types import IntExt, ParsedElement, ParsedScene, ParsedScript

_CHAR_EXTENSION = re.compile(r"\s*\(.*?\)\s*$")


def _para_text(paragraph: ET.Element) -> str:
    return "".join(t.text or "" for t in paragraph.findall("Text")).strip()


def parse_fdx(xml_text: str) -> ParsedScript:
    root = ET.fromstring(xml_text)
    content = root.find("Content")
    script = ParsedScript(source_format="fdx")
    if content is None:
        return script

    current: ParsedScene | None = None
    body: list[str] = []
    auto_number = 0

    def flush() -> None:
        if current is not None:
            current.body = "\n".join(body).strip()
            current.page_eighths = estimate_page_eighths(body)

    for para in content.findall("Paragraph"):
        ptype = para.get("Type", "")
        text = _para_text(para)
        if ptype == "Scene Heading":
            flush()
            body = []
            number, int_ext, location, tod = parse_slugline(text)
            explicit = para.get("Number") or number
            auto_number += 1
            current = ParsedScene(
                number=explicit or str(auto_number),
                int_ext=int_ext if isinstance(int_ext, IntExt) else IntExt.INT,
                location=location,
                time_of_day=tod,
                heading=text,
            )
            script.scenes.append(current)
        elif current is not None:
            if ptype == "Character" and text:
                name = _CHAR_EXTENSION.sub("", text).strip().rstrip(":").strip()
                if name and name not in current.characters:
                    current.characters.append(name)
                    current.elements.append(ParsedElement("cast", name, 1.0, "rule"))
            if text:
                body.append(text)

    flush()
    return script


def _para(parent: ET.Element, ptype: str, text: str, **attrs: str) -> ET.Element:
    p = ET.SubElement(parent, "Paragraph", {"Type": ptype, **attrs})
    t = ET.SubElement(p, "Text")
    t.text = text
    return p


def to_fdx(script: ParsedScript) -> str:
    """Serialize a ParsedScript back to Final Draft XML (core fields preserved)."""
    root = ET.Element(
        "FinalDraft",
        {"DocumentType": "Script", "Template": "No", "Version": "5"},
    )
    content = ET.SubElement(root, "Content")
    for scene in script.scenes:
        heading = scene.heading or _compose_heading(scene)
        _para(content, "Scene Heading", heading, Number=scene.number)
        for name in scene.characters:
            _para(content, "Character", name)
        if scene.body:
            for line in scene.body.split("\n"):
                if line.strip():
                    _para(content, "Action", line.strip())
    rough = ET.tostring(root, encoding="unicode")
    pretty = minidom.parseString(rough).toprettyxml(indent="  ")
    return pretty


def _compose_heading(scene: ParsedScene) -> str:
    prefix = {IntExt.INT: "INT.", IntExt.EXT: "EXT.", IntExt.INT_EXT: "INT./EXT."}[scene.int_ext]
    parts = [prefix, scene.location]
    heading = " ".join(p for p in parts if p)
    if scene.time_of_day:
        heading = f"{heading} - {scene.time_of_day}"
    return heading
