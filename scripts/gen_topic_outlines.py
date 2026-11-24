# -*- coding: utf-8 -*-
"""Generate frontend/src/data/topicOutlines.js from step card sources."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / "backend/app/services/step_cards.py",
    ROOT / "backend/app/services/step_cards_fine.py",
    ROOT / "backend/app/services/step_cards_extra.py",
]
OUT = ROOT / "frontend/src/data/topicOutlines.js"


def main() -> None:
    src = "\n".join(p.read_text(encoding="utf-8") for p in FILES)
    out: dict[str, dict] = {}
    ids = list(re.finditer(r'"method_id"\s*:\s*"([^"]+)"', src))
    for i, m in enumerate(ids):
        mid = m.group(1)
        end = ids[i + 1].start() if i + 1 < len(ids) else len(src)
        block = src[m.start() : end]

        bullets: list[str] = []
        sd = re.search(r'"step_details"\s*:\s*\[(.*?)]\s*,\s*"speak_intro"', block, re.S)
        if sd:
            bullets = re.findall(r'"title"\s*:\s*"([^"]+)"', sd.group(1))
        if not bullets:
            steps = re.search(r'"steps"\s*:\s*\[(.*?)]', block, re.S)
            if steps:
                bullets = re.findall(r'"([^"]+)"', steps.group(1))[:4]

        blurb = ""
        intro = re.search(r'"intro_story"\s*:\s*\[(.*?)]', block, re.S)
        if intro:
            first = re.search(r'"([^"]+)"', intro.group(1))
            if first:
                blurb = first.group(1)

        out[mid] = {"blurb": blurb, "bullets": bullets[:6]}

    lines = [
        "/** 首页思维导图：知识点细分要点（来自步骤卡 step_details / steps） */",
        "export const topicOutlines = {",
    ]
    for k in sorted(out):
        v = out[k]
        bullets = json.dumps(v["bullets"], ensure_ascii=False)
        blurb = json.dumps(v["blurb"], ensure_ascii=False)
        lines.append(f"  {k}: {{ blurb: {blurb}, bullets: {bullets} }},")
    lines.extend(
        [
            "};",
            "",
            "export function outlineFor(topicId) {",
            '  return topicOutlines[topicId] || { blurb: "", bullets: [] };',
            "}",
            "",
        ]
    )
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {len(out)} outlines -> {OUT}")


if __name__ == "__main__":
    main()
